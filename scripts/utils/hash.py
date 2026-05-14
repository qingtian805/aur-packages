"""哈希计算工具模块"""

import hashlib
from collections.abc import Callable
from pathlib import Path

from constants.constants import HashAlgorithmEnum

_HASH_BUILDERS: dict[str, Callable[[], hashlib._hashlib.HASH]] = {
    HashAlgorithmEnum.SHA256.value: hashlib.sha256,
    HashAlgorithmEnum.SHA512.value: hashlib.sha512,
}


def calculate_file_hash(
    file_path: str | Path, hash_algorithm: str = HashAlgorithmEnum.SHA512.value
) -> str:
    """
    计算文件哈希值

    支持 SHA256 和 SHA512 算法，分块读取大文件避免内存占用过高
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if hash_algorithm.lower() not in _HASH_BUILDERS:
        raise ValueError(
            f"不支持的哈希算法: {hash_algorithm}，支持的算法: {list(_HASH_BUILDERS.keys())}"
        )

    hash_func: hashlib._hashlib.HASH = _HASH_BUILDERS[hash_algorithm.lower()]()

    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def calculate_multiple_hashes(
    file_path: str | Path, algorithms: list[str] | None = None
) -> dict[str, str]:
    """一次性计算文件的多种哈希值，只读取文件一次"""
    file_path = Path(file_path)

    if algorithms is None:
        algorithms = [HashAlgorithmEnum.SHA256.value, HashAlgorithmEnum.SHA512.value]

    hashers: list[hashlib._hashlib.HASH] = [_HASH_BUILDERS[alg.lower()]() for alg in algorithms]

    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            for hasher in hashers:
                hasher.update(chunk)

    return {alg: hasher.hexdigest() for alg, hasher in zip(algorithms, hashers)}


def verify_file_hash(
    file_path: str | Path,
    expected_hash: str,
    hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
) -> bool:
    """验证文件哈希值是否匹配预期值"""
    try:
        actual_hash = calculate_file_hash(file_path, hash_algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except (FileNotFoundError, ValueError):
        return False


def format_checksum_for_pkgbuild(
    checksum: str,
    arch: str | None = None,
    hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
) -> str:
    """格式化校验和为 PKGBUILD 语法"""
    algo_name = hash_algorithm.lower()
    if arch:
        return f"{algo_name}sums_{arch}=('{checksum}')"
    return f"{algo_name}sums=('{checksum}')"
