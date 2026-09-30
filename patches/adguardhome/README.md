# AdGuard Home patches (ClearDNS)

These patches are applied to AdGuard Home **v0.107.79** during the Docker build
(`adguard-src` stage): overlay files are copied on top of the cloned tree, then
`git apply` runs on `git/*.patch`.

Keep AGH customizations here. Do not edit AdGuard Home in the image by hand.

## Layout

- `overlay/` — new files copied into the AGH source tree
  - `internal/ipgeo/` — offline ip2region lookup (vendored `xdb` searcher)
  - `client/src/components/Logs/Cells/GeoCell.tsx` — query-log geo column
- `git/` — unified diffs against upstream files
  - `0001-header-hide-nav.patch` — hide setup nav (former Dockerfile echo)
  - `0002-querylog-json-geo.patch` — add `answer[].geo` at API display time
  - `0003-querylog-ui-geo.patch` — table column + tooltip/modal geo text

## Refresh on a 0.107.x bump

1. Clone the new tag: `git clone --depth=1 -b v0.107.xx https://github.com/AdguardTeam/AdGuardHome.git`.
2. Copy overlay: `cp -a overlay/. AdGuardHome/`.
3. Apply patches: `git -C AdGuardHome apply --verbose --check git/*.patch` then `git apply`.
4. If `git apply` conflicts, fix the files in the clone, then regenerate:

   ```sh
   git -C AdGuardHome diff -- client/src/components/Header/Header.css > git/0001-header-hide-nav.patch
   git -C AdGuardHome diff -- internal/querylog/json.go > git/0002-querylog-json-geo.patch
   git -C AdGuardHome diff -- \
     client/src/helpers/helpers.tsx \
     client/src/components/Logs/Cells/Header.tsx \
     client/src/components/Logs/Cells/index.tsx \
     client/src/components/Logs/Logs.css \
     client/src/__locales/en.json \
     client/src/__locales/zh-cn.json \
     > git/0003-querylog-ui-geo.patch
   ```

5. Point `Dockerfile` `ENV ADGUARD` at the new tag. Do not vendor the whole AGH tree.

## Runtime

xdb files are **not** in git. The image downloads them at build time to
`/usr/share/ip2region/ip2region_v{4,6}.xdb`. Override with `IP2REGION_V4` /
`IP2REGION_V6`. If a file is missing, AGH still starts and geo fields stay empty.

ip2region `xdb` searcher is Apache-2.0 OR MIT; see `overlay/internal/ipgeo/xdb/LICENSE.md`.
