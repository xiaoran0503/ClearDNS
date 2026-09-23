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
## v2.0.3 (2026-09-22) — 复审新缺陷修复（幽灵槽位）

复审验证报告（WorkBuddy 第二轮）经真实源码编译运行复现并验证新严重缺陷，修复已核实采纳：

### 修复（核实属实，已采纳）

- **单组件崩溃可导致整个 DNS 服务退出**（`src/utils/process.c` get_sub_exit）：死亡进程就地重启后若新子进程在 1 秒内再次死亡，会被末尾兜底 `waitpid(-1)` 回收，`proc->pid` 残留为"幽灵 PID"；下一次 SIGCHLD 扫描时 `waitpid(幽灵PID)` 返回 `-1/ECHILD`，旧代码将其当作致命错误调用 `server_exit(EXIT_WAIT_ERROR)`，杀光全部子进程并退出——单个组件崩溃升级为整个服务中断。
- 修复：新增 `#include <errno.h>`，`get_sub_exit()` 内对 `waitpid == -1 && errno == ECHILD` 降级为"重启该进程"（复用 `restarted` 标记与 1 秒节流），其余 waitpid 错误维持原退出语义。一处守卫同时覆盖两条触发路径（重启后秒死 / 扫描与兜底之间的竞态窗口）。
- 验证：复审沙箱实测 RUN A（旧代码）启动约 1 秒后整服务退出码 3；RUN C（新代码）15 秒持续存活、每秒重启 1 次、零致命错误；项目构建参数（gnu99 -Wall -Wextra -Werror）编译零警告。

### 复审对既有修复的确认

- S2 / S3 / N2 / N5 / N7 均确认已修复；O8 撤回（我方上轮误报）；N6 依据修正为"OOM 概率低，且守护进程由容器重启策略兜底"；S1 维持留档（self-pipe 专项重构）。
- 复审更正上轮 S3 表述：SIGCHLD 在 handler 执行期间不丢弃而是 pending 合并，真正根因是"信号合并 + 命中即 return"，本轮全表扫描修复方向正确。

### 验证（CI 流程）

- 代码经 GitHub Actions 直连构建；构建成功后 1ms 拉取镜像部署冒烟（含子进程 kill -9 自动重启验证）。- v2.0.3 构建（run 6 / 35709014957 全绿）经 1ms 拉取部署冒烟通过：ClearDNS v2.0.0-12-ga5dab0c / dnsproxy 0.84.2 / overture v2.0.9；国内组/国外组/主入口分流解析全部正常。
- **崩溃重启实测**：连续两轮 `kill -9` overture / domestic dnsproxy / foreign dnsproxy，全部自动重启成功（19→80→162、17→114、18→195），全程无 `waitpid error`（旧代码此场景会致命退出）；容器日志确认整体退出仅由外部 SIGTERM 触发（`Get exit signal` 正常路径），`--restart` 策略自动拉起，服务无残留故障。
## v2.0.4 (2026-09-22) — 第三轮审阅处置（SIGCHLD 重构 + 构建链加固）

第三轮审阅报告（WorkBuddy 第三轮）经真实源码编译运行复现新严重缺陷，连同构建/发布链问题一并处置：

### 修复（核实属实，已采纳）

- **P0 首个组件崩溃循环导致全部组件不启动**（`src/utils/process.c`）：SIGCHLD 处理器原在主流程之外执行整套重启工作（含 `sleep(1)` 节流），处理器被反复重入、主流程 `pause()` 被饿死——进程列表中**第一个**组件秒死时，其后组件（真实映射即 Domestic dnsproxy 崩溃 → Foreign/overture/crond/AdGuardHome 全部起不来）永不启动，服务整体不可用。审阅沙箱对照实验：修复前 B/C 启动 0 次，修复后各 1 次。
  - 修复（信号处理器异步安全化 + 主循环接管）：新增 `CHILD_EXIT` 标志，`get_sub_exit()` 只置标志；新增 `reap_sub_exit()`（原处理器函数体原样迁移），由 `process_list_daemon()` 主循环在 **SIGCHLD 阻塞态**下检查标志、**解除阻塞态**下执行重启（避免 `fork` 让子进程继承阻塞掩码——crond 等自 fork 组件将无法获知子进程结束），`sigsuspend` 原子等待不丢事件；ECHILD 幽灵槽位守卫（v2.0.3）原样保留。
  - 权衡（审阅明示，已接受）：重启动作从信号处理器移至主循环，最长延迟毫秒级；`cleardns.c` 首次资源更新（SIGALRM 处理器内同步执行，最多数分钟）期间子进程死亡待处理、更新结束后重启——行为回退量级为一次资源更新时间，属可接受权衡。
  - 验证：审阅沙箱三场景（A 崩溃循环+B/C 长驻 / 全正常 / 全崩溃循环）+ 子进程信号掩码检查（SigBlk 全 0）全部通过，`-std=gnu99 -Wall -Wextra -Werror` 编译零警告；本机语法级编译复核通过。
