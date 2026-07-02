#!/usr/bin/env python3
"""Record exact black-box outputs for selected upstream PocketLang tests."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


UPSTREAM_SCRIPTS = [
    "tests/lang/basics.pk",
    "tests/lang/builtin_fn.pk",
    "tests/lang/builtin_ty.pk",
    "tests/lang/class.pk",
    "tests/lang/closure.pk",
    "tests/lang/controlflow.pk",
    "tests/lang/fibers.pk",
    "tests/lang/functions.pk",
    "tests/lang/import.pk",
    "tests/lang/tco.pk",
    "tests/modules/dummy.pk",
    "tests/modules/math.pk",
    "tests/modules/path.pk",
    "tests/modules/json.pk",
    "tests/random/linked_list.pk",
    "tests/random/lisp_eval.pk",
    "tests/random/string_algo.pk",
    "tests/examples/brainfuck.pk",
    "tests/examples/fib.pk",
    "tests/examples/fizzbuzz.pk",
    "tests/examples/helloworld.pk",
    "tests/examples/matrix.pk",
    "tests/examples/pi.pk",
    "tests/examples/prime.pk",
]


def case_id(path: str) -> str:
    return path.removesuffix(".pk").replace("/", "__").replace(" ", "_")


def normalize_output(text: str, fixture_root: Path) -> str:
    text = text.replace(str(fixture_root), "/workspace/fixtures/pocketlang")
    return re.sub(r"0x[0-9A-Fa-f]+", "0x<addr>", text)


def run_case(executable: Path, fixture_root: Path, rel_path: str, timeout: int) -> dict | None:
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    env["TZ"] = "UTC"
    env["NO_COLOR"] = "1"
    proc = subprocess.run(
        [str(executable), rel_path],
        cwd=fixture_root,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode == 0 and proc.stdout == "" and proc.stderr == "":
        return None
    return {
        "id": case_id(rel_path),
        "source": rel_path,
        "args": [rel_path],
        "returncode": proc.returncode,
        "stdout": normalize_output(proc.stdout, fixture_root),
        "stderr": normalize_output(proc.stderr, fixture_root),
        "timeout": timeout,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    cases = []
    skipped_empty = []
    for rel_path in UPSTREAM_SCRIPTS:
        result = run_case(args.executable, args.fixtures, rel_path, args.timeout)
        if result is None:
            skipped_empty.append(rel_path)
            continue
        cases.append(result)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(cases, indent=2) + "\n")
    print(
        json.dumps(
            {
                "written": str(args.out),
                "cases": len(cases),
                "skipped_empty_success": skipped_empty,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
