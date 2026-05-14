# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Arch Linux AUR 包自动更新工具，用于从上游获取最新版本并更新 PKGBUILD 文件。项目使用 Python 3.13+ 开发，采用模块化架构。

## 开发命令

```bash
# 进入项目目录
cd scripts

# 运行程序（使用 uv）
uv run main.py                    # 更新所有包
uv run main.py --all              # 更新所有包（显式）
uv run main.py --package qq       # 更新指定包
uv run main.py --list             # 列出所有可用包

# 运行测试（使用 uv）
uv run pytest                     # 运行所有测试
uv run pytest tests/              # 运行所有测试
uv run pytest tests/fetcher/test_fetcher.py  # 运行单个测试文件

# 依赖管理（使用 uv）
uv sync                           # 同步依赖
uv add <package>                  # 添加新依赖
uv remove <package>               # 移除依赖
```

**重要**: 项目统一使用 `uv` 管理和运行，禁止显式使用 `python` 命令（特殊情况除外）。

## 架构设计

### 核心流程

工具采用三阶段处理流程：**Fetch → Parse → Update**

1. **Fetch** (`fetcher/`): 从网络获取版本信息
2. **Parse** (`parsers/`): 解析数据，提取版本号和下载链接
3. **Update** (`updater/`): 更新 PKGBUILD 文件

### 目录结构

```
scripts/                          # 主要代码目录
├── cli/                          # 命令行接口
│   └── cli.py                    # argparse 入口，处理命令行参数
├── core/
│   └── package_updater.py        # PackageUpdater 类，整合三个阶段流程
├── constants/
│   └── constants.py              # 枚举类：ArchEnum、HashAlgorithmEnum、ParserEnum
├── fetcher/
│   └── fetcher.py                # Fetcher 类，HTTP 客户端封装
├── loaders/
│   └── config_loader.py          # ConfigLoader，加载 packages.yaml 配置
├── parsers/
│   ├── base_parser.py            # BaseParser 抽象基类
│   ├── qq.py                     # QQParser 实现
│   └── navicat.py                # NavicatPremiumCSParser 实现
├── updater/
│   └── pkgbuild_editor.py        # PKGBUILDEditor，编辑 PKGBUILD 文件
├── utils/
│   └── hash.py                   # 哈希计算工具函数
├── tests/                        # pytest 测试目录
├── packages.yaml                 # 包配置文件（核心配置）
└── main.py                       # 程序入口

packages/                         # AUR 包目录
├── linuxqq-nt/                   # QQ Linux 包
│   └── PKGBUILD                  # PKGBUILD 文件
└── navicat17-premium-zh-cn/      # Navicat 包
    └── PKGBUILD                  # PKGBUILD 文件

.github/workflows/                # CI/CD 工作流
├── keep-alive.yml                # 每月启用所有 workflow，防止 GitHub 自动停用
├── push-to-aur.yml               # 推送 PKGBUILD 到 AUR
└── update-packages.yml           # 定时检测并更新包版本
```

### 关键类和接口

**BaseParser** (`parsers/base_parser.py`)
- 抽象基类，所有解析器必须继承此类
- 实现两个抽象方法：
  - `parse_version(response_data) -> str | None`: 解析版本号
  - `parse_url(arch, response_data) -> str | None`: 解析下载 URL

**PackageUpdater** (`core/package_updater.py`)
- 核心协调器，整合 fetch、parse、update 三个阶段
- `project_root` 指向 `scripts/` 目录
- `pkgbuild_root` 指向项目根目录（用于定位 PKGBUILD 文件）
- 维护 `parsers` 字典，映射 `ParserEnum` 到解析器实例

**PKGBUILDEditor** (`updater/pkgbuild_editor.py`)
- 使用正则表达式编辑 PKGBUILD 文件
- 支持更新 `pkgver`、`pkgrel`、`source_<arch>`、`sha512sums_<arch>` 等字段
- 注意：文件路径处理使用 `Path` 对象，支持相对和绝对路径

### 配置文件结构

**packages.yaml** 示例：
```yaml
packages:
  qq:
    name: qq                                    # 包名
    source: qq                                  # 来源标识
    fetch_url: "https://..."                    # 获取版本信息的 URL
    upstream: "Tencent/QQ"                      # 上游项目
    parser: QQParser                            # 解析器名称（必须匹配 ParserEnum）
    pkgbuild: "packages/linuxqq-nt/PKGBUILD"    # PKGBUILD 相对路径
    update_source_url: true                     # 是否更新 source URL
    arch:                                       # 支持的架构列表
      - x86_64
      - aarch64
      - loong64
```

