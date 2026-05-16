# AUR 包自动更新工具

> 自动化 Arch Linux AUR 包版本更新工具

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 特性

- 自动获取最新版本并更新 PKGBUILD
- 多架构支持：x86_64、aarch64、loong64
- SHA512 校验和自动计算
- 基于 aria2c 的多连接分片下载
- 插件化解析器设计，易于扩展

## 快速开始

```bash
git clone https://github.com/awsl1414/aur-packages.git
cd aur-packages/scripts

# 安装系统依赖
sudo pacman -S aria2   # 或 sudo apt install aria2

# 安装 Python 依赖
pip install uv
uv sync

# 运行
uv run main.py              # 更新所有包
uv run main.py --package qq # 更新指定包
uv run main.py --list       # 列出所有包
```

## 支持的包

- `linuxqq-nt` - QQ Linux
- `navicat17-premium-zh-cn` - Navicat Premium

## 添加新包

1. **编辑配置** (`scripts/config.yaml`)
2. **创建解析器** (`scripts/parsers/`)，继承 `BaseParser`
3. **注册解析器**：在 `constants/constants.py` 的 `ParserEnum` 和 `core/package_updater.py` 中注册
4. **创建 PKGBUILD**：在 `packages/` 目录

详细步骤见 [CLAUDE.md](CLAUDE.md)。

## 开发

```bash
uv run pytest    # 运行测试
uv run ty check  # 类型检查
uv sync          # 同步依赖
```

## 技术栈

- Python 3.13+ / uv
- aria2c (多线程下载)
- httpx (异步 HTTP)
- pydantic (数据验证)

## 许可证

MIT License