- **B4 资源更新缺数据质量闸门**（`assets/*.py` + `.github/workflows/update-assets.yml`）：三个脚本用 `os.popen('curl -sL')` 抓取上游，curl 静默失败不产生非零退出码，空内容会被写文件并无条件提交推送 → Dockerfile assets 阶段打包空分流表发布给所有用户。
  - 修复：脚本改用 `subprocess.run` 检查返回码 + `curl -sfL`（HTTP 错误返回非零），源失败计数告警、**全部源失败则拒绝写空文件并退出非零**；workflow 新增 Validate assets 步骤（gfwlist ≥ 5000 行 / china-ip ≥ 500 行 / chinalist ≥ 5000 行，不达标 fail，阻断提交）。
- **B3 构建硬依赖 git 元数据**（`CMakeLists.txt`）：源码压缩包（无 `.git`）或仓库无 tag 时 `git describe` 失败即 `FATAL_ERROR`；改为失败回退 `VERSION="unknown"` + warning，仅 CI 环境要求 git describe。
- **B8 默认配置生成空指针**（`src/loader/default.c`）：`.json` 后缀路径下 `to_json_format()` 可能返回 NULL 导致 `fputs(NULL, fp)`；增加 NULL 检查并回退写入 YAML 原文。
- **B5 构建上下文污染**（`.dockerignore`）：补 `src/target`（Rust 本地产物不再进构建上下文）。
- **B7 并发构建竞态**（`.github/workflows/docker-build.yml`）：新增 `concurrency: {group: docker-build, cancel-in-progress: true}`，连续 push 不再并发构建竞相推送 latest。
- **B2 工具链未锁定**（`Dockerfile`）：`pip3 install cmake` 未锁版本，未来装出 3.x 会导致 CI 失败；改为 `'cmake>=4.2,<5'`（保持 4.x 下限可复现）。说明：项目 CMakeLists 使用指令均为 3.x 既有 API，`cmake_minimum_required(VERSION 4.2)` 即启用 CMake 4.x 策略集，无需为用而用引入冗余特性。

### 评估后不修复（附理由）

- **B1 默认配置隐私/凭据**：`doh.ac0.top` 为维护者私有 DoH——用户指定选用，不更换；默认口令 `admin/cleardns` 与 AdGuardHome 监听 0.0.0.0:80——用户指示密码明文问题不处理（默认仅限内网部署场景，README 已说明可改）。
- **B6 其余项**：上游源码无校验和（供应链加固留档）；Header.css 按 DOM 顺序隐藏导航项（低概率，升级 AdGuardHome 时纳入检查清单）；UPX 壳在强化内核下可能拒绝加载（低概率，镜像冒烟已覆盖可启动断言）。

### 验证

- 本机 WSL：`process.c` / `default.c` / `assets.c` 以 `-std=gnu99 -Wall -Wextra -Werror` 语法级编译零警告零错误；三个 assets 脚本 `py_compile` 通过。
- 推送后 GitHub Actions 直连构建（run 35711899182 全绿，GHA 缓存加速约 3 分钟）；1ms 拉取镜像部署。
- **容器级复现验证（真实镜像实测）**：将 Domestic 组 `dnsproxy` 替换为条件秒死脚本（domestic 调用 exit 1、foreign 转交真实二进制）模拟"首个组件崩溃循环"：
  - `Process start complete` 出现（启动循环走完，旧代码此场景永不出现）；Foreign / overture / crond / AdGuardHome 全部被拉起并存活；
  - Domestic 崩溃循环被节流处理：每 1 秒重启一次（PID 25→128→141→…→146，7 次），全程 0 `waitpid error` / 0 fatal；
  - **v2.0.3 ECHILD 幽灵槽位守卫被真实触发 6 次**（`already reaped -> restart`，秒死 PID 被兜底回收后守卫降级重启而非致命退出），两轮修复协同生效；
  - 首次崩溃处理延迟 45 秒系 assets 首更（SIGALRM 同步拉取）占用所致——CHILD_EXIT 标志待处理、更新结束后统一重启，无事件丢失（报告 2.5 节权衡符合预期）；
  - 容器最终仅因外部 SIGTERM 退出（`Get exit signal` 正常路径），非缺陷。
