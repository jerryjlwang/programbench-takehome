#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$ROOT/tasks/reproduced_janet/scripts/quality_gate.py"
QC_SCRIPT="$ROOT/tasks/reproduced_janet/scripts/build_qc_report.py"
EVAL="$ROOT/tasks/reproduced_janet/tests_generated/eval"
EXECUTABLE="$ROOT/tasks/reproduced_janet/task_env/executable"
OUT="$ROOT/tasks/reproduced_janet/reports/quality_generated"
LOG="$ROOT/tasks/reproduced_janet/logs/quality_generated.log"

mkdir -p "$OUT" "$(dirname "$LOG")"

set +e
docker run --rm --platform linux/amd64 \
  -v "$SCRIPT:/workspace/quality_gate.py:ro" \
  -v "$EVAL:/workspace/eval:ro" \
  -v "$EXECUTABLE:/workspace/executable:ro" \
  -v "$OUT:/workspace/out" \
  python:3.11-slim bash -lc '
    set -euo pipefail
    pip install pytest -q >/dev/null
    python3 /workspace/quality_gate.py \
      --eval /workspace/eval \
      --executable /workspace/executable \
      --out /workspace/out
  ' | tee "$LOG"
gate_rc="${PIPESTATUS[0]}"
set -e

qc_rc=0
python3 "$QC_SCRIPT" --root "$ROOT" || qc_rc="$?"

if [[ "$gate_rc" -ne 0 ]]; then
  exit "$gate_rc"
fi
exit "$qc_rc"
