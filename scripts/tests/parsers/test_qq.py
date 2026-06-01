"""QQParser 单元测试"""

from constants.constants import ArchEnum
from parsers.qq import QQParser

QQ_JS_RESPONSE: str = """
var params = {
    "version": "3.2.28",
    "x64DownloadUrl": {
        "deb": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.28_260429_amd64_01.deb"
    },
    "armDownloadUrl": {
        "deb": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.28_260429_arm64_01.deb"
    },
    "loongarchDownloadUrl": {
        "deb": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.28_260429_loongarch64_01.deb"
    },
    "mipsDownloadUrl": {
        "deb": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.28_260429_mips64el_01.deb"
    }
};
"""


class TestQQParseVersion:
    def test_valid_js(self) -> None:
        parser = QQParser()
        assert parser.parse_version(QQ_JS_RESPONSE) == "3.2.28_260429"

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_version(None) is None

    def test_no_json_block(self) -> None:
        parser = QQParser()
        assert parser.parse_version("no var params here") is None

    def test_missing_version_field(self) -> None:
        parser = QQParser()
        js = 'var params = {"x64DownloadUrl": {"deb": "https://example.com/QQ_1.0.0_123_amd64.deb"}};'
        assert parser.parse_version(js) is None

    def test_version_mismatch(self) -> None:
        parser = QQParser()
        js = """
        var params = {
            "version": "3.2.29",
            "x64DownloadUrl": {"deb": "https://example.com/QQ_3.2.28_260429_amd64.deb"}
        };
        """
        assert parser.parse_version(js) is None

    def test_malformed_json_in_params(self) -> None:
        """能匹配 var params 但内容不是合法 JSON 时返回 None"""
        parser = QQParser()
        js = "var params = {invalid json not parseable};"
        assert parser.parse_version(js) is None


class TestQQParseUrl:
    def test_x86_64(self) -> None:
        parser = QQParser()
        url = parser.parse_url(ArchEnum.X86_64, QQ_JS_RESPONSE)
        assert url is not None
        assert "amd64" in url
        assert url.endswith(".deb")

    def test_aarch64(self) -> None:
        parser = QQParser()
        url = parser.parse_url(ArchEnum.AARCH64, QQ_JS_RESPONSE)
        assert url is not None
        assert "arm64" in url

    def test_loong64(self) -> None:
        parser = QQParser()
        url = parser.parse_url(ArchEnum.LOONG64, QQ_JS_RESPONSE)
        assert url is not None
        assert "loongarch64" in url

    def test_mips64el(self) -> None:
        parser = QQParser()
        url = parser.parse_url(ArchEnum.MIPS64EL, QQ_JS_RESPONSE)
        assert url is not None
        assert "mips64el" in url

    def test_non_string_input(self) -> None:
        parser = QQParser()
        assert parser.parse_url(ArchEnum.X86_64, None) is None