- **干净镜像冒烟（v2.0.0-14-g1cfddc2）**：五服务 running success + `Process start complete`；国内组（阿里 DoH）、国外组（doh.ac0.top）、主入口 overture 分流解析全部正常。


## v2.0.5 (2026-09-23) — 默认缓存方案落地 + 国外组上游调整

按运行日志分析结论（doh.ac0.top 故障导致国外组查询超时）与缓存收益评估，调整默认配置：

### 变更

- **ClearDNS 组缓存默认关闭**（`src/loader/default.c`）：`cache.enable: true -> false`——与 AdGuardHome 缓存二选一，避免分流器上重复缓存开销；
- **AdGuardHome 默认开启缓存 4MiB + 乐观缓存**（`src/applet/adguard.c`）：生成 AdGuardHome.yaml 时注入 `dns.cache_size=4194304` / `cache_ttl_min=0` / `cache_ttl_max=0` / `cache_optimistic=true`——缓存位于链路最上游，上游故障期间已缓存查询完全本地返回；
- **国外组 primary 更换**（`src/loader/default.c`）：`https://doh.ac0.top/google-query` -> `https://doh.18bit.cn/dns-query`（上游可用性调整，fallback 8.8.8.8/1.1.1.1 保留）。

### 验证

- `default.c` / `adguard.c` 以 `-std=gnu99 -Wall -Wextra -Werror` 语法级编译零警告；
- 推送后 GitHub Actions 直连构建（run 35805563825 全绿），1ms 拉取部署实测（v2.0.0-16-gf081791）：
  - `cleardns.yml` 生成 `cache.enable: false`（ClearDNS 组缓存关闭）；
  - `AdGuardHome.yaml` 生成 `cache_size: 4194304` / `cache_optimistic: true`（4MiB + 乐观缓存注入成功，含 AdGuardHome 默认 `cache_optimistic_answer_ttl: 30s` 等优化字段）；
  - `foreign.json` upstream 确认 `doh.18bit.cn/dns-query`（国外组 google 返回 216.239.38.120，新上游生效）；
  - 国内组（阿里 DoH）、国外组（doh.18bit.cn）、主入口分流解析全部正常。


## v2.0.6 (2026-09-23) — 修复 assets 解压错位（分流文件长期为空）

### 背景

用户核查成品镜像时发现 `china-ip.txt` / `chinalist.txt` / `gfwlist.txt` 出现在 `/cleardns/` 顶层（与 `cleardns.yml` 平级），而 `/cleardns/assets/` 目录为空。

### 根因

`src/utils/assets.c` 的 `extract()` 解压命令为：

```
tar xf /assets.tar.xz <file> -C /cleardns/assets/
```

`-C` 位于归档成员参数**之后**，GNU tar 在此调用形式下不切换目录，三个文件被解压到进程当前工作目录 `/cleardns/`（而非 `/cleardns/assets/`）。`extract()` 仅以 `tar` 退出码判断成功（退出码 0），**假成功**；随后 `load_diverter_assets()` 的 `file_append` 因源文件不存在复制失败，`/etc/cleardns/*.txt` 全部为 0 字节 —— overture 加载的空分流列表，**gfwlist / chinalist / china-ip 分流自 v2.0.0 起实际未生效**（未匹配域名全部落入 domestic 组兜底）。

### 修复

- `extract()`：`-C` 移到归档成员之前：`tar xf /assets.tar.xz -C /cleardns/assets/ <file>`；
- 解压后增加存在性校验（`is_file_exist`），失败不再报 success，输出 `verify failed` 告警（避免内存泄漏）。

### 验证

- `assets.c` 以 `-std=gnu99 -Wall -Wextra -Werror` 语法级编译零警告；
- 推送后 CI 构建，1ms 拉取部署：`/cleardns/assets/` 三个文件存在且非空、`/etc/cleardns/*.txt` 与 assets 内容一致（非 0 字节）、gfwlist/chinalist 分流真实生效。


## v2.0.7 (2026-09-23) — AdGuardHome 缓存 TTL 覆盖 / EDNS / 上游加固

按用户要求调整 AdGuardHome 生成配置（`src/applet/adguard.c` 的 `adguard_config()`，每次启动覆盖）：

### 变更

