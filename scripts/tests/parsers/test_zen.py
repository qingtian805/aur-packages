"""ZenParser 单元测试"""

import json
from typing import Any


from constants.constants import ArchEnum
from parsers.zen import ZenParser


def _make_zen_response(
    name: str = "Twilight build - 1.21t (2026-05-30 at 02:13:41)",
    assets: list[dict[str, Any]] | None = None,
) -> str:
    """构造 Zen GitHub Release JSON 响应"""
    if assets is None:
        assets = [
            {
                "name": "zen.linux-x86_64.tar.xz",
                "browser_download_url": "https://github.com/zen-browser/desktop/releases/download/twilight-1/zen.linux-x86_64.tar.xz",
            },
            {
                "name": "zen.linux-aarch64.tar.xz",
                "browser_download_url": "https://github.com/zen-browser/desktop/releases/download/twilight-1/zen.linux-aarch64.tar.xz",
            },
        ]
    return json.dumps({"name": name, "assets": assets})


class TestZenParseVersion:
    """ZenParser.parse_version 测试"""

    def setup_method(self) -> None:
        self.parser = ZenParser()

    def test_valid_response(self) -> None:
        """正常从 release name 提取版本号"""
        result = self.parser.parse_version(
            _make_zen_response(name="Twilight build - 1.21t (2026-05-30)")
        )
        assert result == "1.21t"

    def test_version_without_letter(self) -> None:
        """版本号无后缀字母"""
        result = self.parser.parse_version(
            _make_zen_response(name="Twilight build - 1.20 (2026-05-01)")
        )
        assert result == "1.20"

    def test_json_decode_failure(self) -> None:
        """JSON 解析失败返回 None"""
        result = self.parser.parse_version("not valid json{")
        assert result is None

    def test_missing_name_field(self) -> None:
        """缺少 name 字段返回 None"""
        result = self.parser.parse_version(json.dumps({"assets": []}))
        assert result is None

    def test_no_version_in_name(self) -> None:
        """name 中无匹配版本号返回 None"""
        result = self.parser.parse_version(
            _make_zen_response(name="Twilight build - nightly")
        )
        assert result is None

    def test_non_string_input(self) -> None:
        """非字符串输入返回 None"""
        assert self.parser.parse_version(None) is None  # type: ignore[arg-type]
        assert self.parser.parse_version(123) is None  # type: ignore[arg-type]


class TestZenParseUrl:
    """ZenParser.parse_url 测试"""

    def setup_method(self) -> None:
        self.parser = ZenParser()

    def test_x86_64(self) -> None:
        """x86_64 架构正常匹配"""
        result = self.parser.parse_url(ArchEnum.X86_64, _make_zen_response())
        assert result is not None
        assert "zen.linux-x86_64.tar.xz" in result

    def test_aarch64(self) -> None:
        """aarch64 架构正常匹配"""
        result = self.parser.parse_url(ArchEnum.AARCH64, _make_zen_response())
        assert result is not None
        assert "zen.linux-aarch64.tar.xz" in result

    def test_unsupported_arch(self) -> None:
        """不支持的架构（loong64）返回 None"""
        result = self.parser.parse_url(ArchEnum.LOONG64, _make_zen_response())
        assert result is None

    def test_no_matching_asset(self) -> None:
        """assets 列表中无匹配项"""
        result = self.parser.parse_url(
            ArchEnum.X86_64,
            _make_zen_response(assets=[{"name": "other-file.zip"}]),
        )
        assert result is None

    def test_empty_assets(self) -> None:
        """空 assets 列表返回 None"""
        result = self.parser.parse_url(
            ArchEnum.X86_64,
            _make_zen_response(assets=[]),
        )
        assert result is None

    def test_non_string_input(self) -> None:
        """非字符串输入返回 None"""
        assert self.parser.parse_url(ArchEnum.X86_64, None) is None  # type: ignore[arg-type]

    def test_string_arch(self) -> None:
        """字符串架构参数正常工作"""
        result = self.parser.parse_url("x86_64", _make_zen_response())
        assert result is not None
