# AUR 包自动更新工具 - 文档索引

> 📚 **项目文档中心** | Arch Linux AUR 包自动更新工具的完整技术文档

## 📖 文档目录

### 1. [快速入门](./01-quickstart.md)
- 项目简介
- 环境要求
- 安装配置
- 快速开始使用

### 2. [架构设计](./02-architecture.md)
- 核心流程（Fetch → Parse → Update）
- 模块化架构
- 目录结构
- 设计模式与原则

### 3. [API 参考](./03-api-reference.md)
- **核心模块**
  - PackageUpdater - 包更新器
  - ConfigLoader - 配置加载器
- **解析器模块**
  - BaseParser - 解析器基类
  - QQParser - QQ 包解析器
  - NavicatPremiumCSParser - Navicat 包解析器
- **工具模块**
  - Fetcher - HTTP 客户端
  - PKGBUILDEditor - PKGBUILD 文件编辑器
  - Hash 工具 - 哈希计算工具
- **枚举类型**
  - ArchEnum - 支持的架构
  - HashAlgorithmEnum - 哈希算法
  - ParserEnum - 解析器名称

### 4. [开发指南](./04-development-guide.md)
- 开发环境搭建
- 添加新软件包
- 创建自定义解析器
- 测试与调试
- 代码规范

### 5. [配置文件说明](./05-configuration.md)
- packages.yaml 配置格式
- 包配置字段说明
- 架构支持配置
- 示例配置

### 6. [常见问题](./06-faq.md)
- 常见错误处理
- 故障排查指南
- 最佳实践

## 🚀 快速导航

### 按角色查找

**新手用户**
- → [快速入门](./01-quickstart.md)
- → [常见问题](./06-faq.md)

**开发者**
- → [架构设计](./02-architecture.md)
- → [开发指南](./04-development-guide.md)
- → [API 参考](./03-api-reference.md)

**贡献者**
- → [开发指南](./04-development-guide.md)
- → [配置文件说明](./05-configuration.md)

### 按任务查找

**添加新包**
1. [配置文件说明](./05-configuration.md) - 添加包配置
2. [开发指南](./04-development-guide.md) - 创建解析器
3. [API 参考 - BaseParser](./03-api-reference.md#baseparser) - 实现解析器接口

**更新现有包**
- [快速入门](./01-quickstart.md) - 运行更新命令
- [API 参考 - PackageUpdater](./03-api-reference.md#packageupdater) - 核心更新流程

**调试问题**
- [常见问题](./06-faq.md) - 故障排查
- [API 参考 - Fetcher](./03-api-reference.md#fetcher) - HTTP 请求调试

## 📂 项目结构概览

```
aur-packages/
├── .github/workflows/              # ⚙️ GitHub Actions
│   ├── keep-alive.yml              # 保持仓库活跃
│   ├── push-to-aur.yml             # 推送到 AUR
│   └── update-packages.yml         # 自动更新包
│
├── docs/                           # 📚 项目文档
│   ├── README.md                   # 文档索引（本文件）
│   ├── 01-quickstart.md            # 快速入门
│   ├── 02-architecture.md          # 架构设计
│   ├── 03-api-reference.md         # API 参考
│   ├── 04-development-guide.md     # 开发指南
│   ├── 05-configuration.md         # 配置文件说明
│   └── 06-faq.md                   # 常见问题
│
├── scripts/                        # 🔧 主要代码目录
│   ├── cli/                        # 命令行接口
│   ├── core/                       # 核心逻辑
│   ├── constants/                  # 常量定义
│   ├── fetcher/                    # 数据获取
│   ├── loaders/                    # 配置加载
│   ├── parsers/                    # 版本解析
│   ├── updater/                    # PKGBUILD 更新
│   ├── utils/                      # 工具函数
│   ├── tests/                      # 测试代码
│   ├── packages.yaml               # 包配置文件
│   └── main.py                     # 程序入口
│
├── packages/                       # 📦 AUR 包目录
│   ├── linuxqq-nt/                 # QQ Linux 包
│   └── navicat17-premium-zh-cn/    # Navicat 包
│
├── CONTRIBUTORS                    # 贡献者名单
├── CLAUDE.md                       # Claude Code 项目指引
└── README.md                       # 项目说明
```

## 🔗 相关资源

### 外部资源
- [Arch Linux 官方文档](https://wiki.archlinux.org/)
- [Arch User Repository (AUR)](https://aur.archlinux.org/)
- [PKGBUILD 示例](https://github.com/archlinux/svntogit-packages)
- [Python 3.13+ 文档](https://docs.python.org/3.13/)

### 项目依赖
- `httpx` - 异步 HTTP 客户端
- `pydantic` - 数据验证
- `pyyaml` - YAML 配置解析
- `pytest` - 测试框架
- `pytest-asyncio` - 异步测试支持

## 📝 文档贡献

文档是项目的重要组成部分，欢迎改进和完善：

1. **发现错误** - 提交 Issue 报告文档问题
2. **补充内容** - 提交 PR 添加新的文档章节
3. **改进说明** - 优化现有文档的表达和示例

### 文档编写规范
- 使用清晰的中文表达
- 提供代码示例和使用场景
- 保持与代码实现的一致性
- 及时更新以反映项目变化

## 📄 许可证

本项目的文档遵循项目的开源许可证。

---

**最后更新**: 2026-01-04
**版本**: 1.0.0
