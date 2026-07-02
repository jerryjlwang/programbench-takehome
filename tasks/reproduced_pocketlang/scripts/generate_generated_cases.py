#!/usr/bin/env python3
"""Generate exact-output PocketLang behavioral cases from the Linux gold executable."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


def cmd_case(case_id: str, code: str, *, expect_success: bool = True, timeout: int = 15) -> dict:
    return {
        "id": case_id,
        "args": ["-c", code],
        "expect_success": expect_success,
        "timeout": timeout,
    }


def file_case(
    case_id: str,
    file_name: str,
    content: str,
    *,
    expect_success: bool = True,
    timeout: int = 15,
    env: dict[str, str] | None = None,
    files: dict[str, str] | None = None,
) -> dict:
    case = {
        "id": case_id,
        "args": [file_name],
        "files": {file_name: content, **(files or {})},
        "expect_success": expect_success,
        "timeout": timeout,
    }
    if env:
        case["env"] = env
    return case


def candidates() -> list[dict]:
    cases: list[dict] = []

    for n in range(60):
        a = n + 3
        b = n * 2 + 5
        c = n % 7 + 2
        cases.extend(
            [
                cmd_case(
                    f"arith_precedence_{n:02d}",
                    f"print(({a} + {b}) * {c}); print({a} ** 2); print({b} % {c})",
                ),
                cmd_case(
                    f"bitwise_combo_{n:02d}",
                    f"x = {a * 17}; print((x & {b * 9}) | {c}); print((x ^ {b}) >> 1)",
                ),
            ]
        )

    for n in range(50):
        end = n % 11 + 5
        cases.extend(
            [
                cmd_case(
                    f"range_sum_{n:02d}",
                    f"sum = 0; for i in 0..{end} do sum += i end; print(sum)",
                ),
                cmd_case(
                    f"while_factorial_{n:02d}",
                    f"i = 1; acc = 1; while i <= {n % 6 + 3} acc *= i; i += 1 end; print(acc)",
                ),
            ]
        )

    words = [
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "iota",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "omicron",
        "pi",
        "rho",
        "sigma",
        "tau",
        "upsilon",
        "phi",
        "chi",
        "psi",
        "omega",
    ]
    for idx, word in enumerate(words):
        raw = f"{word}-{idx:02d}"
        cases.extend(
            [
                cmd_case(
                    f"string_methods_{idx:02d}",
                    f"s = '{raw}'; print(s.upper()); print(s.lower()); print(s.replace('-', ':'))",
                ),
                cmd_case(
                    f"string_slice_interpolation_{idx:02d}",
                    f"s = '{word}'; print(s[0..2]); print('item-${{{idx} + 7}}:$s')",
                ),
            ]
        )

    for n in range(45):
        values = [n + 1, n + 2, n + 4, n + 8]
        values_src = ", ".join(str(v) for v in values)
        cases.extend(
            [
                cmd_case(
                    f"list_append_pop_{n:02d}",
                    f"l = [{values_src}]; l.append({n * 3}); print(l.length); print(l.pop()); print(l[1])",
                ),
                cmd_case(
                    f"map_lookup_default_{n:02d}",
                    f"m = {{'a': {n}, 'b': {n*n}}}; print(m['a'] + m['b']); print(m.get('z', {n + 11}))",
                ),
            ]
        )

    for n in range(40):
        cases.extend(
            [
                cmd_case(
                    f"function_square_offset_{n:02d}",
                    f"def f(x) return x * x + {n} end; print(f({n % 9 + 2}))",
                ),
                cmd_case(
                    f"closure_shared_upvalue_{n:02d}",
                    f"def make(base) return fn(x) return base + x + {n} end end; f = make({n + 3}); print(f({n % 5}))",
                ),
            ]
        )

    for n in range(28):
        cases.append(
            cmd_case(
                f"class_operator_{n:02d}",
                "class Box\n"
                "  def _init(v) self.v = v end\n"
                "  def +(other) return Box(self.v + other.v) end\n"
                "  def _str return 'Box(${self.v})' end\n"
                "end\n"
                f"print(Box({n}) + Box({n + 5}))",
            )
        )

    for n in range(18):
        file_name = f"script_case_{n:02d}.pk"
        content = "\n".join(
            [
                "def fib(n)",
                "  if n < 2 then return n end",
                "  return fib(n-1) + fib(n-2)",
                "end",
                f"print(fib({n % 9 + 2}))",
                f"print('file-case-{n:02d}')",
            ]
        ) + "\n"
        cases.append(file_case(f"script_fibonacci_{n:02d}", file_name, content))

    for n in range(40):
        limit = n % 13 + 4
        file_name = f"control_case_{n:02d}.pk"
        content = "\n".join(
            [
                "total = 0",
                f"for i in 0..{limit} do",
                "  if i % 2 == 0 then",
                "    total += i * i",
                "  else",
                "    total -= i",
                "  end",
                "end",
                "print(total)",
            ]
        ) + "\n"
        cases.append(file_case(f"script_control_flow_{n:02d}", file_name, content))

    for n in range(32):
        file_name = f"function_case_{n:02d}.pk"
        content = "\n".join(
            [
                "def make(base)",
                "  return fn(x)",
                f"    return base * x + {n}",
                "  end",
                "end",
                f"f = make({n % 7 + 2})",
                f"print(f({n % 9 + 3}))",
            ]
        ) + "\n"
        cases.append(file_case(f"script_closure_return_{n:02d}", file_name, content))

    module_cases = {
        "module_types_hash": "\n".join(
            [
                "import types",
                "print(types.hashable(123))",
                "print(types.hashable('abc'))",
                "print(types.hashable([1, 2]))",
                "print(types.hash('abc'))",
            ]
        ) + "\n",
        "module_bytebuffer_basic": "\n".join(
            [
                "import types",
                "b = types.ByteBuffer()",
                "print(b.write(65))",
                "print(b.write(66))",
                "print(b.write('CD'))",
                "print(b.count())",
                "print(b.string())",
                "print(b[1])",
                "b[1] = 90",
                "print(b.string())",
                "b.clear()",
                "print(b.count())",
            ]
        ) + "\n",
        "module_bytebuffer_fill": "\n".join(
            [
                "import types",
                "b = types.ByteBuffer()",
                "b.reserve(8)",
                "b.fill(3, 88)",
                "print(b.count())",
                "print(b[0])",
                "print(b[2])",
            ]
        ) + "\n",
        "module_vector_accessors": "\n".join(
            [
                "from types import Vector",
                "v = Vector(1, 2, 3)",
                "print(v)",
                "print(v.x + v.y + v.z)",
                "v.y = 10",
                "v.z = v.x + v.y",
                "print(v)",
            ]
        ) + "\n",
        "module_os_files": "\n".join(
            [
                "import os",
                "print(os.NAME)",
                "print(os.getenv('PB_TEST_ENV'))",
                "print(os.getenv('PB_MISSING_ENV'))",
                "print(os.filesize('data.txt'))",
                "os.mkdir('tmpdir')",
                "os.chdir('tmpdir')",
                "print(os.getcwd())",
                "os.chdir('..')",
                "os.rmdir('tmpdir')",
                "print(os.exepath())",
            ]
        ) + "\n",
        "module_os_unlink_moditime": "\n".join(
            [
                "import os",
                "print(os.filesize('payload.bin'))",
                "print(os.moditime('payload.bin') > 0)",
                "os.unlink('payload.bin')",
                "print(os.moditime('payload.bin'))",
            ]
        ) + "\n",
        "module_time_sleep": "\n".join(
            [
                "from time import sleep",
                "sleep(0)",
                "print('sleep-ok')",
            ]
        ) + "\n",
    }
    for case_id, content in module_cases.items():
        extra_files = {}
        env = None
        if case_id == "module_os_files":
            extra_files = {"data.txt": "abcdef\n"}
            env = {"PB_TEST_ENV": "pocket-env"}
        elif case_id == "module_os_unlink_moditime":
            extra_files = {"payload.bin": "0123456789"}
        cases.append(file_case(case_id, f"{case_id}.pk", content, env=env, files=extra_files))

    module_error_cases = {
        "module_types_hash_error": "\n".join(
            [
                "import types",
                "print(types.hash([1, 2, 3]))",
            ]
        ) + "\n",
        "module_bytebuffer_index_error": "\n".join(
            [
                "import types",
                "b = types.ByteBuffer()",
                "b.write(65)",
                "print(b[4])",
            ]
        ) + "\n",
        "module_bytebuffer_value_error": "\n".join(
            [
                "import types",
                "b = types.ByteBuffer()",
                "b.write(65)",
                "b[0] = 999",
            ]
        ) + "\n",
        "module_vector_arity_error": "\n".join(
            [
                "from types import Vector",
                "print(Vector(1, 2, 3, 4))",
            ]
        ) + "\n",
        "module_os_filesize_error": "\n".join(
            [
                "import os",
                "print(os.filesize('missing.txt'))",
            ]
        ) + "\n",
    }
    for case_id, content in module_error_cases.items():
        cases.append(
            file_case(case_id, f"{case_id}.pk", content, expect_success=False)
        )

    cases.extend(
        [
            {
                "id": "cli_long_cmd_option",
                "args": ["--cmd", "print('long-cmd'); print(6 * 7)"],
                "expect_success": True,
                "timeout": 15,
            },
            {
                "id": "cli_debug_long_cmd_option",
                "args": ["--debug", "--cmd", "print('debug-long-cmd')"],
                "expect_success": True,
                "timeout": 15,
            },
            {
                "id": "cli_version_option",
                "args": ["--version"],
                "expect_success": True,
                "timeout": 15,
            },
            {
                "id": "cli_help_option",
                "args": ["--help"],
                "expect_success": True,
                "timeout": 15,
            },
            {
                "id": "cli_missing_file_error",
                "args": ["missing_script.pk"],
                "expect_success": False,
                "timeout": 15,
            },
            {
                "id": "cli_invalid_option_error",
                "args": ["--not-an-option"],
                "expect_success": False,
                "timeout": 15,
            },
        ]
    )

    error_snippets = [
        "print(1 + )",
        "assert(false, 'generated failure')",
        "missing_name + 1",
        "l = [1, 2]; print(l[9])",
        "class Bad is MissingParent end",
        "def broken(x) if x then print(x) end",
    ]
    for idx, code in enumerate(error_snippets):
        cases.append(cmd_case(f"error_diagnostic_{idx:02d}", code, expect_success=False))

    return cases


def normalize_output(text: str, cwd: Path, executable: Path) -> str:
    text = text.replace(str(cwd), "<tmp>")
    text = text.replace(str(executable), "<executable>")
    return re.sub(r"0x[0-9A-Fa-f]+", "0x<addr>", text)


def run_raw_case(executable: Path, raw_case: dict, cwd: Path) -> dict | None:
    for rel_path, content in raw_case.get("files", {}).items():
        target = cwd / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    env = os.environ.copy()
    env["LC_ALL"] = "C"
    env["TZ"] = "UTC"
    env["NO_COLOR"] = "1"
    env.update(raw_case.get("env", {}))
    proc = subprocess.run(
        [str(executable), *raw_case["args"]],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=raw_case.get("timeout", 15),
    )
    if raw_case.get("expect_success", True) and proc.returncode != 0:
        return None
    if not raw_case.get("expect_success", True) and proc.returncode == 0:
        return None
    if proc.returncode == 0 and proc.stdout == "" and proc.stderr == "":
        return None
    case = {
        "id": raw_case["id"],
        "args": raw_case["args"],
        "returncode": proc.returncode,
        "stdout": normalize_output(proc.stdout, cwd, executable),
        "stderr": normalize_output(proc.stderr, cwd, executable),
        "timeout": raw_case.get("timeout", 15),
    }
    if "files" in raw_case:
        case["files"] = raw_case["files"]
    if "env" in raw_case:
        case["env"] = raw_case["env"]
    return case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    out = []
    skipped = []
    for raw_case in candidates():
        with tempfile.TemporaryDirectory() as tmp:
            case = run_raw_case(args.executable, raw_case, Path(tmp))
        if case is None:
            skipped.append(raw_case["id"])
            continue
        out.append(case)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"written": str(args.out), "cases": len(out), "skipped": skipped}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
