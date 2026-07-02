#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC="$ROOT/tasks/reproduced_pocketlang/_src/pocketlang"
EVAL="$ROOT/tasks/reproduced_pocketlang/tests_generated/eval"
OUT="$ROOT/tasks/reproduced_pocketlang/reports/coverage_generated"
LOG="$ROOT/tasks/reproduced_pocketlang/logs/coverage_generated.log"

mkdir -p "$OUT" "$(dirname "$LOG")"

docker run --rm --platform linux/amd64 \
  -v "$SRC:/src" \
  -v "$EVAL:/workspace/eval:ro" \
  -v "$OUT:/coverage" \
  gcc:13-bookworm bash -lc '
    set -euo pipefail
    apt-get update >/dev/null
    apt-get install -y python3-pytest gcovr >/dev/null

    cd /src
    make clean
    find . -name "*.gcda" -o -name "*.gcno" | xargs -r rm -f
    make release CFLAGS="-fPIC --coverage" RELEASE_CFLAGS="-O0 -g --coverage" LDFLAGS="-lm -ldl --coverage"

    cd /workspace
    EXECUTABLE=/src/build/Release/bin/pocket python3 -m pytest -p no:cacheprovider eval/tests -q --tb=short

    gcovr --root /src --object-directory /src/build/Release/obj \
      --filter /src/cli --filter /src/src/core --filter /src/src/libs \
      --exclude /src/src/libs/thirdparty \
      --gcov-ignore-parse-errors \
      --txt /coverage/coverage_summary.txt \
      --html-details /coverage/coverage.html \
      --json-summary /coverage/coverage_summary.json \
      --json /coverage/coverage.json

    cat /coverage/coverage_summary.txt
  ' | tee "$LOG"
