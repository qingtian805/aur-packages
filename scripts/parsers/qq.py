"""QQ Linux 版本解析器"""

import json
import re
from typing import Any

from constants.constants import ArchEnum
from .base_parser import BaseParser


class QQParser(BaseParser):
    """QQ Linux 版本解析器"""

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 QQ 响应数据中提取版本号"""
        if not isinstance(response_data, str):
            return None
        url: str | None = self.parse_url(ArchEnum.X86_64, response_data)
        if not url:
            return None
        pattern: str = r"QQ_([\d._]+)_amd64"
        matched: re.Match[str] | None = re.search(pattern, url)
        return matched.group(1) if matched else None

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 QQ 响应数据中提取指定架构的下载 URL"""
        if not isinstance(response_data, str):
            return None
        arch_value: str = arch.value if isinstance(arch, ArchEnum) else arch

        pattern: str = r"var params\s*=\s*(\{.*?\});"
        matched: re.Match[str] | None = re.search(pattern, response_data, re.DOTALL)

        if matched:
            try:
                result: dict[str, dict[str, str]] = json.loads(matched.group(1))
                match arch_value:
                    case ArchEnum.X86_64.value:
                        return result.get("x64DownloadUrl", {}).get("deb")
                    case ArchEnum.AARCH64.value:
                        return result.get("armDownloadUrl", {}).get("deb")
                    case ArchEnum.LOONG64.value:
                        loongarch_url: str | dict[str, str] | None = result.get("loongarchDownloadUrl")
                        if isinstance(loongarch_url, dict):
                            return loongarch_url.get("deb")
                        return loongarch_url
                    case ArchEnum.MIPS64EL.value:
                        mips_url: str | dict[str, str] | None = result.get("mipsDownloadUrl")
                        if isinstance(mips_url, dict):
                            return mips_url.get("deb")
                        return mips_url

            except json.JSONDecodeError:
                print(f"JSON解析失败: {matched.group(1)}")

        return None
