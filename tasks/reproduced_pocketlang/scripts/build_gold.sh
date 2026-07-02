#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TASK="$ROOT/tasks/reproduced_pocketlang"
SRC="$TASK/_src/pocketlang"
OUT="$TASK/gold"
TASK_ENV="$TASK/task_env"
LOG="$TASK/logs/gold_build.log"

mkdir -p "$OUT" "$TASK_ENV" "$(dirname "$LOG")"

docker run --rm --platform linux/amd64 \
  -v "$SRC:/src" \
  -v "$OUT:/out" \
  gcc:13-bookworm bash -lc '
    set -euo pipefail
    cd /src
    make clean
    make release
    cp build/Release/bin/pocket /out/pocket
    sha256sum /out/pocket
    file /out/pocket
  ' | tee "$LOG"

cp "$OUT/pocket" "$TASK_ENV/executable"
chmod 755 "$TASK_ENV/executable"
sha256sum "$TASK_ENV/executable" | tee "$TASK/logs/gold_sha256.txt"
