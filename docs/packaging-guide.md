# AUR 打包实践指南

本文档面向本项目中的 AUR 包维护，分为三个层级：

- **[官方规范]**：Arch Wiki / AUR 要求，必须遵守
- **[推荐实践]**：经过验证的最佳做法，建议遵守
- **[项目约定]**：本项目内部约定，保持一致性

通用 Arch 打包规范请参考 [Arch Wiki - Creating packages](https://wiki.archlinux.org/title/Creating_packages)。

---

## 版本 [官方规范]

### pkgver

- 应与上游发布的版本号一致
- 可包含字母、数字、点和下划线，**不允许连字符**（`-`），需替换为下划线（`_`）
- 上游使用时间戳版本时，使用 ISO 8601 倒序格式（如 `20141030` 而非 `30102014`）
- 可通过 `vercmp` 工具验证版本排序

### pkgrel

- 修改 `source`、`depends`、`package()` 等影响打包输出的字段时，必须递增 `pkgrel`
- 修改 `pkgver` 时，`pkgrel` 重置为 `1`

### epoch

- 用于强制将包视为比任何具有较低 epoch 的版本更新，值为非负整数，默认为 `0`
- 仅在版本号方案变更导致正常版本比较失效时使用
- 除非绝对必要，不应使用

## .SRCINFO [官方规范]

AUR 提交必须包含 `.SRCINFO`，且与 PKGBUILD 保持同步：

```bash
makepkg --printsrcinfo > .SRCINFO
```

## license [官方规范]

- Arch Linux 使用 SPDX 许可证标识符（如 `MIT`、`Apache-2.0`、`GPL-3.0-or-later`）
- BSD、MIT 等许可族使用 SPDX 标识符（如 `BSD-3-Clause`），但需提供对应的许可证文件
- 非标准许可证使用 `LicenseRef-license-name` 或 `custom:license-name` 格式
- 组合许可证遵循 SPDX 语法（如 `'Apache-2.0 WITH LLVM-exception'`），必须为单引号包裹的单个字符串

安装到 `/usr/share/licenses/${pkgname}/`：

```bash
install -Dm644 "LICENSE.txt" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
```

## 依赖 [官方规范]

| 字段 | 用途 |
|------|------|
| `depends` | 运行时依赖 |
| `makedepends` | 构建时依赖 |
| `checkdepends` | 测试时依赖 |
| `optdepends` | 可选功能依赖，应附简短说明 |

关键规则：

- `depends` 应列出所有直接依赖，即使某些已被其他依赖传递引入
- `makedepends` 中 `base-devel` 视为已安装，不要包含其子包
- `depends` 不应重复出现在 `makedepends` 中（`depends` 隐含在构建时也需要）
- 可指定版本约束：`depends=('foobar>=1.8.0')`，需要多个约束时重复声明
- 若依赖名为库文件（如 `libfoobar.so`），makepkg 会自动检测并附加 soname 版本

依赖确认方式：

- 通过 `ldd`、`namcap`（或 `find-libdeps`）检查二进制实际依赖
- 只声明**实际依赖**的系统库，不基于框架理论推断

## 函数职责 [官方规范]

| 函数 | 职责 |
|------|------|
| `prepare()` | 补丁、预处理 |
| `build()` | 编译 |
| `check()` | 测试 |
| `package()` | 安装文件到 `${pkgdir}` |

预编译二进制包通常省略 `build()` 和 `check()`，只在 `prepare()` 中解包，`package()` 中安装。

`package()` 在 fakeroot 环境中运行，`chmod 4755` 等权限操作只影响 `${pkgdir}` 内的元数据，不会修改宿主机文件。

## 校验和 [官方规范]

- 优先使用 `sha256sums` 或 `b2sums`
- 不使用 `SKIP`，除非源文件动态变化无法固定（如 VCS 源）

## 代码质量 [推荐实践]

提交前使用 namcap 检查：

```bash
namcap PKGBUILD
namcap *.pkg.tar.zst
```

可检测缺失/多余依赖、不规范文件路径等问题。

## 文件操作 [推荐实践]

批量复制使用 `cp -a`（保留权限、时间戳、符号链接）：

```bash
cp -a "${srcdir}/app/." "${pkgdir}/opt/${pkgname}/"
```

安装单个文件使用 `install`（显式设定权限）：

```bash
install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
install -Dm644 "${srcdir}/app.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
```

## source 声明 [推荐实践]

`source` 数组中的文件名必须唯一（`SRCDEST` 目录所有包共享）。若上游 URL 中的文件名可能冲突，使用 `::` 语法重命名：

```bash
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/user/repo/archive/v${pkgver}.tar.gz")
```

- `.install` 文件由 makepkg 自动识别，不应加入 `source` 数组
- `.sig`、`.sign`、`.asc` 后缀的文件被自动识别为 PGP 签名
- 架构特定的源使用 `source_x86_64=()` 等后缀，需对应 `sha256sums_x86_64=()` 等校验和数组

## 图标安装 [推荐实践]

推荐使用 XDG hicolor 图标目录，而非传统的 `/usr/share/pixmaps/`：

```bash
install -Dm644 "icon.png" "${pkgdir}/usr/share/icons/hicolor/512x512/apps/${pkgname}.png"
```

`.desktop` 文件中 `Icon=` 字段只写包名，系统通过 hicolor 主题自动查找：

```ini
Icon=trae
```

## provides 和 conflicts [推荐实践]

- `provides`：仅在包名与提供的虚拟包不同时声明；不要将 `pkgname` 加入，makepkg 自动处理
- `provides` 应附带版本号（如 `provides=('trae=2.3.25938')`），以便依赖特定版本的包正确解析
- `conflicts`：声明文件冲突或功能冲突的包
- 通过 `provides` 提供相同功能的包互为隐式冲突，无需在 `conflicts` 中逐一列举所有变体

```bash
# trae（主包，pkgname = trae，provides 自动包含）
conflicts=('trae-bin')

# trae-sg（变体包）
provides=('trae')
conflicts=('trae-bin')
# 无需 conflicts=('trae' 'trae-us')，三者均 provides=('trae')，隐式互斥
```

---

## Electron 直装（tarball）

解压 tarball 后直接复制到 `/opt/`。

### source 文件排除 [项目约定]

makepkg 将 `source=()` 中的本地文件以符号链接形式放入 `${srcdir}/`，与 tarball 解压内容混合。推荐按文件名显式排除，不依赖符号链接检测：

```bash
for f in "${srcdir}"/*; do
    case "${f##*/}" in launcher.sh|app.desktop) continue ;; esac
    cp -a "$f" "${pkgdir}/opt/${pkgname}/"
done
```

### SUID sandbox [项目约定]

部分 Electron/Chromium 发行版需要为 `chrome-sandbox` 设置 SUID 位：

```bash
chmod 4755 "${pkgdir}/opt/${pkgname}/chrome-sandbox"
```

即使 `cp -a` 保留了原始权限，仍显式设置作为防御性措施。现代 Chromium/Electron 可能使用 user namespace sandbox 替代 SUID。

### 构建选项 [项目约定]

Electron 预编译二进制包使用 `!strip` 避免破坏符号表：

```bash
options=('!strip' '!debug')
```

### 启动脚本 [项目约定]

支持用户通过配置文件传递自定义参数：

```bash
#!/bin/bash
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
if [[ -f "${XDG_CONFIG_HOME}/${pkgname}-flags.conf" ]]; then
    mapfile -t USER_FLAGS <<<"$(grep -v '^#' "${XDG_CONFIG_HOME}/${pkgname}-flags.conf")"
fi
exec /opt/${pkgname}/${binary} "${USER_FLAGS[@]}" "$@"
```

注意：参数展开中使用 `$HOME` 而非 `~`，因为 `~` 在引号内不会被展开。

### 完整示例

```bash
package() {
    install -d "${pkgdir}/opt/${pkgname}"

    for f in "${srcdir}"/*; do
        case "${f##*/}" in launcher.sh|app.desktop) continue ;; esac
        cp -a "$f" "${pkgdir}/opt/${pkgname}/"
    done

    chmod 4755 "${pkgdir}/opt/${pkgname}/chrome-sandbox"

    install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
    install -Dm644 "${srcdir}/app.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    install -Dm644 "${pkgdir}/opt/${pkgname}/resources/app/resources/linux/code.png" \
        "${pkgdir}/usr/share/icons/hicolor/512x512/apps/${pkgname}.png"
}
```

---

## deb 解包

使用 `bsdtar` 解包 deb 中的 `data.tar.xz`（或 `data.tar.gz`）到 `${pkgdir}/`，然后修正路径和清理冲突文件。

deb 文件是 ar 归档，makepkg 的 `bsdtar` 能直接处理（自动提取内层 data.tar.*）。`source` 声明示例：

```bash
source=("launcher.sh" "app.desktop")
source_x86_64=("https://example.com/${pkgname}_${pkgver}_amd64.deb")
source_aarch64=("https://example.com/${pkgname}_${pkgver}_arm64.deb")
```

### 内部结构 [推荐实践]

deb 包通常包含以下结构：

```
data.tar.xz
├── opt/<vendor>/              # 主程序（直接解压到目标位置）
├── usr/bin/                   # 启动脚本
├── usr/share/applications/    # .desktop 文件
└── usr/share/icons/           # 图标
```

`bsdtar -xf` 会将其中所有内容解压到 `${pkgdir}/`。Arch 官方规范要求文件不安装到 `/bin`、`/sbin` 等已合并目录，也不安装到 `/usr/local/`。deb 的 Debian 路径约定可能与 Arch 不一致（如 `/usr/lib/<package>/` vs `/usr/lib/`），解包后需要逐一检查。

### 解包与清理 [推荐实践]

```bash
package() {
    bsdtar -xf data.tar.xz -C "${pkgdir}/"

    # 修正 .desktop 文件中的路径和图标引用
    sed -i "s|Exec=.*|Exec=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    sed -i "s|Icon=.*|Icon=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"

    # 移除上游自带的启动脚本，使用自定义 launcher
    rm -f "${pkgdir}/usr/bin/${pkgname}"
    install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"

    # 移除冲突的捆绑库
    rm -fv "${pkgdir}/opt/${pkgname}/lib/conflicting-lib.so"

    # 安装许可证
    install -Dm644 "${pkgdir}/opt/${pkgname}/LICENSE" \
        "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
```

### 捆绑库处理 [推荐实践]

deb 包常自带系统库的私有版本，可能与 Arch 系统库冲突。处理原则：

- 使用 `ldd` 和 `namcap`（或 `find-libdeps`）检查二进制实际依赖
- 与系统库版本冲突时，移除捆绑版本（如 `libssh2.so`、`libvips-cpp.so`）
- 仅在捆绑库是上游特有修改版本（非系统库的简单副本）时保留
- 移除前验证程序能正常启动

---

## AppImage 解包

在 `prepare()` 中使用 `--appimage-extract` 解包 squashfs，在 `package()` 中复制到 `/opt/`。

### 解包流程 [推荐实践]

```bash
prepare() {
    cd "${srcdir}/" && rm -rf "squashfs-root"
    chmod +x "${srcdir}/${_pkgname}.AppImage"
    "${srcdir}/${_pkgname}.AppImage" --appimage-extract
}

package() {
    install -d "${pkgdir}/opt/${_pkgname}"
    cp -a "${srcdir}/squashfs-root/." "${pkgdir}/opt/${_pkgname}/"

    ln -s "/opt/${_pkgname}/AppRun" "${pkgdir}/usr/bin/${pkgname}"

    install -Dm644 "${srcdir}/squashfs-root/usr/share/icons/hicolor/256x256/apps/app-icon.png" \
        "${pkgdir}/usr/share/icons/hicolor/256x256/apps/${pkgname}.png"

    install -Dm644 "${srcdir}/squashfs-root/app.desktop" \
        "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    sed -i "s|Exec=.*|Exec=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    sed -i "s|Icon=.*|Icon=${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
}
```

### AppRun 启动问题 [推荐实践]

`AppRun` 可能依赖特定工作目录或环境变量。符号链接方式启动失败时，改用 wrapper script：

```bash
install -Dm755 "${srcdir}/launcher.sh" "${pkgdir}/usr/bin/${pkgname}"
```

wrapper script 中 `cd` 到 `/opt/${pkgname}/` 或设置必要环境变量后再执行 `AppRun`。

### 捆绑库冲突与 LD_PRELOAD [推荐实践]

AppImage 自带完整的运行时库，其中的某些库（如 `libsystemd.so`）可能与系统版本冲突，导致启动失败。解决方式：

- **方案一（推荐）**：移除冲突的捆绑库，让程序使用系统版本
- **方案二**：在 .desktop 的 `Exec=` 中添加 `env LD_PRELOAD=/usr/lib/libsystemd.so.0` 强制使用系统库

方案二适用于无法安全移除捆绑库的情况。修改后应验证补丁是否生效：

```bash
sed -i "s#Exec=${pkgname}#Exec=env LD_PRELOAD=\"/usr/lib/libsystemd.so.0\" ${pkgname}#"

if ! grep -q "LD_PRELOAD" "${pkgdir}/usr/share/applications/${pkgname}.desktop"; then
    error "LD_PRELOAD patch failed"
    return 1
fi
```

---

## 源码编译

从源码编译安装，使用完整的 `prepare()` → `build()` → `check()` → `package()` 四阶段流程。

### 构建流程 [官方规范]

源码编译包与预编译包的核心区别：需要 `build()` 编译，通常包含 `check()` 测试，且需要声明 `makedepends` 和 `checkdepends`：

```bash
makedepends=('cmake' 'ninja')
checkdepends=('gtest')

prepare() {
    # 应用补丁等预处理
}

build() {
    # 编译
}

check() {
    # 运行测试
}

package() {
    # 安装到 pkgdir
}
```

各构建系统（Make/CMake/Meson/Go/Rust）的具体用法参考 [Arch Wiki](https://wiki.archlinux.org/title/Arch_package_guidelines)。

### 构建标志 [推荐实践]

`/etc/makepkg.conf` 提供标准构建标志（`CFLAGS`、`CXXFLAGS`、`LDFLAGS` 等），构建系统会自动读取。不应在 PKGBUILD 中硬编码编译优化参数。

安装时统一使用 `DESTDIR="${pkgdir}"`。

### strip 与 debug 包 [推荐实践]

源码编译的 ELF 二进制 strip 通常正常工作（与 Electron 预编译包不同），默认不需要 `!strip`。如需保留调试符号使用 `options=('!strip')`。

### VCS 包 [推荐实践]

从 Git/SVN 等版本控制系统直接构建时：

- `source` 使用 `git+https://...` 格式
- 必须实现 `pkgver()` 函数动态生成版本号
- 校验和使用 `SKIP`

```bash
pkgver() {
    cd "${srcdir}/${pkgname}"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

source=("${pkgname}::git+https://github.com/user/repo.git")
sha256sums=('SKIP')
```
