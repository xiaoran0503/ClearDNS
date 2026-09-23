#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClearDNS 依赖版本自动核查
- 从 Dockerfile 解析当前版本矩阵
- 对比官方最新稳定版（GitHub API / 官方源）
- 有新版本时输出差异并（在 CI 且配置了 GH_TOKEN 时）创建去重 issue
- 大版本升级（major 变化）会明确标注"需用户决策"；overture 为 fork 特判

用法:
  python3 check-versions.py [--repo <repo-root>]
  环境变量: GH_TOKEN (可选，GitHub API 认证 + 创建 issue)
"""
import json
import os
import re
import sys
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GH_TOKEN", "")

UA = "ClearDNS-version-check/1.0"


def http_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def gh_api(path, payload=None):
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    url = f"https://api.github.com{path}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"User-Agent": UA, **headers}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    return http_json(url, headers)


def ver_tuple(v):
    return tuple(int(x) for x in re.split(r"[^0-9]+", v) if x)


def major(v):
    return ver_tuple(v)[0] if ver_tuple(v) else 0


def parse_dockerfile(path):
    """从 Dockerfile 解析当前版本矩阵"""
    with open(path, encoding="utf-8") as f:
        txt = f.read()

    def grab(pattern):
        m = re.search(pattern, txt)
        return m.group(1) if m else None

    return {
        "debian": grab(r'ARG DEBIAN="debian:([0-9.]+)-slim"'),
        "node": grab(r'ARG NODE="node:([0-9.]+)-'),
        "rust": grab(r'ARG RUST="rust:([0-9.]+)-'),
        "golang": grab(r'ARG GOLANG="golang:([0-9.]+)-'),
        "dnsproxy": grab(r'ENV DNSPROXY="([0-9.]+)"'),
        "overture": grab(r'ENV OVERTURE="([0-9.]+)"'),
        "adguard": grab(r'ENV ADGUARD="([0-9.]+)"'),
        "cmake_bound": (lambda m: (m.group(1), m.group(2)) if m else None)(
            re.search(r"cmake>=([0-9.]+),<([0-9.]+)", txt)),
    }


def latest_versions():
    """查询各组件官方最新稳定版"""
    out = {}

    r = gh_api("/repos/AdguardTeam/dnsproxy/releases/latest")
    out["dnsproxy"] = r["tag_name"].lstrip("v")

    r = gh_api("/repos/AdguardTeam/AdGuardHome/releases/latest")
    out["adguard"] = r["tag_name"].lstrip("v")

    # overture: fork 仓库按 tag 发布（无 release 对象），tags 第一个即最新
    r = gh_api("/repos/xiaoran0503/overture/tags")
    out["overture"] = r[0]["name"].lstrip("v")

    r = http_json("https://go.dev/dl/?mode=json")
    out["golang"] = r[0]["version"].lstrip("go")

    # node: 取最新 LTS（生产基准），跳过 Current
    r = http_json("https://nodejs.org/dist/index.json")
    out["node"] = next(v["version"].lstrip("v") for v in r if v.get("lts"))

    # rust: 官方 stable channel manifest（[pkg.rust] 段的版本，可能带 commit 后缀）
    r = http_text("https://static.rust-lang.org/dist/channel-rust-stable.toml")
    m = re.search(r'\[pkg\.rust\]\s*version = "([0-9.]+)', r)
    out["rust"] = m.group(1) if m else "?"

    r = gh_api("/repos/Kitware/CMake/releases/latest")
    out["cmake"] = r["tag_name"].lstrip("v")

    # debian trixie 最新 point release（取页面上最大版本号）
    r = http_text("https://www.debian.org/releases/trixie/")
    pts = [int(x) for x in re.findall(r"Debian 13\.(\d+)", r)]
    out["debian"] = f"13.{max(pts)}" if pts else "?"

    return out


def build_report(cur, latest):
    """生成差异报告。返回 (rows, outdated)"""
    names = {
        "debian": "Debian 基础镜像",
        "golang": "Go SDK",
        "node": "Node SDK (LTS)",
        "rust": "Rust SDK",
        "dnsproxy": "dnsproxy",
        "adguard": "AdGuardHome",
        "overture": "overture (fork)",
        "cmake": "cmake (pip 约束)",
    }
    rows = []
    outdated = []

    for key, label in names.items():
        cur_v = cur.get(key)
        lat_v = latest.get(key)
        if key == "cmake":
            bound = cur.get("cmake_bound") or ("4.2", "5")
            lo, hi = bound[0], bound[1]
            cv = ver_tuple(lat_v or "")
            ok = cv and (ver_tuple(lo) <= cv < ver_tuple(hi))
            status = "✅ 约束内" if ok else "🔴 约束失效，需修改 Dockerfile"
            rows.append((label, f">={lo},<{hi}", lat_v, status))
            if not ok:
                outdated.append((key, label, f">={lo},<{hi}", lat_v, "cmake 约束失效"))
            continue
        if not cur_v:
            rows.append((label, "?", lat_v or "?", "⚠️ 解析失败"))
            outdated.append((key, label, "?", lat_v, "解析失败"))
            continue
            cv = ver_tuple(lat_v or "")
            ok = cv and (ver_tuple(lo) <= cv < ver_tuple(hi))
            status = "✅ 约束内" if ok else "🔴 约束失效，需修改 Dockerfile"
            rows.append((label, f">={lo},<{hi}", lat_v, status))
            if not ok:
                outdated.append((key, label, f">={lo},<{hi}", lat_v, "cmake 约束失效"))
            continue
        cv, lv = ver_tuple(cur_v), ver_tuple(lat_v or "")
        if not lv:
            rows.append((label, cur_v, lat_v or "?", "⚠️ 无法获取最新版"))
            continue
        if cv == lv:
            rows.append((label, cur_v, lat_v, "✅ 最新"))
        elif cv < lv:
            major_up = major(lat_v) > major(cur_v)
            note = "🔔 大版本升级，需用户决策" if major_up else "⚠️ 有新版本"
            rows.append((label, cur_v, lat_v, note))
            outdated.append((key, label, cur_v, lat_v, "大版本" if major_up else "小版本"))
        else:
            rows.append((label, cur_v, lat_v, "❓ 当前高于官方最新，请核对"))

    return rows, outdated


def ensure_issue(outdated):
    """有更新时创建去重 issue（仅 CI 且有 token 时）"""
    if not (TOKEN and REPO):
        return
    title = f"[版本更新] ClearDNS 依赖有新版本 ({__import__('datetime').date.today().isoformat()})"
    # 去重：已存在相同标题的 open issue 则跳过
    issues = gh_api(f"/repos/{REPO}/issues?state=open&per_page=100")
    if any(i.get("title") == title for i in issues):
        return
    body_lines = [
        "自动版本核查发现以下组件有新版本：",
        "",
        "| 组件 | 当前 | 最新 | 类型 |",
        "|---|---|---|---|",
    ]
    for _, label, cur, lat, kind in outdated:
        body_lines.append(f"| {label} | {cur} | {lat} | {kind} |")
    body_lines += [
        "",
        "> 大版本升级需由用户决策后再升级；overture 为 fork（另一会话维护），需先同步 fork 再评估。",
        "> 本 issue 由 `.github/workflows/check-versions.yml` 自动生成。",
    ]
    gh_api(f"/repos/{REPO}/issues", payload={
        "title": title, "body": "\n".join(body_lines), "labels": ["dependencies"],
    })


def main():
    argv = sys.argv[1:]
    repo = os.getcwd()
    if "--repo" in argv:
        repo = os.path.abspath(argv[argv.index("--repo") + 1])
    elif argv:
        repo = os.path.abspath(argv[0])
    dockerfile = os.path.join(repo, "Dockerfile")
    if not os.path.exists(dockerfile):
        print(f"错误: 未找到 {dockerfile}", file=sys.stderr)
        return 1

    cur = parse_dockerfile(dockerfile)
    print("查询各组件官方最新稳定版 ...")
    latest = latest_versions()

    rows, outdated = build_report(cur, latest)
    print("\n## ClearDNS 依赖版本核查 " + __import__("datetime").date.today().isoformat())
    print("| 组件 | 当前 | 最新稳定版 | 状态 |")
    print("|---|---|---|---|")
    for label, cv, lv, st in rows:
        print(f"| {label} | {cv} | {lv} | {st} |")

    if not outdated:
        print("\n✅ 全部组件均已是最新，无需任何升级动作。")
    else:
        print("\n发现更新项：")
        for _, label, cv, lv, kind in outdated:
            print(f"  - {label}: {cv} -> {lv} ({kind})")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## ClearDNS 依赖版本核查\n")
            f.write("| 组件 | 当前 | 最新稳定版 | 状态 |\n|---|---|---|---|\n")
            for label, cv, lv, st in rows:
                f.write(f"| {label} | {cv} | {lv} | {st} |\n")
            f.write("\n")

    ensure_issue(outdated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
