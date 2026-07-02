#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$ROOT/tasks/reproduced_pocketlang/scripts/quality_gate.py"
EVAL="$ROOT/tasks/reproduced_pocketlang/tests_generated/eval"
EXECUTABLE="$ROOT/tasks/reproduced_pocketlang/task_env/executable"
OUT="$ROOT/tasks/reproduced_pocketlang/reports/quality_generated"
LOG="$ROOT/tasks/reproduced_pocketlang/logs/quality_generated.log"

mkdir -p "$OUT" "$(dirname "$LOG")"

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
