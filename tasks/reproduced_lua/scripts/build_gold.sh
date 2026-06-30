#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC="$ROOT/tasks/reproduced_lua/_src/lua"
OUT="$ROOT/tasks/reproduced_lua/gold"
LOG="$ROOT/tasks/reproduced_lua/logs/gold_build.log"

mkdir -p "$OUT" "$(dirname "$LOG")"

docker run --rm --platform linux/amd64 \
  -v "$SRC:/src" \
  -v "$OUT:/out" \
  gcc:13-bookworm bash -lc '
    set -euo pipefail
    cd /src
    make clean
    make all
    cp lua /out/lua
    sha256sum /out/lua
    file /out/lua
  ' | tee "$LOG"