### 枚举类型

**ArchEnum** (`constants/constants.py`): 支持的架构
- `X86_64`, `AARCH64`, `LOONG64`, `MIPS64EL`

**HashAlgorithmEnum**: 哈希算法
- `SHA256`, `SHA512`

**ParserEnum**: 解析器名称
- 必须与 `PackageUpdater.parsers` 字典的键对应

## 添加新软件包

1. 在 `packages.yaml` 中添加包配置
2. 在 `parsers/` 中创建新的解析器类，继承 `BaseParser`
3. 在 `constants/constants.py` 的 `ParserEnum` 中添加解析器名称
4. 在 `core/package_updater.py` 的 `PackageUpdater.__init__()` 中注册解析器实例
5. 在 `packages/` 目录中创建对应的 PKGBUILD 文件

## 测试

- 使用 `pytest` 和 `pytest-asyncio`
- 测试文件位于 `scripts/tests/` 目录
- 测试使用 `unittest.mock` 进行异步 HTTP 请求模拟

## 代码规范

### 类型注解（Type Hints）

**重要**: 项目严格使用类型注解，所有函数和方法必须包含完整的类型注解。

#### 基本规则

1. **所有函数必须有返回类型注解**
   ```python
   # ✓ 正确
   def get_version(url: str) -> str | None:
       ...

   # ✗ 错误（缺少返回类型）
   def get_version(url: str):
       ...
   ```

2. **所有参数必须有类型注解**
   ```python
   # ✓ 正确
   async def download_file(url: str, path: Path, retries: int = 3) -> bool:
       ...

   # ✗ 错误（缺少参数类型）
   async def download_file(url, path, retries = 3):
       ...
   ```

3. **使用 Python 3.13+ 的现代类型注解语法**
   ```python
   # ✓ 使用 | 联合类型（Python 3.10+）
   def parse_version(data: str | None) -> str | None:
       ...

   # ✓ 使用 list/dict 泛型（Python 3.9+）
   def get_urls(arch: str) -> list[str]:
       return []

   def get_config() -> dict[str, str]:
       return {}

   # ✗ 避免（旧式语法）
   from typing import List, Dict, Optional, Union
   def parse_version(data: Union[str, None]) -> Optional[str]:
       ...
   ```

4. **类属性和方法注解**
   ```python
   class PackageUpdater:
       parsers: dict[str, BaseParser]  # 类属性类型注解

       def __init__(self) -> None:  # __init__ 返回 None
           self.config: ConfigLoader = ConfigLoader.load_from_yaml()

       def update_package(self, name: str, config: PackageConfig) -> bool:
           ...
   ```

5. **异步函数类型注解**
   ```python
   async def fetch_text(url: str) -> str | None:
       ...

   async def download_all(urls: dict[str, str]) -> dict[str, bool]:
       ...
   ```

6. **复杂类型使用 typing 模块**
   ```python
   from typing import Callable, Any

   def process_data(
       data: dict[str, Any],
       callback: Callable[[str], bool] | None = None
   ) -> bool:
       ...
   ```

#### 类型检查

项目使用 **ty**（Astral 开发的快速 Python 类型检查器）进行静态类型检查：

```bash
# 运行类型检查
uv run ty check

# 检查特定文件或目录
uv run ty check scripts/core/
uv run ty check loaders/ utils/ fetcher/

# 详细输出
uv run ty check -v

# 监视模式（自动重新检查）
uv run ty check --watch
```

#### 类型存根文件

对于第三方库缺少类型注解的情况，使用类型存根：

```bash
# 安装类型存根
uv add --dev types-requests types-pyyaml
```

## 注意事项

- **项目严格使用类型注解**，所有函数必须包含完整的参数和返回类型注解
- **项目使用 uv 统一管理运行环境，禁止显式使用 `python` 命令**
- 项目使用绝对导入（`from cli.cli import update_main`），而不是相对导入
- Python 版本要求 >= 3.13
- PKGBUILD 文件路径相对于项目根目录（`aur-packages/`），而非 `scripts/` 目录
- 下载的文件默认保存在 `scripts/downloads/` 目录
- 支持多架构包，每个架构独立计算校验和
