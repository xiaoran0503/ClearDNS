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

## v2.0.1 (2026-09-22) — Docker Hub 自动构建 CI

### 新增

- 新增 `.github/workflows/docker-build.yml`：push master 自动构建并推送镜像至 Docker Hub（`xiaoran05032/cleardns:latest`），支持 `workflow_dispatch` 手动触发并附加指定 tag；
- Docker Hub 凭据通过仓库 Secrets（`DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`）注入，不进入代码库；
- 海外 runner 直连上游：`GH_MIRROR=` 空（GitHub 直连）、`GOPROXY=https://proxy.golang.org,direct`、`APT_MIRROR=deb.debian.org`；启用 `type=gha` 构建缓存加速增量构建。

### 修复

- checkout 改为 `fetch-depth: 0`：Dockerfile cleardns 阶段 `git describe --tags` 取版本号依赖完整历史与 tags，浅克隆会报 `Unable to get version information` 导致 CMake 配置失败。

### 验证

- GitHub Actions run 全步骤 success（Checkout / Docker Buildx / meta / Login / Build and push 全绿）；
- 从 Docker Hub 拉取 `xiaoran05032/cleardns:latest`（198MB）并启动冒烟通过：ClearDNS v2.0.0-5-g0e649aa / dnsproxy 0.84.2 / overture v2.0.9，五服务正常；国内组（阿里 DoH）、国外组（doh.ac0.top）、主入口 overture 分流解析均正常。
### 流程变更（用户拍板：全 CI 直连编译，本地不编译）

- **所有编译统一在 GitHub Actions 完成**（push master 自动构建），本地不再编译；
- **去掉全部针对国内网络的优化**：Dockerfile 移除 ghfast.top（`GH_MIRROR` 默认空）、rsproxy cargo 源、npmmirror npm 源、清华 pip/apt 源，全部直连官方上游（`GOPROXY=https://proxy.golang.org,direct` / 官方 crates.io / npmjs / PyPI / deb.debian.org）；
- `src/loader/default.c` 与 README 中 assets 下发地址恢复为直连 `raw.githubusercontent.com`；
- 本地测试流程：仅用 1ms registry mirror（docker.1ms.run）加速拉取 Docker Hub 编译产物 → 部署 → 冒烟测试 → 记录文档；
- 后续迭代默认遵循本流程，无需重复提醒。- 直连版构建验证（run 35704866039 全绿）：Docker Hub 拉取 `xiaoran05032/cleardns:latest`（198MB，17s 经 docker.1ms.run 加速）部署冒烟通过——ClearDNS v2.0.0-8-ge374fb2 / dnsproxy 0.84.2 / overture v2.0.9，五服务正常；国内组（阿里 DoH）、国外组（doh.ac0.top）、主入口 overture 分流解析全部正常。
## v2.0.2 (2026-09-22) — 代码审查问题修复（AI 评估处置）

根据代码审查报告（WorkBuddy 2026-09-22）逐项核实后修复以下真实问题：

### 修复（核实属实）

- **S2 信号标志类型**（`src/utils/process.c`）：`EXITED/EXITING` 由 `uint8_t` 改为 `volatile sig_atomic_t`，避免信号处理器与主循环共享标志的寄存器缓存与原子性问题（`while(!EXITED) pause()` 可能永远读不到更新）；
- **S3 子进程退出事件丢失**（`src/utils/process.c`）：SIGCHLD 处理器去掉 `return`，一次信号到达时扫描并重启全部已退出进程（此前多进程同时退出只重启第一个，其余静默死亡）；重启节流 `sleep(RESTART_DELAY)` 由单次改为整批一次；
- **N2 配置根节点未校验**（`src/loader/parser.c`）：`cleardns_parser` 增加 `cJSON_IsObject` 根节点校验，避免根为数组/标量时 `strcmp(NULL, ...)` 段错误；
- **N7 错误文案不符**（`src/loader/parser.c`）：`adguard`/`assets` 两处 `"must be array"` 改为 `"must be object"`（实际校验为 object）；
- **N5 system() 退出码解析**（`src/common/system.c`）：`/256` 改为标准 `WIFEXITED/WEXITSTATUS`，并处理 `system()` 返回 -1（fork 失败）的情况。

### 评估后不修复（附理由）

- **N1 AdGuardHome 明文密码日志**：用户指示不处理；debug 日志默认不输出；
- **S1 信号处理器调用非 async-signal-safe 函数**：完整修复需 self-pipe/signalfd 专项重构守护进程核心逻辑，改动风险高于收益；本次 S2/S3 精简已显著降低触发概率，专项重构留档后续评估；
- **N4 pgrep 杀全部 overture 实例**：容器隔离场景影响有限，且改动需跨模块传 PID，收益低；
- **N6 malloc 无 NULL 检查**：系统性补齐成本高，OOM 场景 log_fatal 已兜底多数路径；
- **N8 shell cat 追加文件**：参数均为编译期常量无注入风险；
- **O8 bin/ 与 src/target/ 混入仓库**：误报，`.gitignore` 已含 `/bin/`、`/src/target/`，未跟踪。

### 验证

- 代码改动经 GitHub Actions 全量构建（无国内优化直连版）；构建成功后按流程 1ms 拉取镜像部署冒烟测试。- v2.0.2 构建（run 35707091974 全绿）经 1ms 拉取部署冒烟通过：ClearDNS v2.0.0-10-g208e0f0 / dnsproxy 0.84.2 / overture v2.0.9；国内组（阿里 DoH）、国外组（doh.ac0.top）、主入口 overture 分流解析全部正常；**S3 修复实测**：`kill -9` overture 后 6 秒内自动重启（新 PID），重启后解析正常。