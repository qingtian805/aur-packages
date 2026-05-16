"""PKGBUILD 编辑器单元测试"""

import pytest

from updater.pkgbuild_editor import PKGBUILDEditor

PKGBUILD_TEMPLATE: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
pkgver=1.0.0
pkgrel=1
arch=('x86_64' 'aarch64')
source=("test.sh" "test.desktop")
source_x86_64=('https://example.com/test-1.0.0-x86_64.tar.gz')
source_aarch64=('https://example.com/test-1.0.0-aarch64.tar.gz')
sha512sums=('SKIP' 'SKIP')
sha512sums_x86_64=('aaa111')
sha512sums_aarch64=('bbb222')
"""


@pytest.fixture
def pkgbuild(tmp_path):
    """创建临时 PKGBUILD 文件"""
    p = tmp_path / "PKGBUILD"
    p.write_text(PKGBUILD_TEMPLATE, encoding="utf-8")
    return p


class TestPKGBUILDEditorGetters:
    def test_get_pkgver(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_pkgver() == "1.0.0"

    def test_get_pkgrel(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_pkgrel() == 1

    def test_get_checksum(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_checksum("x86_64") == "aaa111"
        assert editor.get_checksum("aarch64") == "bbb222"

    def test_get_checksum_no_arch(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_checksum() == "SKIP"


class TestPKGBUILDEditorUpdate:
    def test_update_pkgver(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgver("2.0.0")
        assert editor.get_pkgver() == "2.0.0"

    def test_update_pkgrel(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgrel(3)
        assert editor.get_pkgrel() == 3

    def test_update_arch_checksum(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_arch_checksum("x86_64", "newhash123")
        assert editor.get_checksum("x86_64") == "newhash123"

    def test_update_source_url(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_source_url("x86_64", "https://example.com/test-2.0.0-x86_64.tar.gz")
        assert "test-2.0.0-x86_64" in editor.content

    def test_save_and_reload(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgver("3.0.0")
        editor.save()

        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "3.0.0"
