# AUR 包故障排查记录

记录各包在 Arch Linux 上遇到的运行时/构建问题及解决方案，供维护参考。

---

## Trae 系列（trae / trae-sg / trae-us / trae-cn）

### ckg 项目索引功能失效

**现象**：项目索引（Code Knowledge Graph）不工作，日志显示 ckg 进程反复崩溃：

```
[ICubeProcessManager] ckg process exit with code 256, description: , restarting...
[ICubeProcessManager] ckg process health check failed: Error: connect ECONNREFUSED 127.0.0.1:51000
```

**根因**：`resources/app/modules/ckg/binary/` 捆绑了 Ubuntu 编译的 GCC 运行时库：

| 文件 | 来源 |
|------|------|
| `libstdc++.so.6` | Ubuntu GCC C++ 标准库 |
| `libgcc_s.so.1` | Ubuntu GCC 基础运行时 |

ckg 启动时通过 `start.sh` 设置 `LD_LIBRARY_PATH` 优先加载这些捆绑库。但：

1. 捆绑的 `libstdc++.so.6`（旧版 GLIBCXX）覆盖了系统版本
2. ckg 间接依赖的 Arch 系统库需要新版 GLIBCXX 符号
3. 同一进程只能加载一个 `libstdc++.so.6`，符号查找失败 → 进程崩溃

**解决方案**：在 `package()` 中删除捆绑的 GCC 运行时库：

```bash
rm -fv "${pkgdir}/opt/trae/resources/app/modules/ckg/binary/libstdc++.so.6"
rm -fv "${pkgdir}/opt/trae/resources/app/modules/ckg/binary/libgcc_s.so.1"
```

删除后 ckg 回退使用系统 `gcc-libs`（Arch 的 `libstdc++.so.6` 包含所有旧版符号，向后兼容）。

**保留的捆绑库**（应用级，非运行时，可能是上游定制构建）：

- `libckg.so` — ckg 主程序
- `libzmq.so.5` — ZeroMQ
- `libsodium.so.18` — 加密库
- `libpgm-5.2.so.0` — PGM 协议

**影响版本**：所有 trae 系列（trae、trae-sg、trae-us、trae-cn）

---

### makepkg 缓存冲突

**现象**：上游下载 URL 文件名不含版本号（如 `Trae-linux-x64.tar.gz`），makepkg 在 `SRCDEST` 中缓存旧文件，版本更新后校验和不匹配。

**解决方案**：使用 `::` 别名为文件名添加 `${pkgver}-${pkgrel}`：

```bash
source_x86_64=("Trae-linux-x64-${pkgver}-${pkgrel}.tar.gz::https://...")
```

**判断标准**：从 URL 提取文件名，若不含版本号则必须添加别名。

**影响版本**：所有 trae 系列

---

## 通用

### 修改本地源文件后 hash 不匹配

**现象**：修改 `.sh`、`.desktop`、`.install` 等本地源文件后，makepkg 构建失败：`FAILED` 校验和不匹配。

**根因**：本地文件列入 `source=()` 数组，makepkg 会校验其哈希。修改内容但未更新 PKGBUILD 中的 `sha512sums`。

**解决方案**：修改本地源文件后，重新计算并更新对应 hash：

```bash
sha512sum packages/trae/trae.sh
# 将输出更新到 PKGBUILD 的 sha512sums 数组
```

**影响版本**：所有包
