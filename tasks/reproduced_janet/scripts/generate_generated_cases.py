#!/usr/bin/env python3
"""Generate exact-output Janet behavioral cases from the Linux gold executable."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "tasks/reproduced_janet"
GOLD = TASK / "task_env/executable"
OUT = TASK / "tests_generated/eval/cases/generated_cases.json"


def eval_case(case_id: str, code: str, *, stdin: str | None = None, timeout: int = 15) -> dict:
    case = {
        "id": case_id,
        "args": ["--eval", code],
        "expect_success": True,
        "timeout": timeout,
    }
    if stdin is not None:
        case["stdin"] = stdin
    return case


def candidates() -> list[dict]:
    cases: list[dict] = [
        eval_case(
            "seed_arrays_and_tables",
            '(print (string/join ["a" "b" "c"] ":")) '
            '(print (get @{ :x 10 :y 20 } :y))',
        ),
        eval_case(
            "seed_buffer_format",
            '(def b (buffer/format @"" "value=%04d" 23)) (print (string b))',
        ),
        eval_case(
            "seed_marshal_roundtrip",
            '(def x @{:a @[1 2 3] :b "str"}) '
            "(print (deep= x (unmarshal (marshal x))))",
        ),
        eval_case(
            "seed_date_format_utc",
            '(print (os/strftime "%Y-%m-%dT%H:%M:%S" 1388608200))',
        ),
        eval_case(
            "seed_parse_multiple_values",
            '(def forms (parse-all "(+ 1 2) :kw [a b]")) '
            "(print (length forms)) (print (in forms 1))",
        ),
        eval_case(
            "seed_sequence_filter_map",
            '(print (string/join (map string (filter odd? (range 0 16))) ","))',
        ),
        eval_case(
            "seed_fiber_resume_status",
            "(def f (fiber/new (fn [] (yield :pause) :done))) "
            "(print (resume f)) (print (resume f)) (print (fiber/status f))",
        ),
        eval_case(
            "seed_mutable_table_slots",
            "(def t @{}) (put t :alpha 11) (put t :beta 22) "
            "(print (get t :alpha) (get t :beta))",
        ),
        eval_case(
            "seed_try_catches_error_value",
            '(print (try (error "ouch") ([e] (string/has-prefix? "ouch" e))))',
        ),
    ]

    for n in range(36):
        a = n + 2
        b = n * 3 + 1
        cases.extend(
            [
                eval_case(
                    f"arith_sum_product_{n:02d}",
                    f'(print (+ {a} {b} {n})) (print (* {a} {n + 5}))',
                ),
                eval_case(
                    f"arith_difference_ratio_{n:02d}",
                    f'(print (- (* {a} {b}) {n})) (print (/ (* {a} 12) 3))',
                ),
                eval_case(
                    f"math_power_format_{n:02d}",
                    f'(print (math/pow {n % 7 + 2} 3)) '
                    f'(print (string/format "case-{n:02d}:%04d" (+ {a} {b})))',
                ),
            ]
        )

    words = [
        "Alpha",
        "Beta",
        "Gamma",
        "Delta",
        "Epsilon",
        "Zeta",
        "Eta",
        "Theta",
        "Iota",
        "Kappa",
        "Lambda",
        "Mu",
        "Nu",
        "Xi",
        "Omicron",
        "Pi",
        "Rho",
        "Sigma",
        "Tau",
        "Upsilon",
        "Phi",
        "Chi",
        "Psi",
        "Omega",
    ]
    for idx, word in enumerate(words):
        raw = f"{word}-{idx:02d}"
        cases.extend(
            [
                eval_case(
                    f"string_upper_lower_{idx:02d}",
                    f'(print (string/ascii-upper "{raw}")) '
                    f'(print (string/ascii-lower "{raw}"))',
                ),
                eval_case(
                    f"string_join_length_{idx:02d}",
                    f'(print (string/join ["{word}" "{idx}" "done"] "|")) '
                    f'(print (length "{raw}"))',
                ),
            ]
        )

    for n in range(28):
        values = [n + 1, n + 2, n + 4, n + 8]
        values_src = " ".join(str(value) for value in values)
        cases.extend(
            [
                eval_case(
                    f"array_loop_square_join_{n:02d}",
                    f"(def out @[]) "
                    f"(each x [{values_src}] (array/push out (string (* x x)))) "
                    '(print (string/join out ","))',
                ),
                eval_case(
                    f"sequence_range_filter_{n:02d}",
                    f'(print (string/join (map string (filter odd? (range {n} {n + 14}))) ":"))',
                ),
            ]
        )

    for n in range(20):
        cases.extend(
            [
                eval_case(
                    f"table_put_get_{n:02d}",
                    f"(def t @{{}}) (put t :alpha {n}) (put t :beta {n * n}) "
                    "(print (get t :alpha) (get t :beta))",
                ),
                eval_case(
                    f"buffer_numeric_format_{n:02d}",
                    f'(def b (buffer/format @"" "n=%03d square=%04d" {n} (* {n} {n}))) '
                    "(print (string b))",
                ),
            ]
        )

    parse_forms = [
        "(+ 1 2)",
        "[:a :b :c]",
        "{:x 1 :y 2}",
        "(defn f [x] (* x x))",
        "(each x [1 2] (print x))",
        "(try (error :bad) ([e] e))",
        "(fn [a b] (+ a b))",
        "(quote (alpha beta gamma))",
    ]
    for idx, form in enumerate(parse_forms):
        escaped = form.replace("\\", "\\\\").replace('"', '\\"')
        cases.append(
            eval_case(
                f"parse_form_count_{idx:02d}",
                f'(def forms (parse-all "{escaped}")) (print (length forms)) '
                f'(print (type (in forms 0)))',
            )
        )

    for n in range(16):
        cases.extend(
            [
                eval_case(
                    f"marshal_roundtrip_table_{n:02d}",
                    f'(def x @{{:n {n} :label "item-{n:02d}" :items @[{n} {n + 1} {n + 2}]}}) '
                    "(print (deep= x (unmarshal (marshal x))))",
                ),
                eval_case(
                    f"fiber_yield_resume_{n:02d}",
                    f"(def f (fiber/new (fn [] (yield {n}) (yield {n + 1}) {n + 2}))) "
                    "(print (resume f)) (print (resume f)) (print (resume f)) "
                    "(print (fiber/status f))",
                ),
            ]
        )

    stdin_payloads = [
        "alpha\nbeta\n",
        "MiXeD Case\n",
        "symbols !@#\n",
        "12345\n67890\n",
        "spaced words here\n",
        "last-line",
    ]
    for idx, payload in enumerate(stdin_payloads):
        cases.append(
            eval_case(
                f"stdin_read_transform_{idx:02d}",
                "(def s (file/read stdin :all)) "
                "(print (length s)) "
                "(print (string/ascii-upper s))",
                stdin=payload,
            )
        )

    return cases


def main() -> int:
    if not GOLD.exists():
        raise SystemExit(f"gold executable missing: {GOLD}")
    raw_cases = candidates()
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        candidate_path = tmpdir / "candidates.json"
        output_path = tmpdir / "generated_cases.json"
        runner_path = tmpdir / "runner.py"
        candidate_path.write_text(json.dumps(raw_cases, indent=2) + "\n")
        runner_path.write_text(
            r'''
import json
import os
import re
import subprocess
from pathlib import Path

cases = json.loads(Path("/workspace/candidates.json").read_text())
out = []
base_env = os.environ.copy()
base_env["LC_ALL"] = "C"
base_env["TZ"] = "UTC"
for key in list(base_env):
    if key.startswith("JANET_"):
        base_env.pop(key)

unstable = re.compile(r"0x[0-9A-Fa-f]{6,}")

for case in cases:
    proc = subprocess.run(
        ["/workspace/executable", *case["args"]],
        input=case.get("stdin"),
        text=True,
        capture_output=True,
        timeout=case.get("timeout", 15),
        env=base_env,
    )
    if case.get("expect_success", True) and proc.returncode != 0:
        raise SystemExit(
            f"{case['id']} failed unexpectedly with {proc.returncode}\n"
            f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
        )
    combined = proc.stdout + proc.stderr
    if unstable.search(combined):
        raise SystemExit(f"{case['id']} produced unstable pointer-like output: {combined!r}")
    item = {
        "id": case["id"],
        "args": case["args"],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    if "stdin" in case:
        item["stdin"] = case["stdin"]
    out.append(item)

Path("/workspace/out/generated_cases.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"generated {len(out)} cases")
'''.lstrip()
        )
        cmd = [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            "--network",
            "none",
            "-v",
            f"{GOLD}:/workspace/executable:ro",
            "-v",
            f"{candidate_path}:/workspace/candidates.json:ro",
            "-v",
            f"{runner_path}:/workspace/runner.py:ro",
            "-v",
            f"{tmpdir}:/workspace/out",
            "python:3.11-slim",
            "python3",
            "/workspace/runner.py",
        ]
        subprocess.run(cmd, check=True)
        generated = json.loads(output_path.read_text())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(generated, indent=2) + "\n")
    print(f"wrote {OUT} with {len(generated)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
