#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC="$ROOT/tasks/reproduced_janet/_src/janet"
EVAL="$ROOT/tasks/reproduced_janet/tests_generated/eval"
OUT="$ROOT/tasks/reproduced_janet/reports/coverage_generated"
LOG="$ROOT/tasks/reproduced_janet/logs/coverage_generated.log"
QC_SCRIPT="$ROOT/tasks/reproduced_janet/scripts/build_qc_report.py"

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
    make build/janet \
      JANET_BUILD="\\\"0fea20c8\\\"" \
      CFLAGS="-O0 -g --coverage" \
      LDFLAGS="-rdynamic --coverage"

    cd /workspace
    EXECUTABLE=/src/build/janet python3 -m pytest -p no:cacheprovider eval/tests -q --tb=short

    gcovr --root /src --object-directory /src/build \
      --filter /src/src --filter /src/build/c --gcov-ignore-parse-errors \
      --txt /coverage/coverage_summary.txt \
      --html-details /coverage/coverage.html \
      --json-summary /coverage/coverage_summary.json \
      --json /coverage/coverage.json

    cat /coverage/coverage_summary.txt
  ' | tee "$LOG"

if [[ -f "$ROOT/tasks/reproduced_janet/reports/quality_generated/quality_report.json" ]]; then
  python3 "$QC_SCRIPT" --root "$ROOT"
fi
