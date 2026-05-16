"""PKGBUILD 文件编辑器模块"""

import re
from pathlib import Path

from constants.constants import HashAlgorithmEnum
from utils.hash import calculate_file_hash, verify_file_hash


class PKGBUILDEditor:
    """PKGBUILD 文件编辑器"""

    def __init__(self, pkgbuild_path: Path) -> None:
        self.pkgbuild_path = pkgbuild_path
        self.content = ""
        self._load_content()

    def _load_content(self) -> None:
        """加载 PKGBUILD 文件内容"""
        with open(self.pkgbuild_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def _save_content(self) -> None:
        """保存 PKGBUILD 文件内容"""
        with open(self.pkgbuild_path, "w", encoding="utf-8") as f:
            f.write(self.content)

    def update_pkgver(self, new_version: str) -> None:
        """更新 pkgver 字段"""
        pattern = r"^pkgver=.*$"
        replacement = f"pkgver={new_version}"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_pkgrel(self, new_pkgrel: int = 1) -> None:
        """更新 pkgrel 字段"""
        pattern = r"^pkgrel=.*$"
        replacement = f"pkgrel={new_pkgrel}"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_epoch(self, new_epoch: int | None = None) -> None:
        """更新或添加 epoch 字段"""
        if new_epoch is None:
            return

        if re.search(r"^epoch=.*$", self.content, flags=re.MULTILINE):
            pattern = r"^epoch=.*$"
            replacement = f"epoch={new_epoch}"
            self.content = re.sub(
                pattern, replacement, self.content, flags=re.MULTILINE
            )
        else:
            pattern = r"^(pkgver=.*)$"
            replacement = f"epoch={new_epoch}\n\1"
            self.content = re.sub(
                pattern, replacement, self.content, flags=re.MULTILINE
            )

    def update_sha512sums(self, new_checksum: str) -> None:
        """更新通用 sha512sums 字段"""
        pattern = r"^sha512sums=\(.*\)$"
        replacement = f"sha512sums=('{new_checksum}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_arch_checksum(
        self,
        arch: str,
        new_checksum: str,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """更新特定架构的校验和字段"""
        pattern = f"^{hash_algorithm}sums_{arch}=\\(.*\\)$"
        replacement = f"{hash_algorithm}sums_{arch}=('{new_checksum}')"
        self.content = re.sub(pattern, replacement, self.content, flags=re.MULTILINE)

    def update_source_url(self, arch: str, new_url: str) -> None:
        """更新特定架构的 source URL"""
        pattern = f"^source_{arch}=\\((?:'([^']*)::[^']*'|.*)\\)$"
        match = re.search(pattern, self.content, flags=re.MULTILINE)
        if match and match.group(1):
            replacement = f"source_{arch}=('{match.group(1)}::{new_url}')"
        else:
            replacement = f"source_{arch}=('{new_url}')"
        self.content = re.sub(
            f"^source_{arch}=\\(.*\\)$",
            replacement,
            self.content,
            flags=re.MULTILINE,
        )

    def get_pkgver(self) -> str:
        """获取当前 pkgver 值"""
        match = re.search(r"^pkgver=(.*)$", self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def get_pkgrel(self) -> int:
        """获取当前 pkgrel 值"""
        match = re.search(r"^pkgrel=(.*)$", self.content, flags=re.MULTILINE)
        return int(match.group(1)) if match else 1

    def get_epoch(self) -> int | None:
        """获取当前 epoch 值"""
        match = re.search(r"^epoch=(.*)$", self.content, flags=re.MULTILINE)
        return int(match.group(1)) if match else None

    def get_checksum(self, arch: str | None = None) -> str:
        """获取当前校验和值"""
        if arch:
            pattern = f"^sha512sums_{arch}=\\((?:'([^']*)'.*)?\\)$"
        else:
            pattern = r"^sha512sums=\((?:'([^']*)'.*)?\)$"

        match = re.search(pattern, self.content, flags=re.MULTILINE)
        return match.group(1) if match else ""

    def update_all(
        self,
        new_version: str,
        new_checksums: dict[str, str],
        new_urls: dict[str, str],
        new_pkgrel: int = 1,
        new_epoch: int | None = None,
        generic_checksum: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """一次性更新所有相关字段"""
        self.update_pkgver(new_version)
        self.update_pkgrel(new_pkgrel)

        if new_epoch is not None:
            self.update_epoch(new_epoch)

        if generic_checksum:
            if hash_algorithm == HashAlgorithmEnum.SHA512.value:
                self.update_sha512sums(generic_checksum)
            else:
                pattern = f"^{hash_algorithm}sums=\\(.*\\)$"
                replacement = f"{hash_algorithm}sums=('{generic_checksum}')"
                self.content = re.sub(
                    pattern, replacement, self.content, flags=re.MULTILINE
                )

        for arch, checksum in new_checksums.items():
            self.update_arch_checksum(arch, checksum, hash_algorithm)

        for arch, url in new_urls.items():
            self.update_source_url(arch, url)

    def save(self) -> None:
        """保存所有更改到文件"""
        self._save_content()

    def reload(self) -> None:
        """重新加载文件内容，放弃未保存的更改"""
        self._load_content()

    def calculate_and_update_checksum(
        self,
        file_path: str | Path,
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> None:
        """计算文件校验和并更新到 PKGBUILD"""
        checksum = calculate_file_hash(file_path, hash_algorithm)

        if arch:
            if hash_algorithm == HashAlgorithmEnum.SHA512.value:
                self.update_arch_checksum(arch, checksum)
            else:
                pattern = f"^{hash_algorithm}sums_{arch}=\\(.*\\)$"
                replacement = f"{hash_algorithm}sums_{arch}=('{checksum}')"
                self.content = re.sub(
                    pattern, replacement, self.content, flags=re.MULTILINE
                )
        else:
            if hash_algorithm == HashAlgorithmEnum.SHA512.value:
                self.update_sha512sums(checksum)
            else:
                pattern = f"^{hash_algorithm}sums=\\(.*\\)$"
                replacement = f"{hash_algorithm}sums=('{checksum}')"
                self.content = re.sub(
                    pattern, replacement, self.content, flags=re.MULTILINE
                )

    def verify_existing_checksum(
        self,
        file_path: str | Path,
        expected_hash: str,
        arch: str | None = None,
        hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
    ) -> bool:
        """验证文件哈希值是否匹配预期值"""
        return verify_file_hash(file_path, expected_hash, hash_algorithm)
