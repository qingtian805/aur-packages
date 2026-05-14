"""Navicat Premium 版本解析器"""

import re
from typing import Any

from constants.constants import ArchEnum, NAVICAT_URLS
from .base_parser import BaseParser


class NavicatPremiumCSParser(BaseParser):
    """Navicat Premium CS 版本解析器"""

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 Navicat 响应数据中提取版本号"""
        if not isinstance(response_data, str):
            return None
        pattern: str = r"(Navicat[^()]*\(Linux\)[^v]*version[^\d]*)(\d+\.\d+\.\d+)"
        matched: re.Match[str] | None = re.search(pattern, response_data, re.IGNORECASE)
        return matched.group(2) if matched else None

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从预定义映射中获取 Navicat 下载 URL"""
        if not isinstance(response_data, str):
            return None
        match arch:
            case ArchEnum.X86_64:
                return NAVICAT_URLS[ArchEnum.X86_64]
            case ArchEnum.AARCH64:
                return NAVICAT_URLS[ArchEnum.AARCH64]
            case _:
                return None
