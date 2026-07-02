#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
INSTANCE_ID="janet-lang__janet.0fea20c"
INPUT="${1:?usage: evaluate_submission.sh /path/to/run-dir-or-submission.tar.gz}"
EVAL="$ROOT/tasks/reproduced_janet/tests_generated/eval"
GOLD="$ROOT/tasks/reproduced_janet/task_env/executable"
REPORT_ROOT="$ROOT/tasks/reproduced_janet/reports/evals"
EVAL_IMAGE="${EVAL_IMAGE:-programbench-janet-eval:local}"

if [[ -d "$INPUT" ]]; then
  if [[ -f "$INPUT/$INSTANCE_ID/submission.tar.gz" ]]; then
    SUBMISSION="$INPUT/$INSTANCE_ID/submission.tar.gz"
    RUN_NAME="$(basename "$INPUT")"
  elif [[ -f "$INPUT/submission.tar.gz" ]]; then
    SUBMISSION="$INPUT/submission.tar.gz"
    RUN_NAME="$(basename "$(dirname "$INPUT")")_$(basename "$INPUT")"
  else
    echo "no submission.tar.gz found under $INPUT" >&2
    exit 1
  fi
else
  SUBMISSION="$INPUT"
  RUN_NAME="$(basename "${SUBMISSION%.tar.gz}")"
fi

if [[ ! -f "$SUBMISSION" ]]; then
  echo "submission archive not found: $SUBMISSION" >&2
  exit 1
fi

OUT="$REPORT_ROOT/$RUN_NAME"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT" "$WORK/submission"
rm -f "$OUT/compile.log" "$OUT/results.xml" "$OUT/pytest.log"

tar -xzf "$SUBMISSION" -C "$WORK/submission"

gold_hash="$(shasum -a 256 "$GOLD" | awk '{print $1}')"

python3 - "$WORK/submission" "$GOLD" "$OUT/summary.json" <<'PY'
import json
import sys
from pathlib import Path

submission, gold, summary = map(Path, sys.argv[1:])
gold_bytes = gold.read_bytes()
patterns = [
    "memfd_create",
    "fexecve",
    "/proc/self/fd",
    "orig_executable",
    "binary_data",
    "cp executable",
    "cp ./executable",
    "open(\"executable\"",
    "open('./executable'",
    "open(\"./executable\"",
]
findings = []
for path in submission.rglob("*"):
    if not path.is_file():
        continue
    data = path.read_bytes()
    rel = str(path.relative_to(submission))
    if gold_bytes and gold_bytes in data:
        findings.append({"file": rel, "reason": "contains_gold_oracle_bytes"})
    text = data.decode("utf-8", errors="ignore")
    for pattern in patterns:
        if pattern in text:
            findings.append({"file": rel, "reason": f"wrapper_pattern:{pattern}"})

if findings:
    Path(summary).write_text(json.dumps({"status": "rejected_wrapper_or_oracle", "findings": findings}, indent=2) + "\n")
    print(f"rejected wrapper/oracle submission; see {summary}", file=sys.stderr)
    raise SystemExit(23)
PY

# A valid ProgramBench-style submission must build its replacement from
# submitted source. The solver-facing oracle is named ./executable, so any
# prebuilt file with that name would let compile.sh copy or embed it.
rm -f "$WORK/submission/executable"

compile_rc=0
docker run --rm --platform linux/amd64 --network none \
  -v "$WORK/submission:/workspace" \
  -w /workspace \
  gcc:13-bookworm bash -lc '
    set -euo pipefail
    chmod +x compile.sh
    ./compile.sh
    test -x executable
  ' > "$OUT/compile.log" 2>&1 || compile_rc="$?"

if [[ "$compile_rc" -ne 0 ]]; then
  echo "{\"status\":\"compile_failed\",\"returncode\":$compile_rc}" > "$OUT/summary.json"
  echo "compile failed; see $OUT/compile.log" >&2
  exit "$compile_rc"
fi

candidate_hash="$(shasum -a 256 "$WORK/submission/executable" | awk '{print $1}')"
if [[ "$candidate_hash" == "$gold_hash" ]]; then
  echo "{\"status\":\"rejected_gold_hash\",\"executable_hash\":\"$candidate_hash\"}" > "$OUT/summary.json"
  echo "candidate executable hash matches gold oracle; refusing to score wrapper/copy submission" >&2
  exit 2
fi

python3 - "$WORK/submission/executable" "$GOLD" "$OUT/summary.json" "$candidate_hash" <<'PY'
import json
import sys
from pathlib import Path

candidate, gold, summary, candidate_hash = sys.argv[1:]
candidate_bytes = Path(candidate).read_bytes()
gold_bytes = Path(gold).read_bytes()
if gold_bytes and gold_bytes in candidate_bytes:
    Path(summary).write_text(
        json.dumps(
            {
                "status": "rejected_gold_embedded_in_candidate",
                "executable_hash": candidate_hash,
            },
            indent=2,
        )
        + "\n"
    )
    print("candidate executable embeds the gold oracle bytes; refusing to score", file=sys.stderr)
    raise SystemExit(24)
PY

if ! docker image inspect "$EVAL_IMAGE" >/dev/null 2>&1; then
  docker build --platform linux/amd64 -t "$EVAL_IMAGE" - <<'DOCKERFILE'
FROM python:3.11-slim
RUN pip install pytest -q
DOCKERFILE
fi

test_rc=0
docker run --rm --platform linux/amd64 --network none \
  -v "$WORK/submission/executable:/workspace/executable:ro" \
  -v "$EVAL:/workspace/eval:ro" \
  -v "$OUT:/workspace/out" \
  "$EVAL_IMAGE" bash -lc '
    set -euo pipefail
    cd /workspace
    EXECUTABLE=/workspace/executable python3 -m pytest -p no:cacheprovider \
      eval/tests -q --tb=short --junitxml=/workspace/out/results.xml
  ' 2>&1 | tee "$OUT/pytest.log" || test_rc="${PIPESTATUS[0]}"

if [[ ! -f "$OUT/results.xml" ]]; then
  echo "{\"status\":\"test_infra_failed\",\"returncode\":$test_rc,\"executable_hash\":\"$candidate_hash\"}" > "$OUT/summary.json"
  echo "test infrastructure failed before producing JUnit XML; see $OUT/pytest.log" >&2
  exit "$test_rc"
fi

python3 - "$OUT/results.xml" "$OUT/summary.json" "$candidate_hash" "$test_rc" <<'PY'
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

results_xml, summary_json, executable_hash, returncode = sys.argv[1:]
root = ET.parse(results_xml).getroot()
suite = root if root.tag == "testsuite" else root.find("testsuite")
summary = {
    "status": "passed" if returncode == "0" else "failed",
    "returncode": int(returncode),
    "executable_hash": executable_hash,
    "tests": int(suite.attrib.get("tests", 0)),
    "failures": int(suite.attrib.get("failures", 0)),
    "errors": int(suite.attrib.get("errors", 0)),
    "skipped": int(suite.attrib.get("skipped", 0)),
    "time": float(suite.attrib.get("time", 0.0)),
}
Path(summary_json).write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

exit "$test_rc"
