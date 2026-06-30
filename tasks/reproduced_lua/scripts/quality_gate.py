#!/usr/bin/env python3
"""Quality gate for generated ProgramBench-style pytest tests.

Checks:
- static assertion lint for common weak-test patterns
- full suite passes against gold
- no tests pass against a dummy executable
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


EXISTS_CALL_NAMES = {"exists", "isfile", "isdir", "is_file", "is_dir"}

STATIC_CHECK_CATALOG = [
    {
        "id": "no_assertions",
        "severity": "HIGH",
        "description": "Test function contains no pytest assertions.",
        "blocking": True,
    },
    {
        "id": "trivially_true",
        "severity": "HIGH",
        "description": "Assertion is always true, such as assert True or assert X or True.",
        "blocking": True,
    },
    {
        "id": "sole_returncode",
        "severity": "HIGH",
        "description": "Only assertion checks returncode == 0.",
        "blocking": True,
    },
    {
        "id": "returncode_in_list",
        "severity": "HIGH",
        "description": "Assertion allows non-zero exits with returncode in a list.",
        "blocking": True,
    },
    {
        "id": "pass_body",
        "severity": "HIGH",
        "description": "Test body is just pass.",
        "blocking": True,
    },
    {
        "id": "assertion_disjunction",
        "severity": "HIGH",
        "description": "Assertion uses A or B instead of asserting an exact outcome.",
        "blocking": True,
    },
    {
        "id": "if_no_else",
        "severity": "HIGH",
        "description": "If branch asserts with no else, silently passing when false.",
        "blocking": True,
    },
    {
        "id": "if_else_both_assert",
        "severity": "HIGH",
        "description": "Both if and else branches assert, suggesting non-deterministic behavior.",
        "blocking": True,
    },
    {
        "id": "try_except_swallow",
        "severity": "HIGH",
        "description": "Except handler with pass swallows failures.",
        "blocking": True,
    },
    {
        "id": "all_assertions_weak",
        "severity": "HIGH",
        "description": "All assertions only check returncode, len, or isdigit.",
        "blocking": True,
    },
    {
        "id": "short_substring",
        "severity": "HIGH",
        "description": "Substring check is shorter than 15 characters.",
        "blocking": True,
    },
    {
        "id": "golden_written_in_test",
        "severity": "HIGH",
        "description": "Test writes to its own golden file.",
        "blocking": True,
    },
    {
        "id": "golden_no_equality",
        "severity": "HIGH",
        "description": "Golden file is referenced in docstring but never compared with ==.",
        "blocking": True,
    },
    {
        "id": "golden_docstring",
        "severity": "HIGH",
        "description": "Golden file is mentioned in docstring but not found in the test body.",
        "blocking": True,
    },
    {
        "id": "for_no_guard",
        "severity": "MED",
        "description": "Loop-only assertions have no pre-loop length check.",
        "blocking": True,
    },
    {
        "id": "weak_sole_assertion",
        "severity": "MED",
        "description": "Sole assertion is len(x) > N.",
        "blocking": True,
    },
    {
        "id": "relative_length_assertion",
        "severity": "MED",
        "description": "Assertion uses len(x) >= N, a relative bound that verifies no content.",
        "blocking": True,
    },
    {
        "id": "any_all_no_guard",
        "severity": "MED",
        "description": "any()/all() assertion has no non-empty guard.",
        "blocking": True,
    },
    {
        "id": "file_exists_no_content",
        "severity": "MED",
        "description": "path.exists() assertion has no content assertion.",
        "blocking": True,
    },
    {
        "id": "only_negative_assertions",
        "severity": "MED",
        "description": "All assertions are negative checks such as not in or !=.",
        "blocking": True,
    },
    {
        "id": "catches",
        "severity": "LOW",
        "description": "Missing or too-short CATCHES docstring.",
        "blocking": False,
    },
]

DYNAMIC_CHECK_CATALOG = [
    {
        "id": "gold_suite_passes",
        "description": "Every generated test passes against the gold executable.",
        "blocking": True,
    },
    {
        "id": "dummy_suite_rejects",
        "description": "No generated test passes against a dummy executable.",
        "blocking": True,
    },
]


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted(node.func)
    return ""


def is_returncode_check(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    parts = [node.left, *node.comparators]
    return any(dotted(part).endswith(".returncode") for part in parts)


def compare_uses_returncode_zero(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if not dotted(node.left).endswith(".returncode"):
        return False
    return any(isinstance(op, ast.Eq) for op in node.ops) and any(
        isinstance(comp, ast.Constant) and comp.value == 0 for comp in node.comparators
    )


def compare_uses_returncode_list(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if not dotted(node.left).endswith(".returncode"):
        return False
    if not any(isinstance(op, ast.In) for op in node.ops):
        return False
    for comp in node.comparators:
        if not isinstance(comp, (ast.List, ast.Tuple, ast.Set)):
            continue
        constants = [item.value for item in comp.elts if isinstance(item, ast.Constant)]
        if len(constants) != len(comp.elts):
            return True
        if any(value != 0 for value in constants):
            return True
    return False


def is_literal_true(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def boolop_contains_true(node: ast.AST) -> bool:
    return isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(
        is_literal_true(value) or boolop_contains_true(value) for value in node.values
    )


def is_string_container(node: ast.AST) -> bool:
    name = dotted(node)
    if name.endswith((".stdout", ".stderr")):
        return True
    if name in {"stdout", "stderr", "combined"}:
        return True
    if isinstance(node, ast.BinOp):
        return is_string_container(node.left) or is_string_container(node.right)
    return False


def is_short_substring(node: ast.AST, short_param_names: set[str]) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if not any(isinstance(op, ast.In) for op in node.ops):
        return False
    if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
        is_short = len(node.left.value) < 15
    elif isinstance(node.left, ast.Name) and node.left.id in short_param_names:
        is_short = True
    else:
        return False
    if not is_short:
        return False
    return any(is_string_container(comp) for comp in node.comparators)


def is_len_check(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if isinstance(node.left, ast.Call) and dotted(node.left.func) == "len":
        return True
    return any(isinstance(c, ast.Call) and dotted(c.func) == "len" for c in node.comparators)


def is_len_greater_check(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Call)
        and dotted(node.left.func) == "len"
        and any(isinstance(op, ast.Gt) for op in node.ops)
    )


def is_len_ge_check(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Call)
        and dotted(node.left.func) == "len"
        and any(isinstance(op, ast.GtE) for op in node.ops)
    )


def is_exists_check(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        name = dotted(node.func)
        return name.split(".")[-1] in EXISTS_CALL_NAMES
    return False


def is_isdigit_check(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and dotted(node.func).endswith(".isdigit")


def is_weak_assertion(expr: ast.AST) -> bool:
    return is_returncode_check(expr) or is_len_check(expr) or is_isdigit_check(expr)


def is_negative_assertion(expr: ast.AST) -> bool:
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return True
    if isinstance(expr, ast.Compare):
        return all(isinstance(op, (ast.NotEq, ast.NotIn, ast.IsNot)) for op in expr.ops)
    return False


def body_has_asserts(nodes: list[ast.stmt]) -> bool:
    return any(isinstance(child, ast.Assert) for node in nodes for child in ast.walk(node))


def body_is_pass_only(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return len(body) == 1 and isinstance(body[0], ast.Pass)


def has_pre_loop_length_guard(node: ast.FunctionDef | ast.AsyncFunctionDef, loop: ast.For) -> bool:
    for stmt in node.body:
        if stmt is loop:
            return False
        if any(isinstance(child, ast.Assert) and is_len_check(child.test) for child in ast.walk(stmt)):
            return True
    return False


def has_non_empty_guard_before(node: ast.FunctionDef | ast.AsyncFunctionDef, target: ast.AST) -> bool:
    for stmt in node.body:
        if stmt is target:
            return False
        for child in ast.walk(stmt):
            if not isinstance(child, ast.Assert):
                continue
            if is_len_check(child.test):
                return True
            if isinstance(child.test, ast.Name):
                return True
    return False


def contains_any_all(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Call) and dotted(child.func) in {"any", "all"}
        for child in ast.walk(node)
    )


def contains_disjunction(node: ast.AST) -> bool:
    return any(isinstance(child, ast.BoolOp) and isinstance(child.op, ast.Or) for child in ast.walk(node))


def contains_content_assertion(asserts: list[ast.Assert]) -> bool:
    for item in asserts:
        if is_exists_check(item.test):
            continue
        if is_returncode_check(item.test):
            continue
        if is_len_check(item.test):
            continue
        return True
    return False


def test_docstring(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    return ast.get_docstring(node) or ""


def catches_too_short(docstring: str) -> bool:
    match = re.search(r"CATCHES\s*:?\s*(.*)", docstring, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return True
    return len(match.group(1).strip()) < 15


def writes_own_golden(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        call_text = ast.unparse(child).lower()
        if "golden" not in call_text and "expected" not in call_text:
            continue
        if dotted(child.func).split(".")[-1] in {"write", "write_text", "write_bytes", "open"}:
            return True
        if dotted(child.func) == "open":
            return True
    return False


def golden_docstring_flags(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict]:
    docstring = test_docstring(node)
    if "golden" not in docstring.lower():
        return []
    body_text = "\n".join(ast.unparse(stmt) for stmt in node.body[1:])
    flags: list[dict] = []
    golden_words = {
        word.strip("`'\".,;:()[]{}")
        for word in re.split(r"\s+", docstring)
        if "golden" in word.lower()
    }
    if golden_words and not any(word in body_text for word in golden_words):
        flags.append({"severity": "HIGH", "id": "golden_docstring", "line": node.lineno})
    if not any(isinstance(child, ast.Compare) and any(isinstance(op, ast.Eq) for op in child.ops) for child in ast.walk(node)):
        flags.append({"severity": "HIGH", "id": "golden_no_equality", "line": node.lineno})
    return flags


def parametrize_short_string_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    short_names: set[str] = set()
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if dotted(decorator.func) != "pytest.mark.parametrize":
            continue
        if len(decorator.args) < 2:
            continue
        raw_names = decorator.args[0]
        names: list[str] = []
        if isinstance(raw_names, ast.Constant) and isinstance(raw_names.value, str):
            names = [name.strip() for name in raw_names.value.split(",")]
        elif isinstance(raw_names, (ast.Tuple, ast.List)):
            names = [
                item.value
                for item in raw_names.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
        raw_values = decorator.args[1]
        if not names or not isinstance(raw_values, (ast.Tuple, ast.List)):
            continue
        for case in raw_values.elts:
            values = case.elts if isinstance(case, (ast.Tuple, ast.List)) else [case]
            for name, value in zip(names, values, strict=False):
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and len(value.value) < 15:
                    short_names.add(name)
    return short_names


def assertion_flags(expr: ast.AST, short_param_names: set[str]) -> list[dict]:
    flags: list[dict] = []
    if is_literal_true(expr) or boolop_contains_true(expr):
        flags.append({"severity": "HIGH", "id": "trivially_true"})
    if compare_uses_returncode_list(expr):
        flags.append({"severity": "HIGH", "id": "returncode_in_list"})
    if contains_disjunction(expr):
        flags.append({"severity": "HIGH", "id": "assertion_disjunction"})
    if is_short_substring(expr, short_param_names):
        flags.append({"severity": "HIGH", "id": "short_substring"})
    if is_len_ge_check(expr):
        flags.append({"severity": "MED", "id": "relative_length_assertion"})
    return flags


def lint_tests(tests_dir: Path) -> list[dict]:
    findings: list[dict] = []
    for path in sorted(tests_dir.glob("test*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue

            def add(severity: str, rule_id: str, line: int) -> None:
                findings.append(
                    {
                        "severity": severity,
                        "id": rule_id,
                        "file": str(path),
                        "test": node.name,
                        "line": line,
                    }
                )

            asserts = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
            docstring = test_docstring(node)
            short_param_names = parametrize_short_string_names(node)

            if body_is_pass_only(node):
                add("HIGH", "pass_body", node.lineno)
            if not asserts:
                add("HIGH", "no_assertions", node.lineno)
            if catches_too_short(docstring):
                add("LOW", "catches", node.lineno)
            if writes_own_golden(node):
                add("HIGH", "golden_written_in_test", node.lineno)
            for flag in golden_docstring_flags(node):
                add(flag["severity"], flag["id"], flag["line"])

            for child in ast.walk(node):
                if isinstance(child, ast.If):
                    body_asserts = body_has_asserts(child.body)
                    else_asserts = body_has_asserts(child.orelse)
                    if body_asserts and not child.orelse:
                        add("HIGH", "if_no_else", child.lineno)
                    if body_asserts and else_asserts:
                        add("HIGH", "if_else_both_assert", child.lineno)
                if isinstance(child, ast.Try):
                    for handler in child.handlers:
                        if handler.body and all(isinstance(stmt, ast.Pass) for stmt in handler.body):
                            add("HIGH", "try_except_swallow", handler.lineno)
                if isinstance(child, ast.For) and body_has_asserts(child.body):
                    if not has_pre_loop_length_guard(node, child):
                        add("MED", "for_no_guard", child.lineno)

            if not asserts:
                continue

            for assert_node in asserts:
                flags = assertion_flags(assert_node.test, short_param_names)
                for flag in flags:
                    add(flag["severity"], flag["id"], assert_node.lineno)
                if contains_any_all(assert_node.test) and not has_non_empty_guard_before(node, assert_node):
                    add("MED", "any_all_no_guard", assert_node.lineno)

            if len(asserts) == 1:
                only = asserts[0].test
                if compare_uses_returncode_zero(only):
                    add("HIGH", "sole_returncode", asserts[0].lineno)
                if is_len_greater_check(only):
                    add("MED", "weak_sole_assertion", asserts[0].lineno)

            if all(is_weak_assertion(assert_node.test) for assert_node in asserts):
                add("HIGH", "all_assertions_weak", node.lineno)
            if all(is_negative_assertion(assert_node.test) for assert_node in asserts):
                add("MED", "only_negative_assertions", node.lineno)
            if any(is_exists_check(assert_node.test) for assert_node in asserts) and not contains_content_assertion(asserts):
                add("MED", "file_exists_no_content", node.lineno)
    return findings


def run_pytest(eval_dir: Path, executable: Path, out_xml: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env["EXECUTABLE"] = str(executable)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        str(eval_dir / "tests"),
        "-q",
        "--tb=short",
        "--junitxml",
        str(out_xml),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def parse_xml(xml_path: Path) -> dict[str, list[str]]:
    root = ET.parse(xml_path).getroot()
    passed: list[str] = []
    failed: list[str] = []
    for case in root.iter("testcase"):
        name = f"{case.attrib.get('classname', '')}.{case.attrib.get('name', '')}".strip(".")
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(name)
        else:
            passed.append(name)
    return {"passed": passed, "failed": failed}


def make_dummy(path: Path) -> None:
    path.write_text("#!/usr/bin/env sh\nexit 0\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    static_findings = lint_tests(args.eval / "tests")

    gold_xml = args.out / "gold_results.xml"
    gold_rc, gold_output = run_pytest(args.eval, args.executable, gold_xml)
    gold_results = parse_xml(gold_xml) if gold_xml.exists() else {"passed": [], "failed": []}

    with tempfile.TemporaryDirectory() as tmp:
        dummy = Path(tmp) / "dummy_executable"
        make_dummy(dummy)
        dummy_xml = args.out / "dummy_results.xml"
        dummy_rc, dummy_output = run_pytest(args.eval, dummy, dummy_xml)
        dummy_results = parse_xml(dummy_xml) if dummy_xml.exists() else {"passed": [], "failed": []}

    blocking_static = [f for f in static_findings if f["severity"] in {"HIGH", "MED"}]
    report = {
        "static_check_catalog": STATIC_CHECK_CATALOG,
        "dynamic_check_catalog": DYNAMIC_CHECK_CATALOG,
        "static_findings": static_findings,
        "blocking_static_findings": blocking_static,
        "gold": {
            "returncode": gold_rc,
            "passed": len(gold_results["passed"]),
            "failed": len(gold_results["failed"]),
            "failed_tests": gold_results["failed"][:100],
            "output_tail": gold_output[-4000:],
        },
        "dummy": {
            "returncode": dummy_rc,
            "passed": len(dummy_results["passed"]),
            "failed": len(dummy_results["failed"]),
            "passed_tests": dummy_results["passed"][:100],
            "output_tail": dummy_output[-4000:],
        },
    }
    (args.out / "quality_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

    if blocking_static or gold_results["failed"] or dummy_results["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
