#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC="$ROOT/tasks/reproduced_janet/_src/janet"
OUT="$ROOT/tasks/reproduced_janet/gold"
LOG="$ROOT/tasks/reproduced_janet/logs/gold_build.log"

mkdir -p "$OUT" "$(dirname "$LOG")"

docker run --rm --platform linux/amd64 \
  -v "$SRC:/src" \
  -v "$OUT:/out" \
  gcc:13-bookworm bash -lc '
    set -euo pipefail
    cd /src
    make clean
    make build/janet JANET_BUILD="\\\"0fea20c8\\\""
    cp build/janet /out/janet
    sha256sum /out/janet
    file /out/janet
  ' | tee "$LOG"
