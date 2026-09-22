# =====================================================================
# ClearDNS 构建链（v2.x 维护线，AI 接手维护）
# - 全流程 Debian（trixie-slim 13.7），不再使用 Alpine
# - 上游依赖与 SDK 同步至最新稳定版
# - 所有 GitHub 拉取统一走 GH_MIRROR 加速（默认 https://ghfast.top/）
# - 容器内包管理走国内镜像：apt=清华 / npm=npmmirror / cargo=rsproxy / pip=清华
# =====================================================================

ARG DEBIAN="debian:13.7-slim"
ARG NODE="node:24.21.0-trixie"
ARG RUST="rust:1.98.1-trixie"
ARG GOLANG="golang:1.27.1-trixie"
ARG GH_MIRROR="https://ghfast.top/"
ARG GOPROXY="https://goproxy.cn,direct"
ARG APT_MIRROR="mirrors.tuna.tsinghua.edu.cn"

# ---------------- dnsproxy (0.84.2) ----------------
FROM ${GOLANG} AS dnsproxy
ARG GH_MIRROR
ARG GOPROXY
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
ENV DNSPROXY="0.84.2"
ENV GOPROXY="${GOPROXY}"
WORKDIR /
RUN wget ${GH_MIRROR}https://github.com/AdguardTeam/dnsproxy/archive/v${DNSPROXY}.tar.gz -O- | tar xz
WORKDIR /dnsproxy-${DNSPROXY}/
RUN go mod download
RUN env CGO_ENABLED=0 go build -v -trimpath -ldflags "-X github.com/AdguardTeam/golibs/version.version=${DNSPROXY} -s -w"
RUN mv dnsproxy /tmp/

# ---------------- overture (fork v2.0.9) ----------------
FROM ${GOLANG} AS overture
ARG GH_MIRROR
ARG GOPROXY
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
ENV OVERTURE="2.0.9"
ENV GOPROXY="${GOPROXY}"
WORKDIR /
RUN wget ${GH_MIRROR}https://github.com/xiaoran0503/overture/archive/v${OVERTURE}.tar.gz -O- | tar xz
WORKDIR /overture-${OVERTURE}/
RUN go mod download
RUN env CGO_ENABLED=0 go build -v -trimpath -ldflags "-X main.version=v${OVERTURE} -s -w" -o overture ./main
RUN mv overture /tmp/overture

# ---------------- AdGuardHome 源码 (0.107.79) ----------------
FROM ${DEBIAN} AS adguard-src
ARG GH_MIRROR
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
ENV ADGUARD="0.107.79"
RUN git clone ${GH_MIRROR}https://github.com/AdguardTeam/AdGuardHome.git -b v${ADGUARD} --depth=1

# ---------------- AdGuardHome 前端资源 ----------------
FROM ${NODE} AS adguard-web
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
ENV npm_config_registry="https://registry.npmmirror.com"
RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*
COPY --from=adguard-src /AdGuardHome/ /AdGuardHome/
WORKDIR /AdGuardHome/
RUN echo '.nav-item .order-4 {display: none;}' >> ./client/src/components/Header/Header.css
RUN make js-deps
RUN make js-build
RUN mv ./build/static/ /tmp/

# ---------------- AdGuardHome 主程序 ----------------
FROM ${GOLANG} AS adguard
ARG GOPROXY
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
ENV GOPROXY="${GOPROXY}"
RUN apt-get update && apt-get install -y --no-install-recommends git make ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=adguard-src /AdGuardHome/ /AdGuardHome/
WORKDIR /AdGuardHome/
RUN go mod download
COPY --from=adguard-web /tmp/static/ ./build/static/
RUN make CHANNEL="release" VERBOSE=1 GOTOOLCHAIN=local GOPROXY="${GOPROXY}" go-build
RUN mv AdGuardHome /tmp/

# ---------------- Rust 静态库 (assets / to-json) ----------------
FROM ${RUST} AS rust-mods
RUN mkdir -p "$CARGO_HOME" && cat > "$CARGO_HOME/config.toml" <<'EOF'
[source.crates-io]
replace-with = 'rsproxy-sparse'
[source.rsproxy-sparse]
registry = 'sparse+https://rsproxy.cn/index/'
[net]
git-fetch-with-cli = true
EOF
COPY ./src/ /cleardns/
WORKDIR /cleardns/
RUN cargo fetch
RUN cargo build --release
RUN mv ./target/release/*.a /tmp/

# ---------------- ClearDNS 主程序（动态链接 glibc，cmake 最新稳定版） ----------------
FROM ${DEBIAN} AS cleardns
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev git make ca-certificates python3-pip && \
    pip3 install --no-cache-dir --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple cmake && \
    rm -rf /var/lib/apt/lists/*
COPY ./ /cleardns/
COPY --from=rust-mods /tmp/libassets.a /cleardns/src/target/release/
COPY --from=rust-mods /tmp/libto_json.a /cleardns/src/target/release/
WORKDIR /cleardns/bin/
RUN cmake .. && make && strip cleardns
RUN mv cleardns /tmp/

# ---------------- 分流资源文件（仓库自动维护，走 GH_MIRROR） ----------------
FROM ${DEBIAN} AS assets
ARG GH_MIRROR
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates xz-utils && rm -rf /var/lib/apt/lists/*
RUN wget ${GH_MIRROR}https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/gfwlist.txt.xz
RUN wget ${GH_MIRROR}https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/china-ip.txt.xz
RUN wget ${GH_MIRROR}https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/chinalist.txt.xz
RUN xz -d *.xz && tar cJf /tmp/assets.tar.xz gfwlist.txt china-ip.txt chinalist.txt

# ---------------- release 打包 + UPX 压缩 ----------------
FROM ${DEBIAN} AS release
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends upx-ucl xz-utils && rm -rf /var/lib/apt/lists/*
COPY --from=assets /tmp/assets.tar.xz /release/
COPY --from=cleardns /tmp/cleardns /release/usr/bin/
COPY --from=dnsproxy /tmp/dnsproxy /release/usr/bin/
COPY --from=overture /tmp/overture /release/usr/bin/
COPY --from=adguard /tmp/AdGuardHome /release/usr/bin/
WORKDIR /release/usr/bin/
RUN for f in cleardns dnsproxy overture AdGuardHome; do upx -9 "$f" 2>/dev/null || echo "skip upx: $f"; done

# ---------------- 最终运行时（Debian trixie-slim） ----------------
FROM ${DEBIAN}
ARG APT_MIRROR
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates cron procps findutils xz-utils && rm -rf /var/lib/apt/lists/*
RUN ln -sf /usr/sbin/cron /usr/sbin/crond
COPY --from=release /release/ /
WORKDIR /cleardns/
ENTRYPOINT ["cleardns"]
