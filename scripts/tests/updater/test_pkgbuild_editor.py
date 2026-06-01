"""PKGBUILD 编辑器单元测试"""

from pathlib import Path

import pytest

from constants.constants import HashAlgorithmEnum
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

PKGBUILD_B2: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
pkgver=1.0.0
pkgrel=1
arch=('x86_64' 'aarch64')
source=("test.sh" "test.desktop")
source_x86_64=('https://example.com/test-1.0.0-x86_64.tar.gz')
source_aarch64=('https://example.com/test-1.0.0-aarch64.tar.gz')
b2sums=('c1c1c1' 'd2d2d2')
b2sums_x86_64=('eee333')
b2sums_aarch64=('fff444')
"""

PKGBUILD_WITH_EPOCH: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
epoch=5
pkgver=1.0.0
pkgrel=1
sha512sums_x86_64=('aaa111')
"""

PKGBUILD_ALIAS: str = """\
# Maintainer: test <test@test.com>
pkgname=test-pkg
pkgver=1.0.0
pkgrel=1
source_x86_64=("test-${pkgver}-${pkgrel}.tar.gz::https://example.com/test.tar.gz")
sha512sums_x86_64=('aaa111')
"""


@pytest.fixture
def pkgbuild(tmp_path) -> Path:
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

    def test_get_checksum_b2(self, tmp_path: Path) -> None:
        """获取 b2sums 校验和"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_B2, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        b2 = HashAlgorithmEnum.B2.value
        assert editor.get_checksum("x86_64", b2) == "eee333"
        assert editor.get_checksum("aarch64", b2) == "fff444"

    def test_get_checksum_b2_no_arch(self, tmp_path: Path) -> None:
        """获取 b2sums 无架构校验和"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_B2, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert (
            editor.get_checksum(hash_algorithm=HashAlgorithmEnum.B2.value) == "c1c1c1"
        )

    def test_get_checksum_algorithm_not_found(self, pkgbuild) -> None:
        """PKGBUILD 中不存在该算法的校验和时返回空字符串"""
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_checksum("x86_64", HashAlgorithmEnum.B2.value) == ""


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

    def test_update_arch_checksum_b2(self, tmp_path: Path) -> None:
        """更新 b2sums 架构校验和"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_B2, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        b2 = HashAlgorithmEnum.B2.value
        editor.update_arch_checksum("x86_64", "new_b2_hash", b2)
        assert editor.get_checksum("x86_64", b2) == "new_b2_hash"

    def test_update_source_url(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_source_url(
            "x86_64", "https://example.com/test-2.0.0-x86_64.tar.gz"
        )
        assert "test-2.0.0-x86_64" in editor.content

    def test_save_and_reload(self, pkgbuild) -> None:
        editor = PKGBUILDEditor(pkgbuild)
        editor.update_pkgver("3.0.0")
        editor.save()

        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "3.0.0"


class TestPKGBUILDEditorEpoch:
    """update_epoch 和 get_epoch 测试"""

    def test_update_epoch_existing(self, tmp_path: Path) -> None:
        """替换已有的 epoch 行"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_WITH_EPOCH, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        editor.update_epoch(10)
        assert editor.get_epoch() == 10

    def test_update_epoch_insert(self, pkgbuild) -> None:
        """无 epoch 行时在 pkgver 前插入"""
        editor = PKGBUILDEditor(pkgbuild)
        assert editor.get_epoch() is None
        editor.update_epoch(5)
        assert editor.get_epoch() == 5

    def test_update_epoch_none(self, pkgbuild) -> None:
        """new_epoch=None 时不做任何修改"""
        editor = PKGBUILDEditor(pkgbuild)
        original = editor.content
        editor.update_epoch(None)
        assert editor.content == original

    def test_get_epoch_non_integer(self, tmp_path: Path) -> None:
        """epoch 值非整数时返回 None"""
        p = tmp_path / "PKGBUILD"
        p.write_text("pkgname=test\nepoch=abc\npkgver=1.0\n", encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert editor.get_epoch() is None


class TestPKGBUILDEditorEdgeCases:
    """边界条件测试"""

    def test_get_pkgrel_non_integer(self, tmp_path: Path) -> None:
        """pkgrel 非数字时返回默认值 1"""
        p = tmp_path / "PKGBUILD"
        p.write_text("pkgname=test\npkgver=1.0\npkgrel=abc\n", encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert editor.get_pkgrel() == 1

    def test_get_pkgrel_missing(self, tmp_path: Path) -> None:
        """无 pkgrel 行时返回默认值 1"""
        p = tmp_path / "PKGBUILD"
        p.write_text("pkgname=test\npkgver=1.0\n", encoding="utf-8")
        editor = PKGBUILDEditor(p)
        assert editor.get_pkgrel() == 1

    def test_source_url_alias_preserved(self, tmp_path: Path) -> None:
        """更新 source URL 时保留 :: 别名"""
        p = tmp_path / "PKGBUILD"
        p.write_text(PKGBUILD_ALIAS, encoding="utf-8")
        editor = PKGBUILDEditor(p)
        editor.update_source_url("x86_64", "https://example.com/test-v2.tar.gz")
        assert "test-${pkgver}-${pkgrel}.tar.gz::" in editor.content
        assert "test-v2.tar.gz" in editor.content


class TestPKGBUILDEditorContextManager:
    """上下文管理器测试"""

    def test_auto_save_on_normal_exit(self, pkgbuild) -> None:
        """with 块正常退出时自动保存"""
        with PKGBUILDEditor(pkgbuild) as editor:
            editor.update_pkgver("9.0.0")

        # 重新加载验证已保存
        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "9.0.0"

    def test_no_save_on_exception(self, pkgbuild) -> None:
        """with 块抛异常时不保存"""
        try:
            with PKGBUILDEditor(pkgbuild) as editor:
                editor.update_pkgver("9.0.0")
                raise RuntimeError("test error")
        except RuntimeError:
            pass

        # 重新加载验证未保存
        editor2 = PKGBUILDEditor(pkgbuild)
        assert editor2.get_pkgver() == "1.0.0"
