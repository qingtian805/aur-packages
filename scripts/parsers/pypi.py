"""PyPI 包解析器"""

import json
import logging
from typing import Any

from constants.constants import ArchEnum

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class PyPIParser(BaseParser):
    """PyPI 包解析器

    从 PyPI JSON API 获取包的最新版本和 sdist 下载 URL。

    API 端点: https://pypi.org/pypi/{package_name}/json
    """

    def __init__(self, package_name: str) -> None:
        self._package_name = package_name

    def parse_version(self, response_data: str | Any) -> str | None:
        """从 PyPI JSON 响应中提取版本号"""
        if not isinstance(response_data, str):
            return None

        try:
            data: dict[str, Any] = json.loads(response_data)
        except json.JSONDecodeError:
            logger.warning("PyPI(%s): JSON 解析失败", self._package_name)
            return None

        version: str | None = data.get("info", {}).get("version")
        if not version:
            logger.warning("PyPI(%s): 缺少 version 字段", self._package_name)
            return None

        return version

    def parse_url(self, arch: ArchEnum | str, response_data: str | Any) -> str | None:
        """从 PyPI JSON 响应中提取 sdist 下载 URL

        对于 arch='any' 的纯 Python 包，返回 sdist URL。
        """
        if not isinstance(response_data, str):
            return None

        try:
            data: dict[str, Any] = json.loads(response_data)
        except json.JSONDecodeError:
            return None

        urls: list[dict[str, Any]] = data.get("urls", [])
        for url_info in urls:
            if url_info.get("packagetype") == "sdist":
                download_url: str | None = url_info.get("url")
                if download_url:
                    return download_url

        logger.warning("PyPI(%s): 未找到 sdist 下载 URL", self._package_name)
        return None
