# Changelog

> 本仓库自 v2.0.0 起由 **AI 接手维护**（原维护者 dnomd343，仓库由用户 xiaoran0503 接管）。
> 迭代记录统一在此维护，构建链与依赖版本变更均需登记。

## v2.0.0 (2026-09-22) — AI 接手首个版本

由 AI 接手维护的首个版本，完成构建链与依赖全面升级：

### 上游依赖同步（最新稳定版）

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| dnsproxy | v0.84.2 | 版本注入机制迁移至 `github.com/AdguardTeam/golibs/version`（`-X ...version=...`） |
| AdGuardHome | v0.107.79 | 0.108 仍为 beta，未升级（大版本由用户决策） |
| overture | v2.0.9 | 自有 fork（另一会话维护，MIGRATION.md 已校验适配） |

### SDK / 基础镜像升级

| SDK | 版本 | 说明 |
| --- | --- | --- |
| Debian base | 13.7-trixie-slim | 全部阶段弃用 Alpine，改用最新 Debian（含最终运行时） |
| Go | 1.27.1-trixie | 最新稳定版 |
| Node | 24.21.0-trixie | 最新 LTS（Krypton） |
| Rust | 1.98.1-trixie | 最新稳定版 |

### 构建链改造

- Dockerfile 全阶段 Debian 化，移除 `musl-dev` / `-static`，ClearDNS 主程序改为动态链接 glibc；
- Rust 静态库链接补充 `pthread dl m`；
- dnsproxy 版本注入适配新版 golibs/version 包；
- overture 构建适配 fork 新版结构（`go build -o overture ./main`）；
- 所有 GitHub 拉取地址统一走 `GH_MIRROR` 环境变量（默认 `https://ghfast.top/` 加速），支持 `--build-arg GH_MIRROR=` 覆盖；
- 运行时 crond 适配 Debian（cron 包 + 符号链接），补齐 `procps`（pgrep）与 `findutils`（xargs）依赖。

### 资源文件（assets）自动化

- 新增 `.github/workflows/update-assets.yml`：每日 04:00 自动拉取上游数据，生成 `gfwlist.txt` / `china-ip.txt` / `chinalist.txt`（含 `.xz` 压缩版），自动提交回本仓库；
- Dockerfile 构建期与运行时默认配置均改为从本仓库 `assets/` 拉取资源；
- `.gitignore` 放行三个生成的 txt 文件。

### 文档

- README 同步资源下发地址（自有仓库 + ghfast.top 镜像）；
- 本 Changelog 建立，后续迭代持续登记。

### 构建链补充优化（本版本内落地）

- 修复 golang 官方镜像默认 WORKDIR 为 `/go` 导致源码解压目录错位的问题（各阶段显式 `WORKDIR /` 后再解压）；
- ARG 作用域修复：`GH_MIRROR` / `GOPROXY` / `APT_MIRROR` 在各 FROM 阶段内重新声明，构建参数正确生效；
- 容器内包管理走国内镜像：apt=清华 TUNA（`APT_MIRROR` 可覆盖）、npm=npmmirror、cargo=rsproxy（`.cargo/config.toml`）、pip=清华 pypi；
- AdGuardHome 构建以 `GOTOOLCHAIN=local` 使用镜像内 Go 1.27.1（官方 Makefile 写死 go1.26.6 会去 proxy.golang.org 下载 toolchain，国内超时）；
- ClearDNS 阶段补齐 `libc6-dev`（gcc 编译需 glibc 开发包）；
- `cmake_minimum_required` 全部升级至最新稳定版 4.2（构建环境为 pip 安装的最新 CMake / WSL 4.2.3）；
- 新增 `.dockerignore` 排除本地 `bin/` 构建产物，避免 CMakeCache 路径污染容器构建；
- Docker 镜像完整构建验证通过：cleardns v2.0.0-1-gb0e3e08 / dnsproxy 0.84.2 / overture v2.0.9 / AdGuardHome v0.107.79，最终运行时 Debian 13 (trixie)，UPX 压缩后四件套齐备；镜像内冒烟测试 DNS 服务正常起停、assets 三列表加载成功。
