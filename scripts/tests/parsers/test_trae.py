"""TraeParser 单元测试"""

import json

import pytest

from constants.constants import ArchEnum
from parsers.trae import TraeParser, TraeRegion

TRAEE_API_RESPONSE: dict = {
    "data": {
        "manifest": {
            "linux": {
                "version": "2.3.25937",
                "download": [
                    {
                        "region": "cn",
                        "x64.tar.gz": "https://lf-cdn.trae.com.cn/obj/trae-com-cn/x64.tar.gz",
                        "arm64.tar.gz": "https://lf-cdn.trae.com.cn/obj/trae-com-cn/arm64.tar.gz",
                    },
                    {
                        "region": "sg",
                        "x64.tar.gz": "https://lf-cdn.trae.ai/obj/trae-ai-sg/x64.tar.gz",
                        "arm64.tar.gz": "https://lf-cdn.trae.ai/obj/trae-ai-sg/arm64.tar.gz",
                    },
                    {
                        "region": "va",
                        "x64.tar.gz": "https://lf-cdn.trae.ai/obj/trae-ai-us/x64.tar.gz",
                        "arm64.tar.gz": "https://lf-cdn.trae.ai/obj/trae-ai-us/arm64.tar.gz",
                    },
                ],
            }
        }
    }
}


@pytest.fixture
def trae_json() -> str:
    return json.dumps(TRAEE_API_RESPONSE)


class TestTraeParseVersion:
    def test_valid_json(self, trae_json: str) -> None:
        parser = TraeParser()
        assert parser.parse_version(trae_json) == "2.3.25937"

    def test_non_string_input(self) -> None:
        parser = TraeParser()
        assert parser.parse_version(None) is None
        assert parser.parse_version(123) is None

    def test_malformed_json(self) -> None:
        parser = TraeParser()
        assert parser.parse_version("not json") is None

    def test_missing_key(self) -> None:
        parser = TraeParser()
        assert parser.parse_version('{"data": {}}') is None


class TestTraeParseUrl:
    def test_cn_region(self, trae_json: str) -> None:
        parser = TraeParser()
        url = parser.parse_url(ArchEnum.X86_64, trae_json)
        assert url == "https://lf-cdn.trae.com.cn/obj/trae-com-cn/x64.tar.gz"

    def test_sg_region(self, trae_json: str) -> None:
        parser = TraeParser(region=TraeRegion.SG)
        url = parser.parse_url(ArchEnum.X86_64, trae_json)
        assert url == "https://lf-cdn.trae.ai/obj/trae-ai-sg/x64.tar.gz"

    def test_us_region(self, trae_json: str) -> None:
        parser = TraeParser(region=TraeRegion.US)
        url = parser.parse_url(ArchEnum.AARCH64, trae_json)
        assert url == "https://lf-cdn.trae.ai/obj/trae-ai-us/arm64.tar.gz"

    def test_no_matching_region(self, trae_json: str) -> None:
        parser = TraeParser(region=TraeRegion.CN)
        # 构造一个不包含 cn region 的响应
        no_cn = '{"data":{"manifest":{"linux":{"version":"1.0","download":[{"region":"sg","x64.tar.gz":"https://sg/x64.tar.gz"}]}}}}'
        assert parser.parse_url(ArchEnum.X86_64, no_cn) is None

    def test_unsupported_arch(self, trae_json: str) -> None:
        parser = TraeParser()
        assert parser.parse_url(ArchEnum.LOONG64, trae_json) is None

    def test_non_string_input(self) -> None:
        parser = TraeParser()
        assert parser.parse_url(ArchEnum.X86_64, None) is None
