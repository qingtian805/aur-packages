# B2 (BLAKE2b) 哈希算法支持设计

## 背景

项目 `zen-browser-twilight-bin` 包的 PKGBUILD 使用 `b2sums`（BLAKE2b），但自动更新工具硬编码 SHA512，导致该包无法被正确更新。

## 目标

使 `scripts/` 支持 BLAKE2b 哈希算法，通过配置驱动每个包的哈希算法选择，同时消除代码中所有 SHA512 硬编码。

## 设计

### 1. HashAlgorithmEnum 新增 B2

**文件**: `constants/constants.py`

```python
class HashAlgorithmEnum(Enum):
    SHA256 = "sha256"
    SHA512 = "sha512"
    B2 = "b2"
```

### 2. 注册 blake2b 构建器

**文件**: `utils/hash.py`

`_HASH_BUILDERS` 新增 `"b2": hashlib.blake2b`。blake2b 默认输出 512-bit（与 SHA512 等长），hexdigest 为 128 字符。现有函数 `calculate_file_hash`、`calculate_multiple_hashes`、`verify_file_hash` 均为算法无关设计，无需改动。

### 3. 配置模型新增 hash_algorithm 字段

**文件**: `loaders/config_loader.py`

- `Settings` 新增 `hash_algorithm: str = "sha512"`（全局默认）
- `PackageConfig` 新增 `hash_algorithm: str | None = None`（包级覆盖，None 表示使用全局默认）
- 新增 `get_effective_hash_algorithm(default: str) -> str` 方法

### 4. config.yaml 配置

**文件**: `config.yaml`

```yaml
settings:
  hash_algorithm: sha512
  download: ...

packages:
  zen-browser:
    hash_algorithm: b2    # 包级覆盖
    # 其余包不需要显式声明，自动使用全局默认 sha512
```

### 5. PKGBUILDEditor API 清理

**文件**: `updater/pkgbuild_editor.py`

**删除**:
- `update_sha512sums()` — 删除，不再保留

**修改**:
- `get_checksum(arch, hash_algorithm="sha512")` → 新增 `hash_algorithm` 参数，regex 从硬编码 `sha512sums` 改为 `f"{hash_algorithm}sums"`

**不变**:
- `update_arch_checksum(arch, checksum, hash_algorithm="sha512")` — 已参数化

### 6. PackageUpdater 消除硬编码

**文件**: `core/package_updater.py`

- `update_package()`: 从 `package_config.get_effective_hash_algorithm(settings.hash_algorithm)` 获取生效算法，传入子方法
- `_calculate_checksum(file_path, hash_algorithm)`: 参数化算法
- `_handle_version_not_newer()`: 接收 hash_algorithm，传递给 `editor.get_checksum()` 和 `editor.update_arch_checksum()`
- `_handle_version_update()`: 接收 hash_algorithm，传递给 `editor.update_arch_checksum()`

### 7. 单元测试补充

**文件**: `tests/utils/test_hash.py`

- `TestCalculateFileHash`: 新增 `test_b2` 验证 hex 长度 128
- `TestCalculateMultipleHashes`: 新增包含 b2 的自定义算法测试
- `TestVerifyFileHash`: 新增 b2 算法验证测试

**文件**: `tests/updater/test_pkgbuild_editor.py`

- 新增 `PKGBUILD_B2` 模板（使用 b2sums 字段）
- 新增 `test_get_checksum_b2` / `test_update_arch_checksum_b2` 测试
- 更新受影响的旧测试（删除 `update_sha512sums` 相关测试，`get_checksum` 测试加上 hash_algorithm 参数）

## 不在范围内

- 不修改任何 `packages/` 下的 PKGBUILD 文件
- 不修改解析器逻辑
- 不修改 fetcher 逻辑