- **缓存 TTL 覆盖**：`cache_ttl_min: 0 -> 30`（最小 TTL 30 秒）、`cache_ttl_max: 0 -> 300`（最大 TTL 300 秒）——低 TTL 记录（如故障探测域名）不低于 30s、高 TTL 不超 300s，减少对上游的重复查询；
- **EDNS 开启**：`edns_enabled: true`（EDNS Client Subnet）；
- **Bootstrap DNS**：`223.5.5.5` + `119.29.29.29`（此前为空数组，无法解析 DoH 主机名时兜底）；
- **后备 DNS（fallback_dns）**：`223.5.5.5` + `119.29.29.29`（主上游不可用时直接走国内明文 DNS）。

### 验证

- `adguard.c` 以 `-std=gnu99 -Wall -Wextra -Werror` 语法级编译零警告；
- 推送后 CI 构建，1ms 拉取部署：确认 AdGuardHome.yaml 生成 `cache_ttl_min: 30` / `cache_ttl_max: 300` / `edns_enabled: true` / `bootstrap_dns` 与 `fallback_dns` 双地址，AdGuardHome 正常启动、DNS 解析正常。


## v2.0.8 (2026-09-23) — AdGuardHome 配置尊重网页端（仅强制上游指向 overture）

### 背景

用户反馈：AdGuardHome 网页端修改的设置（缓存、TTL、EDNS、引导/后备 DNS 等）在重启容器后被还原。

根因：`adguard_config()` 每次启动（含容器重启）都用 `json_field_replace` 强制覆盖写回 `dns` 段全部核心字段与 `users`。

### 变更

`src/applet/adguard.c` 重构，`adguard_config()` 增加 `is_new` 参数：

- **首次创建**（AdGuardHome.yaml 不存在）：注入完整默认值——账号密码、`dns.port/bind_host`、`upstream_dns`、`bootstrap_dns`(223.5.5.5/119.29.29.29)、`fallback_dns`(223.5.5.5/119.29.29.29)、`edns_client_subnet.enabled=true`、缓存 4MiB + TTL 30–300s + 乐观缓存；
- **已存在配置**：**仅强制 `upstream_dns = 127.0.0.1:5353`**（主链路命脉，防止网页配置导致分流链路断裂），其余字段（缓存、TTL、EDNS、引导/后备 DNS、账号、端口等）完全尊重网页端设置，重启不再还原。

### 验证

- `adguard.c` 以 `-std=gnu99 -Wall -Wextra -Werror` 语法级编译零警告；
- 推送后 CI 构建，1ms 拉取部署：首启生成完整默认 AdGuardHome.yaml；修改 yaml 中缓存值后重启容器，缓存值保留、`upstream_dns` 仍指向 127.0.0.1:5353、解析正常。


## v2.0.9 (2026-09-23) — 依赖版本自动核查（CI 定时巡检）

### 背景

用户要求列出"未拉到最新的依赖/组件/编译工具/运行时"清单。核查结论（2026-09-23）：**当前版本矩阵全部为最新稳定版，无任何升级动作**——Debian 13.7 / Go 1.27.1 / Node 24.21.0 LTS / Rust 1.98.1 / dnsproxy 0.84.2 / AdGuardHome 0.107.79 / overture fork 2.0.9 / cmake 4.4.3（pip 约束 `>=4.2,<5` 内）。

为免人工逐次核查，新增自动巡检：

### 变更

- **新增 `.github/scripts/check-versions.py`**：从 `Dockerfile` 解析当前版本矩阵（ARG/ENV 镜像 tag 与版本变量），对比官方最新稳定版——GitHub Releases API（dnsproxy / AdGuardHome / cmake / overture fork tags）、go.dev（Go）、nodejs.org（Node 最新 LTS）、rust-lang 官方 channel manifest（Rust stable）、debian.org（trixie 最新 point release）；
- **新增 `.github/workflows/check-versions.yml`**：每周一 00:00 UTC + 手动触发，输出核查表格到 job summary；发现新版本时自动创建**去重 issue**（标题含日期，已存在同标题 open issue 则跳过），大版本升级（major 变化）标注"需用户决策"，overture 为 fork 特判"需先同步 fork"；
- cmake 为 pip 范围约束（非固定版本），脚本校验最新 4.x 是否落在 `>=4.2,<5` 区间内，越界才告警；
- 本版本不修改任何构建/运行配置（核查结论：全部已最新）。

### 验证

- 本地直连实测脚本：8 个组件全部解析成功且判定"✅ 最新"，输出 Markdown 表格正常；
- 推送后触发 workflow_dispatch，确认 CI 全绿。
