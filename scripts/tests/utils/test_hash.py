"""hash 工具模块单元测试"""

from pathlib import Path

import pytest

from constants.constants import HashAlgorithmEnum
from utils.hash import (
    calculate_file_hash,
    calculate_multiple_hashes,
    format_checksum_for_pkgbuild,
    verify_file_hash,
)


class TestCalculateFileHash:
    """calculate_file_hash 测试"""

    def test_sha512(self, tmp_path: Path) -> None:
        """正常计算 SHA512"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        result = calculate_file_hash(f, HashAlgorithmEnum.SHA512.value)
        assert isinstance(result, str)
        assert len(result) == 128  # SHA512 hex 长度

    def test_sha256(self, tmp_path: Path) -> None:
        """正常计算 SHA256"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        result = calculate_file_hash(f, HashAlgorithmEnum.SHA256.value)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex 长度

    def test_b2(self, tmp_path: Path) -> None:
        """正常计算 BLAKE2b (b2)"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        result = calculate_file_hash(f, HashAlgorithmEnum.B2.value)
        assert isinstance(result, str)
        assert len(result) == 128  # BLAKE2b 默认 512-bit，hex 长度 128

    def test_file_not_found(self) -> None:
        """文件不存在抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            calculate_file_hash("/nonexistent/file.bin")

    def test_unsupported_algorithm(self, tmp_path: Path) -> None:
        """不支持的算法抛出 ValueError"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"data")
        with pytest.raises(ValueError, match="不支持的哈希算法"):
            calculate_file_hash(f, "md5")

    def test_empty_file(self, tmp_path: Path) -> None:
        """空文件正常计算哈希"""
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        result = calculate_file_hash(f, HashAlgorithmEnum.SHA512.value)
        assert isinstance(result, str)
        assert len(result) == 128


class TestCalculateMultipleHashes:
    """calculate_multiple_hashes 测试"""

    def test_default_algorithms(self, tmp_path: Path) -> None:
        """默认计算 SHA256 + SHA512"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        result = calculate_multiple_hashes(f)
        assert "sha256" in result
        assert "sha512" in result
        assert len(result) == 2

    def test_custom_algorithms(self, tmp_path: Path) -> None:
        """自定义算法列表"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        result = calculate_multiple_hashes(f, [HashAlgorithmEnum.SHA512.value])
        assert len(result) == 1
        assert "sha512" in result

    def test_b2_in_multiple(self, tmp_path: Path) -> None:
        """包含 b2 的多种算法"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        result = calculate_multiple_hashes(
            f,
            [HashAlgorithmEnum.SHA512.value, HashAlgorithmEnum.B2.value],
        )
        assert len(result) == 2
        assert "sha512" in result
        assert "b2" in result


class TestVerifyFileHash:
    """verify_file_hash 测试"""

    def test_matching_hash(self, tmp_path: Path) -> None:
        """哈希匹配返回 True"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        expected = calculate_file_hash(f, HashAlgorithmEnum.SHA512.value)
        assert verify_file_hash(f, expected) is True

    def test_non_matching_hash(self, tmp_path: Path) -> None:
        """哈希不匹配返回 False"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        assert verify_file_hash(f, "0" * 128) is False

    def test_file_not_found(self) -> None:
        """文件不存在返回 False"""
        assert verify_file_hash("/nonexistent/file.bin", "abc") is False

    def test_case_insensitive(self, tmp_path: Path) -> None:
        """大小写不敏感仍匹配"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        expected = calculate_file_hash(f, HashAlgorithmEnum.SHA512.value)
        assert verify_file_hash(f, expected.upper()) is True

    def test_b2_matching(self, tmp_path: Path) -> None:
        """b2 哈希匹配"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        expected = calculate_file_hash(f, HashAlgorithmEnum.B2.value)
        assert (
            verify_file_hash(f, expected, hash_algorithm=HashAlgorithmEnum.B2.value)
            is True
        )

    def test_b2_non_matching(self, tmp_path: Path) -> None:
        """b2 哈希不匹配"""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello")
        assert (
            verify_file_hash(f, "0" * 128, hash_algorithm=HashAlgorithmEnum.B2.value)
            is False
        )


class TestFormatChecksumForPkgbuild:
    """format_checksum_for_pkgbuild 测试"""

    def test_with_arch(self) -> None:
        """带架构后缀"""
        result = format_checksum_for_pkgbuild("abc123", arch="x86_64")
        assert result == "sha512sums_x86_64=('abc123')"

    def test_without_arch(self) -> None:
        """不带架构后缀"""
        result = format_checksum_for_pkgbuild("abc123")
        assert result == "sha512sums=('abc123')"

    def test_custom_algorithm(self) -> None:
        """自定义算法"""
        result = format_checksum_for_pkgbuild(
            "abc123", hash_algorithm=HashAlgorithmEnum.SHA256.value
        )
        assert result == "sha256sums=('abc123')"

    def test_b2_with_arch(self) -> None:
        """b2 带架构后缀"""
        result = format_checksum_for_pkgbuild(
            "abc123", arch="x86_64", hash_algorithm=HashAlgorithmEnum.B2.value
        )
        assert result == "b2sums_x86_64=('abc123')"

    def test_b2_without_arch(self) -> None:
        """b2 不带架构后缀"""
        result = format_checksum_for_pkgbuild(
            "abc123", hash_algorithm=HashAlgorithmEnum.B2.value
        )
        assert result == "b2sums=('abc123')"
