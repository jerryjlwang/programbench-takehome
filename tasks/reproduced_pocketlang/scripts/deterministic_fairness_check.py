#!/usr/bin/env python3
"""Deterministic fairness audit for the PocketLang task recreation."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "tasks" / "reproduced_pocketlang"
TASK_ENV = TASK / "task_env"
EVAL = TASK / "tests_generated" / "eval"
TESTS = EVAL / "tests"
GENERATED_CASES = EVAL / "cases" / "generated_cases.json"
HARVESTED_CASES = EVAL / "cases" / "harvested_cases.json"
QUALITY = TASK / "reports" / "quality_generated" / "quality_report.json"
HARVESTED_COVERAGE = TASK / "reports" / "coverage_harvested" / "coverage_summary.json"
GENERATED_COVERAGE = TASK / "reports" / "coverage_generated" / "coverage_summary.json"
USAGE = TASK_ENV / "docs" / "USAGE.md"
REPORT_DIR = TASK / "reports" / "qc"

EXPECTED_TASK_ENV_FILES = {
    "compile.sh",
    "docs/USAGE.md",
    "docs/help.txt",
    "executable",
}

FORBIDDEN_TASK_ENV_PARTS = {
    ".git",
    "_src",
    "tests_generated",
    "tests_harvested",
    "reports",
    "logs",
    "gold",
    "cases",
    "fixtures",
}

FORBIDDEN_TEXT_PATTERNS = [
    r"/Users/",
    r"programbench-takehome",
    r"tasks/reproduced_pocketlang/_src",
    r"tasks/reproduced_pocketlang/gold",
    r"github\.com/ThakeeNathees/pocketlang",
    r"cc73ca61b113d48ee130d837a7a8b145e41de5ce",
]

REQUIRED_DOC_TERMS = [
    "stdout",
    "stderr",
    "exit status",
    "-c",
    "--cmd",
    "script file",
    "imports",
    "modules",
    "classes",
    "closures",
    "fibers",
    "json",
    "path",
    "math",
    "io",
    "os",
    "time",
    "types",
    "bytebuffer",
    "vector",
    "filesystem",
    "environment",
    "runtime",
    "compiler",
    "normal cli execution",
    "no original pocketlang source tree",
    "only the produced `./executable`",
    "self-contained",
]

ALLOWED_TEST_IMPORTS = {"json", "pathlib", "pytest", "re"}


@dataclass
class Check:
    id: str
    status: str
    evidence: str


def rel(path: Path) -> str:
    return str(path.relative_to(TASK))


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def add(checks: list[Check], check_id: str, status: str, evidence: str) -> None:
    checks.append(Check(check_id, status, evidence))


def text_findings(paths: list[Path], patterns: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    compiled = [(pattern, re.compile(pattern, re.I)) for pattern in patterns]
    for path in paths:
        text = read_text(path)
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern, regex in compiled:
                if regex.search(line):
                    findings.append(
                        {
                            "file": rel(path),
                            "line": line_no,
                            "pattern": pattern,
                            "text": line[:240],
                        }
                    )
    return findings


def python_test_files() -> list[Path]:
    return sorted(TESTS.glob("test_*.py"))


def audit_task_env(checks: list[Check]) -> None:
    files = {
        str(path.relative_to(TASK_ENV))
        for path in TASK_ENV.rglob("*")
        if path.is_file()
    }
    unexpected = sorted(files - EXPECTED_TASK_ENV_FILES)
    missing = sorted(EXPECTED_TASK_ENV_FILES - files)
    forbidden = sorted(
        str(path.relative_to(TASK_ENV))
        for path in TASK_ENV.rglob("*")
        if any(part in FORBIDDEN_TASK_ENV_PARTS for part in path.relative_to(TASK_ENV).parts)
    )
    ok = not unexpected and not missing and not forbidden
    add(
        checks,
        "task_env_contains_only_solver_facing_files",
        "pass" if ok else "fail",
        "task_env contains only executable, compile.sh, and docs."
        if ok
        else json.dumps({"missing": missing, "unexpected": unexpected, "forbidden": forbidden}, indent=2),
    )


def audit_docs(checks: list[Check]) -> None:
    usage = re.sub(r"\s+", " ", read_text(USAGE).lower())
    missing = [term for term in REQUIRED_DOC_TERMS if term not in usage]
    add(
        checks,
        "solver_docs_cover_hidden_behavior_families",
        "pass" if not missing else "fail",
        "USAGE.md names the CLI, language, standard-library, error, and runtime boundaries covered by hidden tests."
        if not missing
        else "USAGE.md missing terms: " + ", ".join(missing),
    )

    forbidden_tools = [
        "strings",
        "objdump",
        "readelf",
        "xxd",
        "hexdump",
        "strace",
        "ltrace",
        "gdb",
        "sha256sum",
        "open(..., \"rb\")",
        "path.read_bytes()",
    ]
    missing_tools = [term for term in forbidden_tools if term.lower() not in usage]
    add(
        checks,
        "solver_docs_explain_black_box_observation_boundary",
        "pass" if not missing_tools else "fail",
        "USAGE.md forbids binary/source shortcuts and limits observation to CLI behavior."
        if not missing_tools
        else "USAGE.md missing oracle-guardrail terms: " + ", ".join(missing_tools),
    )


def audit_pytest_wrappers(checks: list[Check]) -> None:
    files = python_test_files()
    conftest = TESTS / "conftest.py"
    leaks = text_findings(files + [conftest], FORBIDDEN_TEXT_PATTERNS)
    add(
        checks,
        "pytest_wrappers_have_no_workspace_source_leaks",
        "pass" if not leaks else "fail",
        "No local workspace, source, gold, repository URL, or commit leaks in pytest wrappers."
        if not leaks
        else json.dumps(leaks[:20], indent=2),
    )

    bad_imports: list[dict[str, Any]] = []
    bad_calls: list[dict[str, Any]] = []
    for path in files:
        tree = ast.parse(read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in ALLOWED_TEST_IMPORTS:
                        bad_imports.append({"file": rel(path), "import": alias.name})
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root not in ALLOWED_TEST_IMPORTS:
                    bad_imports.append({"file": rel(path), "import": node.module})
            elif isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in {"subprocess", "Popen", "run", "check_output", "system"}:
                    bad_calls.append({"file": rel(path), "call": name, "line": getattr(node, "lineno", None)})

    add(
        checks,
        "pytest_tests_route_behavior_through_run_pocket",
        "pass" if not bad_imports and not bad_calls else "fail",
        "Test wrappers avoid direct subprocess/source inspection and route behavior through the run_pocket fixture."
        if not bad_imports and not bad_calls
        else json.dumps({"bad_imports": bad_imports, "bad_calls": bad_calls}, indent=2),
    )

    joined = "\n".join(read_text(path) for path in files)
    exact_terms = [
        'result.returncode == case["returncode"]',
        '== case["stdout"]',
        '== case["stderr"]',
        "version.stdout ==",
        "help_result.stdout ==",
    ]
    missing = [term for term in exact_terms if term not in joined]
    add(
        checks,
        "pytest_assertions_compare_exact_observable_behavior",
        "pass" if not missing else "fail",
        "Wrappers assert exact return code, stdout, and stderr instead of broad substring checks."
        if not missing
        else "Missing exact assertion terms: " + ", ".join(missing),
    )


def audit_case_manifest(checks: list[Check]) -> dict[str, Any]:
    generated = json.loads(GENERATED_CASES.read_text())
    harvested = json.loads(HARVESTED_CASES.read_text())
    generated_ids = [case.get("id") for case in generated]
    duplicate_ids = sorted(case_id for case_id, count in Counter(generated_ids).items() if count > 1)
    schema_errors: list[str] = []
    path_leaks: list[str] = []

    for manifest_name, cases in (("generated", generated), ("harvested", harvested)):
        for index, case in enumerate(cases):
            for key in ("id", "args", "returncode", "stdout", "stderr"):
                if key not in case:
                    schema_errors.append(f"{manifest_name} case {index} missing {key}")
            if not isinstance(case.get("args"), list):
                schema_errors.append(f"{manifest_name} case {case.get('id', index)} args is not a list")
            joined = json.dumps(case)
            if re.search(r"/Users/|programbench-takehome|tasks/reproduced_pocketlang|_src|gold/", joined):
                path_leaks.append(f"{manifest_name} case {case.get('id', index)} leaks local/source path")

    nonempty_generated = [
        case for case in generated if case.get("stdout") or case.get("stderr") or case.get("returncode") != 0
    ]
    ok = (
        not schema_errors
        and not path_leaks
        and not duplicate_ids
        and len(generated) >= 224
        and len(nonempty_generated) == len(generated)
    )
    add(
        checks,
        "case_manifests_are_exact_self_contained_and_large_enough",
        "pass" if ok else "fail",
        f"{len(harvested)} harvested cases and {len(generated)} generated cases have exact outputs, unique ids, no local path leaks, and non-empty observable behavior."
        if ok
        else json.dumps(
            {
                "schema_errors": schema_errors[:20],
                "path_leaks": path_leaks[:20],
                "duplicate_ids": duplicate_ids,
                "generated_count": len(generated),
                "nonempty_generated": len(nonempty_generated),
            },
            indent=2,
        ),
    )
    return {"harvested_case_count": len(harvested), "generated_case_count": len(generated)}


def audit_quality_and_coverage(checks: list[Check]) -> dict[str, Any]:
    quality = json.loads(QUALITY.read_text())
    gold = quality.get("gold", {})
    dummy = quality.get("dummy", {})
    quality_ok = (
        not quality.get("blocking_static_findings")
        and gold.get("failed") == 0
        and gold.get("passed", 0) > 0
        and dummy.get("passed") == 0
        and dummy.get("failed", 0) == gold.get("passed", -1)
    )
    add(
        checks,
        "quality_gate_gold_passes_dummy_rejected",
        "pass" if quality_ok else "fail",
        f"Gold passed {gold.get('passed')} tests with 0 failures; dummy passed {dummy.get('passed')} and failed {dummy.get('failed')}."
        if quality_ok
        else json.dumps({"blocking_static_findings": quality.get("blocking_static_findings"), "gold": gold, "dummy": dummy}, indent=2),
    )

    harvested = json.loads(HARVESTED_COVERAGE.read_text())
    generated = json.loads(GENERATED_COVERAGE.read_text())
    coverage_ok = (
        generated.get("line_percent", 0) >= harvested.get("line_percent", 0)
        and generated.get("branch_percent", 0) >= harvested.get("branch_percent", 0)
    )
    add(
        checks,
        "generated_suite_preserves_or_improves_coverage",
        "pass" if coverage_ok else "fail",
        f"Harvested coverage {harvested.get('line_percent')}% line/{harvested.get('branch_percent')}% branch; generated coverage {generated.get('line_percent')}% line/{generated.get('branch_percent')}% branch."
        if coverage_ok
        else json.dumps({"harvested": harvested, "generated": generated}, indent=2),
    )
    return {
        "gold_passed": gold.get("passed"),
        "dummy_passed": dummy.get("passed"),
        "harvested_line_percent": harvested.get("line_percent"),
        "harvested_branch_percent": harvested.get("branch_percent"),
        "generated_line_percent": generated.get("line_percent"),
        "generated_branch_percent": generated.get("branch_percent"),
    }


def write_reports(checks: list[Check], metrics: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    passed = sum(check.status == "pass" for check in checks)
    failed = sum(check.status != "pass" for check in checks)
    report = {
        "task": "reproduced_pocketlang",
        "status": "pass" if failed == 0 else "fail",
        "passed": passed,
        "failed": failed,
        "metrics": metrics,
        "checks": [asdict(check) for check in checks],
    }
    (REPORT_DIR / "deterministic_fairness_report.json").write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# PocketLang Deterministic Fairness Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Checks: {passed} passed, {failed} failed",
        f"- Harvested cases: {metrics.get('harvested_case_count')}",
        f"- Generated cases: {metrics.get('generated_case_count')}",
        f"- Generated coverage: {metrics.get('generated_line_percent')}% line, {metrics.get('generated_branch_percent')}% branch",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        lines.append(f"- `{check.status}` `{check.id}`: {check.evidence}")
    (REPORT_DIR / "deterministic_fairness_report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))


def main() -> int:
    checks: list[Check] = []
    metrics: dict[str, Any] = {}
    audit_task_env(checks)
    audit_docs(checks)
    audit_pytest_wrappers(checks)
    metrics.update(audit_case_manifest(checks))
    metrics.update(audit_quality_and_coverage(checks))
    write_reports(checks, metrics)
    return 0 if all(check.status == "pass" for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
