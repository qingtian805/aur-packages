"""
包更新器
整合fetch、parse和update三个流程

架构设计：
1. 串行下载所有维护的 AUR 包（一个包处理完后才处理下一个）
2. 并行下载单个包的所有架构（使用 Downloader 的并发功能）
"""

from pathlib import Path

from constants.constants import DOWNLOAD_DIR, ArchEnum, HashAlgorithmEnum, ParserEnum
from fetcher.fetcher import Fetcher
from loaders.config_loader import ConfigLoader, PackageConfig
from parsers.base_parser import BaseParser
from parsers.qq import QQParser
from parsers.navicat import NavicatPremiumCSParser
from updater.pkgbuild_editor import PKGBUILDEditor
from utils.downloader import Downloader
from utils.url_utils import generate_download_filename
from utils.version_utils import compare_versions


class PackageUpdater:
    """包更新器，整合fetch、parse和update流程"""

    def __init__(self) -> None:
        # 加载配置
        self.config = ConfigLoader.load_from_yaml()

        # 从配置中获取下载设置
        download_settings = self.config.settings.download

        # 初始化 Fetcher（使用配置的超时时间）
        self.fetcher = Fetcher(timeout=download_settings.timeout)

        # 注册解析器
        self.parsers: dict[str, BaseParser] = {
            ParserEnum.QQ.value: QQParser(),
            ParserEnum.NAVICAT_PREMIUM_CS.value: NavicatPremiumCSParser(),
        }

        # 初始化下载器（使用配置的下载设置）
        self.downloader = Downloader(
            max_retries=download_settings.max_retries,
            retry_wait=download_settings.retry_wait,
            timeout=download_settings.timeout,
            connections=download_settings.connections,
            show_progress=download_settings.show_progress,
        )

        # 获取项目根目录（这里的项目根目录指更新脚本的根目录）
        # 当前脚本位于 scripts/core/，所以需要向上两级到达项目根目录
        self.project_root = Path(__file__).parent.parent
        # PKGBUILD目录相对于项目根目录
        self.pkgbuild_root = self.project_root.parent

    async def close(self) -> None:
        """释放资源"""
        await self.fetcher.client.aclose()

    def _get_pkgbuild_path(self, pkgbuild_relative_path: str) -> Path:
        """
        获取PKGBUILD文件的完整路径

        注意：PKGBUILD目录需要从项目根目录的上级目录开始

        Args:
            pkgbuild_relative_path: PKGBUILD的相对路径

        Returns:
            PKGBUILD的完整路径
        """
        # 如果路径已经是绝对路径，直接返回
        pkgbuild_path = Path(pkgbuild_relative_path)
        if pkgbuild_path.is_absolute():
            return pkgbuild_path

        # 否则，将其与pkgbuild_root结合
        full_path = self.pkgbuild_root / pkgbuild_relative_path
        return full_path

    def _check_pkgbuild_exists(self, package_name: str, package_config: PackageConfig) -> bool:
        """
        检查 PKGBUILD 文件是否存在

        Args:
            package_name: 包名
            package_config: 包配置

        Returns:
            True 如果文件存在，False 否则
        """
        pkgbuild_path = self._get_pkgbuild_path(package_config.pkgbuild)
        if not pkgbuild_path.exists():
            print(f"  跳过: PKGBUILD 文件不存在: {pkgbuild_path}")
            return False
        return True

    async def _fetch_arch_urls(
        self, parser: BaseParser, supported_archs: list[ArchEnum], response_data: str
    ) -> dict[str, str]:
        """获取所有架构的下载 URL"""
        arch_urls = {}
        for arch in supported_archs:
            url = parser.parse_url(arch, response_data)
            if url:
                arch_urls[arch.value] = url
            else:
                print(f"  警告: 无法获取 {arch.value} 架构的下载URL")
        return arch_urls

    async def _download_and_verify(
        self,
        package_name: str,
        new_version: str,
        arch_urls: dict[str, str],
        verify_only: bool = False,
    ) -> tuple[dict[str, str], bool]:
        """
        下载文件并计算校验和

        使用 Downloader 的并发下载功能，并行下载单个包的所有架构
        """
        download_dir = Path(DOWNLOAD_DIR)
        download_dir.mkdir(exist_ok=True)

        downloads = {
            arch: (
                url,
                download_dir
                / generate_download_filename(
                    package_name, new_version, arch, url, default_extension=".deb"
                ),
            )
            for arch, url in arch_urls.items()
        }

        # 使用 Downloader 并行下载所有架构
        download_results = await self.downloader.download_all(
            downloads, package_name=package_name
        )

        checksums = {}
        failed_archs = []

        for arch, result in download_results.items():
            if not result.success:
                if not verify_only:
                    print(f"  错误: {arch} 架构下载失败: {result.error}")
                    failed_archs.append(arch)
                else:
                    print(f"  警告: {arch} 架构下载失败: {result.error}")
                continue

            if result.file_path is None:
                if not verify_only:
                    print(f"  错误: {arch} 架构文件路径为空")
                    failed_archs.append(arch)
                continue

            checksum = await self._calculate_checksum(result.file_path)
            checksums[arch] = checksum
            print(f"  {arch} 架构哈希验证通过: {checksum}")

        if not verify_only and (failed_archs or not checksums):
            if failed_archs:
                print(f"  错误: {len(failed_archs)} 个架构下载失败: {failed_archs}")
            if not checksums:
                print("  错误: 没有成功下载任何架构的文件")
            return {}, False

        return checksums, True

    async def update_package(
        self, package_name: str, package_config: PackageConfig
    ) -> bool:
        """更新单个包"""
        print(f"开始更新包: {package_name}")

        try:
            # 1. 获取最新版本信息
            print(f"  1. 从 {package_config.fetch_url} 获取版本信息...")
            response_data = await self.fetcher.fetch_text(package_config.fetch_url)
            if not response_data:
                print("  错误: 无法获取版本信息")
                return False

            # 2. 解析版本号和下载 URL
            print("  2. 解析版本信息...")
            parser = self.parsers.get(package_config.parser)
            if not parser:
                print(f"  错误: 找不到解析器 {package_config.parser}")
                return False

            new_version = parser.parse_version(response_data)
            if not new_version:
                print("  错误: 无法解析版本号")
                return False

            print(f"  最新版本: {new_version}")

            # 3. 检查当前版本
            pkgbuild_path = self._get_pkgbuild_path(package_config.pkgbuild)
            print(f"  PKGBUILD路径: {pkgbuild_path}")

            if not pkgbuild_path.exists():
                print(f"  错误: PKGBUILD文件不存在: {pkgbuild_path}")
                return False

            editor = PKGBUILDEditor(pkgbuild_path)
            current_version = editor.get_pkgver()
            print(f"  当前版本: {current_version}")

            # 获取包支持的架构
            supported_archs = package_config.get_supported_archs()

            # 版本比较
            version_comparison = compare_versions(new_version, current_version)

            if version_comparison <= 0:
                # 当前版本 >= 新版本，仅验证哈希
                return await self._handle_version_not_newer(
                    package_name,
                    new_version,
                    current_version,
                    parser,
                    supported_archs,
                    response_data,
                )

            # 版本更新流程
            return await self._handle_version_update(
                package_name,
                new_version,
                current_version,
                editor,
                parser,
                supported_archs,
                response_data,
                package_config,
            )

        except Exception as e:
            print(f"  错误: 更新包 {package_name} 时发生异常: {e}")
            return False

    async def _handle_version_not_newer(
        self,
        package_name: str,
        new_version: str,
        current_version: str,
        parser: BaseParser,
        supported_archs: list[ArchEnum],
        response_data: str,
    ) -> bool:
        """
        处理版本不更新的情况（当前版本 >= 新版本）

        两种场景：
        1. 当前版本 > 新版本：版本降级，仅验证哈希
        2. 当前版本 = 新版本：版本相同，检查哈希变化并更新 pkgrel
        """
        version_comparison = compare_versions(new_version, current_version)

        if version_comparison < 0:
            # 当前版本 > 新版本：版本降级
            print(f"  跳过更新: 新版本 {new_version} 低于当前版本 {current_version}")
            print("  说明: 当前包版本较新，无需降级")
            print("  注意: 仍将下载并验证哈希数据...")

            arch_urls = await self._fetch_arch_urls(
                parser, supported_archs, response_data
            )
            if not arch_urls:
                print("  错误: 无法获取任何架构的下载URL")
                return False

            checksums, _ = await self._download_and_verify(
                package_name, new_version, arch_urls, verify_only=True
            )

            print(f"  包 {package_name} 验证完成（未更新 PKGBUILD）")
            return True

        # 当前版本 = 新版本：检查哈希变化
        print("  版本未变化，检查文件哈希是否变化...")

        # 获取当前 PKGBUILD 中的哈希值
        pkgbuild_path = self._get_pkgbuild_path(
            self.config.packages[package_name].pkgbuild
        )
        editor = PKGBUILDEditor(pkgbuild_path)

        current_checksums = {}
        for arch in supported_archs:
            current_checksum = editor.get_checksum(arch.value)
            if current_checksum:
                current_checksums[arch.value] = current_checksum
            else:
                print(f"  警告: 无法获取 {arch.value} 架构的当前哈希值")

        # 下载并计算新哈希值
        arch_urls = await self._fetch_arch_urls(parser, supported_archs, response_data)
        if not arch_urls:
            print("  错误: 无法获取任何架构的下载URL")
            return False

        new_checksums, success = await self._download_and_verify(
            package_name, new_version, arch_urls
        )
        if not success:
            return False

        # 比较哈希值
        hash_changed = False
        for arch, new_checksum in new_checksums.items():
            if arch in current_checksums:
                if current_checksums[arch] != new_checksum:
                    print(f"  检测到 {arch} 架构的文件哈希已变化")
                    hash_changed = True
                else:
                    print(f"  {arch} 架构的文件哈希未变化")

        if not hash_changed:
            print("  所有架构的文件哈希均未变化，无需更新")
            return True

        # 哈希已变化，自增 pkgrel
        print("  文件哈希已变化，更新 pkgrel 和校验和...")
        current_pkgrel = editor.get_pkgrel()
        new_pkgrel = current_pkgrel + 1
        print(f"  pkgrel: {current_pkgrel} → {new_pkgrel}")

        editor.update_pkgrel(new_pkgrel)

        # 更新校验和（不更新 source URL，因为版本未变）
        for arch, checksum in new_checksums.items():
            editor.update_arch_checksum(arch, checksum)

        editor.save()
        print(f"  包 {package_name} 的 pkgrel 已更新（版本未变但哈希已变）")
        return True

    async def _handle_version_update(
        self,
        package_name: str,
        new_version: str,
        current_version: str,
        editor: PKGBUILDEditor,
        parser: BaseParser,
        supported_archs: list[ArchEnum],
        response_data: str,
        package_config: PackageConfig,
    ) -> bool:
        """处理版本更新流程"""
        print("  3. 下载文件并计算校验和...")
        print(f"  支持的架构: {[arch.value for arch in supported_archs]}")

        arch_urls = await self._fetch_arch_urls(parser, supported_archs, response_data)
        if not arch_urls:
            print("  错误: 无法获取任何架构的下载URL")
            return False

        checksums, success = await self._download_and_verify(
            package_name, new_version, arch_urls
        )
        if not success:
            return False

        # 更新 PKGBUILD
        print("  4. 更新 PKGBUILD 版本和校验和...")
        editor.update_pkgver(new_version)
        editor.update_pkgrel(1)  # 重置 pkgrel 为 1

        # 更新各架构的 source 和校验和
        for arch, url in arch_urls.items():
            if package_config.update_source_url:
                editor.update_source_url(arch, url)
            editor.update_arch_checksum(arch, checksums[arch])

        editor.save()
        print("  5. PKGBUILD 已更新")

        print(f"包 {package_name} 更新完成!")
        return True

    async def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件的 SHA512 校验和"""
        import asyncio
        from functools import partial

        from utils.hash import calculate_file_hash

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(calculate_file_hash, file_path, HashAlgorithmEnum.SHA512.value)
        )

    async def update_all_packages(self) -> tuple[int, int]:
        """
        更新所有配置的包

        串行处理所有包（一个包处理完后才处理下一个）
        每个包的多个架构并行下载（通过 Downloader 实现）

        Returns:
            (成功数量, 总数量)
        """
        # 过滤出启用的包
        enabled_packages = {
            name: config
            for name, config in self.config.packages.items()
            if config.enable
        }
        disabled_packages = [
            name
            for name, config in self.config.packages.items()
            if not config.enable
        ]

        print(f"开始更新所有包（共 {len(enabled_packages)} 个启用，{len(disabled_packages)} 个禁用）...")

        if disabled_packages:
            print(f"  已跳过禁用的包: {', '.join(disabled_packages)}")

        # 预检查 PKGBUILD 文件是否存在
        valid_packages = {}
        missing_pkgbuild_packages = []

        for package_name, package_config in enabled_packages.items():
            if not self._check_pkgbuild_exists(package_name, package_config):
                missing_pkgbuild_packages.append(package_name)
            else:
                valid_packages[package_name] = package_config

        if missing_pkgbuild_packages:
            print(f"  已跳过 PKGBUILD 文件不存在的包: {', '.join(missing_pkgbuild_packages)}")

        if not valid_packages:
            print("\n没有可更新的包")
            return 0, 0

        success_count = 0
        total_count = len(valid_packages)

        for package_name, package_config in valid_packages.items():
            print()
            success = await self.update_package(package_name, package_config)
            if success:
                success_count += 1

        print()
        print(f"更新完成: {success_count}/{total_count} 个包更新成功")
        return success_count, total_count

    def _is_package_updatable(
        self, package_name: str, package_config: PackageConfig
    ) -> tuple[bool, str | None]:
        """
        检查包是否可更新

        Args:
            package_name: 包名
            package_config: 包配置

        Returns:
            (是否可更新, 跳过原因)
        """
        if not package_config.enable:
            return False, f"包 '{package_name}' 已禁用"

        if not self._check_pkgbuild_exists(package_name, package_config):
            return False, f"包 '{package_name}' PKGBUILD 文件不存在"

        return True, None

    async def update_single_package(self, package_name: str) -> bool:
        """更新单个指定的包"""
        success_count, total_count = await self.update_packages([package_name])
        return success_count > 0 and total_count > 0

    async def update_packages(
        self, package_names: list[str]
    ) -> tuple[int, int]:
        """
        更新指定的包列表

        Args:
            package_names: 包名列表

        Returns:
            (成功数量, 总数量)
        """
        if not package_names:
            return 0, 0

        # 验证和过滤包
        valid_packages: dict[str, PackageConfig] = {}
        invalid_packages: list[str] = []
        skip_reasons: list[str] = []

        for package_name in package_names:
            if package_name not in self.config.packages:
                invalid_packages.append(package_name)
                continue

            package_config = self.config.packages[package_name]
            is_updatable, skip_reason = self._is_package_updatable(package_name, package_config)

            if is_updatable:
                valid_packages[package_name] = package_config
            elif skip_reason:
                skip_reasons.append(skip_reason)

        # 输出跳过的包
        if invalid_packages:
            print(f"错误: 以下包不在配置中: {', '.join(invalid_packages)}")

        for reason in skip_reasons:
            print(f"  跳过: {reason}")

        if not valid_packages:
            return 0, 0

        # 更新包
        print(f"开始更新 {len(valid_packages)} 个包...")

        success_count = 0
        total_count = len(valid_packages)

        for package_name, package_config in valid_packages.items():
            print()
            if await self.update_package(package_name, package_config):
                success_count += 1

        print()
        print(f"更新完成: {success_count}/{total_count} 个包更新成功")

        return success_count, total_count

    def list_available_packages(self) -> None:
        """列出所有可用的包"""
        print("可用的包:")
        for package_name, package_config in self.config.packages.items():
            status = "启用" if package_config.enable else "禁用"
            print(f"  - {package_name} [{status}]")
