"""NavicatPremiumCSParser 单元测试"""

from constants.constants import ArchEnum
from parsers.navicat import NavicatPremiumCSParser

NAVICAT_HTML: str = "<html>Navicat Premium (Linux) version 17.3.8 released</html>"

NAVICAT_URLS: dict[str, str] = {
    "x86_64": "https://dn.navicat.com/download/navicat17-premium-cs-x86_64.AppImage",
    "aarch64": "https://dn.navicat.com/download/navicat17-premium-cs-aarch64.AppImage",
}


class TestNavicatParseVersion:
    def test_valid_html(self) -> None:
        parser = NavicatPremiumCSParser()
        assert parser.parse_version(NAVICAT_HTML) == "17.3.8"

    def test_non_string_input(self) -> None:
        parser = NavicatPremiumCSParser()
        assert parser.parse_version(None) is None
        assert parser.parse_version(123) is None

    def test_no_match(self) -> None:
        parser = NavicatPremiumCSParser()
        assert parser.parse_version("<html>no version info</html>") is None


class TestNavicatParseUrl:
    def test_x86_64(self) -> None:
        parser = NavicatPremiumCSParser(urls=NAVICAT_URLS)
        assert parser.parse_url(ArchEnum.X86_64, "") == NAVICAT_URLS["x86_64"]

    def test_aarch64(self) -> None:
        parser = NavicatPremiumCSParser(urls=NAVICAT_URLS)
        assert parser.parse_url(ArchEnum.AARCH64, "") == NAVICAT_URLS["aarch64"]

    def test_unsupported_arch(self) -> None:
        parser = NavicatPremiumCSParser(urls=NAVICAT_URLS)
        assert parser.parse_url(ArchEnum.LOONG64, "") is None

    def test_empty_urls(self) -> None:
        parser = NavicatPremiumCSParser()
        assert parser.parse_url(ArchEnum.X86_64, "") is None

    def test_string_arch(self) -> None:
        parser = NavicatPremiumCSParser(urls=NAVICAT_URLS)
        assert parser.parse_url("x86_64", "") == NAVICAT_URLS["x86_64"]
