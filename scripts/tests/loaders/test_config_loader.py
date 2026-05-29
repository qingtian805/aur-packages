"""配置加载器单元测试"""

from pathlib import Path

import pytest

from constants.constants import ArchEnum
from loaders.config_loader import ConfigLoader, PackageConfig


class TestPackageConfig:
    def test_defaults(self) -> None:
        config = PackageConfig(
            name="test",
            source="test",
            fetch_url="https://example.com",
            upstream="test/test",
            parser="TestParser",
            pkgbuild="packages/test/PKGBUILD",
        )
        assert config.update_source_url is True
        assert config.enable is True
        assert config.urls == {}
        assert config.arch == []

    def test_urls_field(self) -> None:
        config = PackageConfig(
            name="test",
            source="test",
            fetch_url="https://example.com",
            upstream="test/test",
            parser="TestParser",
            pkgbuild="packages/test/PKGBUILD",
            urls={"x86_64": "https://example.com/test.AppImage"},
        )
        assert config.urls["x86_64"] == "https://example.com/test.AppImage"

    def test_get_supported_archs(self) -> None:
        config = PackageConfig(
            name="test",
            source="test",
            fetch_url="https://example.com",
            upstream="test/test",
            parser="TestParser",
            pkgbuild="packages/test/PKGBUILD",
            arch=["x86_64", "aarch64"],
        )
        archs = config.get_supported_archs()
        assert archs == [ArchEnum.X86_64, ArchEnum.AARCH64]

    def test_get_supported_archs_empty(self) -> None:
        config = PackageConfig(
            name="test",
            source="test",
            fetch_url="https://example.com",
            upstream="test/test",
            parser="TestParser",
            pkgbuild="packages/test/PKGBUILD",
        )
        assert config.get_supported_archs() == []

    def test_extra_fields_ignored(self) -> None:
        config = PackageConfig(
            name="test",
            source="test",
            fetch_url="https://example.com",
            upstream="test/test",
            parser="TestParser",
            pkgbuild="packages/test/PKGBUILD",
        )
        assert config.name == "test"


class TestConfigLoader:
    def test_load_from_yaml(self) -> None:
        loader = ConfigLoader.load_from_yaml()
        assert "qq" in loader.packages
        assert "navicat" in loader.packages
        assert "trae" in loader.packages
        assert loader.packages["qq"].parser == "QQParser"

    def test_navicat_urls_loaded(self) -> None:
        loader = ConfigLoader.load_from_yaml()
        navicat = loader.packages["navicat"]
        assert "x86_64" in navicat.urls
        assert "aarch64" in navicat.urls

    def test_load_empty_yaml(self, tmp_path: Path) -> None:
        """空 YAML 文件抛出 ValueError"""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="配置文件为空"):
            ConfigLoader.load_from_yaml(str(empty_file))

    def test_load_missing_file(self) -> None:
        """不存在的文件抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_yaml("/nonexistent/config.yaml")


class TestPackageConfigUnknownArch:
    def test_unknown_arch_skipped(self) -> None:
        """未知架构字符串被跳过"""
        config = PackageConfig(
            name="test",
            source="test",
            fetch_url="https://example.com",
            upstream="test/test",
            parser="TestParser",
            pkgbuild="packages/test/PKGBUILD",
            arch=["x86_64", "riscv64"],
        )
        archs = config.get_supported_archs()
        assert archs == [ArchEnum.X86_64]
