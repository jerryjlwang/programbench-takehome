#!/usr/bin/env python3
"""Deterministic fairness audit for the Lua generated evaluation suite."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "tasks" / "reproduced_lua"
EVAL = TASK / "tests_generated" / "eval"
TESTS = EVAL / "tests"
CASES = EVAL / "cases" / "generated_cases.json"
FIXTURES = EVAL / "fixtures" / "testes"
USAGE = TASK / "task_env" / "docs" / "USAGE.md"
BUILD_IMAGE = TASK / "scripts" / "build_miniswe_cleanroom_image.sh"
REPORT_DIR = TASK / "reports" / "qc"

REQUIRED_DOC_TERMS = [
    "arithmetic",
    "bitwise",
    "strings",
    "pattern matching",
    "utf-8",
    "tables",
    "metatables",
    "closures",
    "upvalues",
    "varargs",
    "goto",
    "control flow",
    "coroutines",
    "garbage collection",
    "finalizers",
    "errors",
    "debug library",
    "package",
    "dynamic library",
    "binary chunks",
    "bytecode",
    "math",
    "sorting",
    "io",
    "os helpers",
    "warnings",
    "environment variables",
    "stdin",
    "interactive repl",
]

PY_TEST_FORBIDDEN = [
    r"tasks/reproduced_lua/_src",
    r"tasks/reproduced_lua/gold",
    r"/Users/",
    r"programbench-takehome",
    r"github\.com/lua/lua",
    r"c6b484823806e08e1756b1a6066a3ace6f080fae",
]

FIXTURE_FORBIDDEN = [
    r"/Users/",
    r"programbench-takehome",
    r"tasks/reproduced_lua/_src",
    r"tasks/reproduced_lua/gold",
]

NATIVE_FIXTURE_NAMES = {".c", ".h", ".o", ".so", ".dylib", ".a"}
ALLOWED_TEST_IMPORTS = {"json", "pathlib", "pytest"}


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


def grep_patterns(paths: list[Path], patterns: list[str]) -> list[dict[str, Any]]:
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


def fixture_files() -> list[Path]:
    return sorted(path for path in FIXTURES.rglob("*") if path.is_file())


def audit_python_wrappers(checks: list[Check]) -> None:
    files = python_test_files()
    leaks = grep_patterns(files + [TESTS / "conftest.py"], PY_TEST_FORBIDDEN)
    add(
        checks,
        "python_wrappers_have_no_workspace_or_source_leaks",
        "pass" if not leaks else "fail",
        "No forbidden workspace/source strings in pytest wrappers."
        if not leaks
        else json.dumps(leaks[:10], indent=2),
    )

    bad_imports: list[dict[str, Any]] = []
    bad_calls: list[dict[str, Any]] = []
    for path in files:
        tree = ast.parse(read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".")[0]
                    if root_name not in ALLOWED_TEST_IMPORTS:
                        bad_imports.append({"file": rel(path), "import": alias.name})
            elif isinstance(node, ast.ImportFrom):
                root_name = (node.module or "").split(".")[0]
                if root_name not in ALLOWED_TEST_IMPORTS:
                    bad_imports.append({"file": rel(path), "import": node.module})
            elif isinstance(node, ast.Call):
                call_name = ""
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                if call_name in {"subprocess", "Popen", "run", "check_output", "system"}:
                    bad_calls.append(
                        {"file": rel(path), "call": call_name, "line": getattr(node, "lineno", None)}
                    )

    add(
        checks,
        "pytest_tests_use_run_lua_black_box_fixture",
        "pass" if not bad_imports and not bad_calls else "fail",
        "Test wrappers avoid direct subprocess/source inspection and route behavior through run_lua."
        if not bad_imports and not bad_calls
        else json.dumps({"bad_imports": bad_imports, "bad_calls": bad_calls}, indent=2),
    )


def audit_generated_cases(checks: list[Check]) -> dict[str, Any]:
    cases = json.loads(CASES.read_text())
    ids = [case.get("id") for case in cases]
    duplicate_ids = sorted(case_id for case_id, count in Counter(ids).items() if count > 1)
    schema_errors: list[str] = []
    for index, case in enumerate(cases):
        for key in ("id", "args", "stdin", "returncode", "stdout", "stderr"):
            if key not in case:
                schema_errors.append(f"case {index} missing {key}")
        if not isinstance(case.get("args"), list):
            schema_errors.append(f"case {index} args is not a list")
        elif case["args"][:1] != ["-e"]:
            schema_errors.append(f"{case.get('id', index)} does not use -e")
        if case.get("env"):
            schema_errors.append(f"{case.get('id', index)} has custom env {case.get('env')}")
        joined = json.dumps(case)
        if re.search(r"/Users/|programbench-takehome|tasks/reproduced_lua|_src/lua|gold/lua", joined):
            schema_errors.append(f"{case.get('id', index)} leaks workspace/source path")

    add(
        checks,
        "generated_cases_are_self_contained_eval_invocations",
        "pass" if not schema_errors and not duplicate_ids else "fail",
        f"{len(cases)} generated cases use -e with explicit stdout/stderr/returncode and no path/env leaks."
        if not schema_errors and not duplicate_ids
        else json.dumps({"schema_errors": schema_errors[:20], "duplicate_ids": duplicate_ids}, indent=2),
    )
    return {"generated_case_count": len(cases)}


def audit_fixture_surface(checks: list[Check]) -> dict[str, Any]:
    files = fixture_files()
    leaks = grep_patterns(files, FIXTURE_FORBIDDEN)
    add(
        checks,
        "fixtures_have_no_workspace_absolute_path_leaks",
        "pass" if not leaks else "fail",
        "No local workspace/gold/_src absolute path leaks in hidden fixture files."
        if not leaks
        else json.dumps(leaks[:20], indent=2),
    )

    test_text = "\n".join(read_text(path) for path in python_test_files())
    native_files = [path for path in files if path.suffix in NATIVE_FIXTURE_NAMES or path.name == "makefile"]
    native_referenced = [
        path for path in native_files if path.name in test_text or str(path.relative_to(FIXTURES)) in test_text
    ]
    native_build_terms = re.findall(r"\b(?:gcc|cc|clang|make)\b|libs/makefile", test_text)
    add(
        checks,
        "native_source_fixtures_are_not_compiled_by_hidden_tests",
        "pass" if not native_referenced and not native_build_terms else "fail",
        f"{len(native_files)} native fixture files exist but pytest wrappers do not compile or name them."
        if not native_referenced and not native_build_terms
        else json.dumps(
            {
                "native_referenced": [rel(path) for path in native_referenced],
                "native_build_terms": native_build_terms,
            },
            indent=2,
        ),
    )

    upstream_wrapper = read_text(TESTS / "test_upstream_user_suite.py")
    all_lua = read_text(FIXTURES / "all.lua")
    user_mode_ok = "[\"-e\", \"_U=true\", \"all.lua\"]" in upstream_wrapper
    internals_disabled = "if usertests then" in all_lua and "T = nil" in all_lua
    add(
        checks,
        "upstream_user_suite_runs_user_mode_without_internal_c_api",
        "pass" if user_mode_ok and internals_disabled else "fail",
        "The upstream suite is invoked with _U=true and all.lua disables internal T/C API checks."
        if user_mode_ok and internals_disabled
        else "Missing _U=true invocation or all.lua user-mode internal-test guard.",
    )

    lua_inputs = sorted(set(re.findall(r"(?:old)?dofile\('([^']+\.lua)'", all_lua)))
    add(
        checks,
        "upstream_fixtures_are_executable_inputs_not_candidate_introspection",
        "pass",
        f"{len(lua_inputs)} upstream Lua scripts are passed to the executable under cwd, not used to inspect candidate source.",
    )
    return {"upstream_user_suite_file_count": len(lua_inputs), "native_fixture_count": len(native_files)}


def audit_docs_surface(checks: list[Check]) -> None:
    usage = read_text(USAGE).lower()
    missing = [term for term in REQUIRED_DOC_TERMS if term.lower() not in usage]
    add(
        checks,
        "solver_docs_name_hidden_behavior_families",
        "pass" if not missing else "fail",
        "USAGE.md names the CLI, language, runtime, and standard-library behavior families covered by hidden tests."
        if not missing
        else f"USAGE.md is missing behavior-family terms: {', '.join(missing)}",
    )

    required_guardrails = ["do not inspect", "open(..., \"rb\")", "normal cli", "no original lua source tree"]
    missing_guardrails = [term for term in required_guardrails if term not in usage]
    add(
        checks,
        "solver_docs_explain_allowed_observation_boundary",
        "pass" if not missing_guardrails else "fail",
        "USAGE.md explains black-box CLI observation and forbids binary/source shortcuts."
        if not missing_guardrails
        else f"USAGE.md missing guardrail terms: {', '.join(missing_guardrails)}",
    )

    required_runtime_terms = ["only the produced `./executable`", "self-contained", "other submitted files are not available"]
    missing_runtime_terms = [term for term in required_runtime_terms if term not in usage]
    add(
        checks,
        "solver_docs_explain_self_contained_runtime",
        "pass" if not missing_runtime_terms else "fail",
        "USAGE.md states that hidden scoring runs only the compiled executable and requires a self-contained runtime."
        if not missing_runtime_terms
        else f"USAGE.md missing self-contained runtime terms: {', '.join(missing_runtime_terms)}",
    )


def audit_cleanroom_image(checks: list[Check]) -> None:
    script = read_text(BUILD_IMAGE)
    runner = read_text(TASK / "scripts" / "run_miniswe_lua.py")
    compile_template = read_text(TASK / "task_env" / "compile.sh")
    conditions = [
        "chown root:agent /workspace" in script,
        "chmod 1775 /workspace" in script,
        "chown root:root /workspace/executable" in script,
        "chmod 0111 /workspace/executable" in script,
        "out=candidate" in compile_template,
        "protected oracle detected" in compile_template,
        "strip_prebuilt_executable_from_submission" in runner,
        "--network" in runner,
        "none" in runner,
    ]
    add(
        checks,
        "cleanroom_image_executes_oracle_without_read_permission",
        "pass" if all(conditions) else "fail",
        "Cleanroom image root-owns the oracle, grants execute-only permission, preserves it during development builds via ./candidate, strips prebuilt executables from submissions, and solve runs with network disabled."
        if all(conditions)
        else "Missing execute-only oracle permission, candidate-build preservation, submission stripping, or network-disabled solve configuration.",
    )


def audit_runner_budget_guards(checks: list[Check]) -> None:
    runner = read_text(TASK / "scripts" / "run_miniswe_lua.py")
    wrapper = read_text(TASK / "scripts" / "run_miniswe_lua.sh")
    conditions = [
        "DEFAULT_MAX_TOKENS = 2048" in runner,
        'DEFAULT_REASONING_EFFORT = "none"' in runner,
        "DEFAULT_OBSERVATION_CHAR_LIMIT = 4000" in runner,
        "DEFAULT_STEP_LIMIT = 1000" in runner,
        "DEFAULT_WALL_TIME_LIMIT_SECONDS = 7200" in runner,
        '"max_tokens": args.max_tokens' in runner,
        '"reasoning_effort": args.reasoning_effort' in runner,
        '"tool_choice"' in runner,
        "parse_tool_choice" in runner,
        '"name": "bash"' in runner,
        "format_error_template()" in runner,
        "normalize_instance_template" in runner,
        "MAX_CONSECUTIVE_IDENTICAL_COMMANDS = 5" in runner,
        "ORACLE_ONLY_STAGNATION_LIMIT = 200" in runner,
        "NONPRODUCTIVE_COMMAND_LIMIT = 80" in runner,
        "OBSERVATION_PHASE_COMMAND_LIMIT = 60" in runner,
        "BUILD_PHASE_COMMAND_LIMIT = 140" in runner,
        "MIN_IMPLEMENTATION_BYTES = 2000" in runner,
        "SOURCE_WRITE_COMMAND_PATTERNS" in runner,
        "workspace_has_nontrivial_implementation" in runner,
        "submission rejected before scoring" in runner,
        "observation phase exceeded" in runner,
        "build phase exceeded" in runner,
        "same command repeated" in runner,
        "oracle commands since the last source/build action" in runner,
        "nonproductive commands since the last source/build action" in runner,
        "network probing or downloading is disallowed" in runner,
        "package manager and package-cache probing is disallowed" in runner,
        "searching system directories for source or runtimes is disallowed" in runner,
        "git init" in runner,
        "scratchpad" in runner,
        "self-contained executable" in runner,
        "install_gemini_context_guards(model)" in runner,
        "install_environment_command_guards(env)" in runner,
        "MINISWE_MAX_TOKENS" in wrapper,
        "MINISWE_REASONING_EFFORT" in wrapper,
        "MINISWE_TOOL_CHOICE" in wrapper,
        'MINISWE_TOOL_CHOICE="${MINISWE_TOOL_CHOICE:-bash}"' in wrapper,
        "MINISWE_OBSERVATION_CHAR_LIMIT" in wrapper,
        "MINISWE_STEP_LIMIT" in wrapper,
        "MINISWE_WALL_TIME_LIMIT_SECONDS" in wrapper,
    ]
    add(
        checks,
        "solve_runner_enforces_context_budget_and_oracle_command_guards",
        "pass" if all(conditions) else "fail",
        "Lua mini-SWE runner applies token/reasoning/observation caps, forces the named bash tool by default, strips Gemini thought metadata, removes commit instructions, enforces source-first/build phases, rejects placeholder submissions, and blocks oracle-inspection/scratchpad/git/network/package/system-search/repeated-command stagnation."
        if all(conditions)
        else "Lua mini-SWE runner is missing one or more token/reasoning/context/tool-choice/source-first/oracle/scratchpad/git/network/package/system-search/stagnation guard settings.",
    )


def audit_determinism(checks: list[Check]) -> None:
    conftest = read_text(TESTS / "conftest.py")
    upstream = read_text(TESTS / "test_upstream_user_suite.py")
    conditions = [
        "LC_ALL" in conftest and "C" in conftest,
        "TZ" in conftest and "UTC" in conftest,
        "random seeds:" in upstream,
        "final OK !!!" in upstream,
    ]
    add(
        checks,
        "test_harness_normalizes_environment_and_avoids_timing_or_seed_exactness",
        "pass" if all(conditions) else "fail",
        "Harness sets LC_ALL=C/TZ=UTC and checks suite completion without pinning random seed or timing values."
        if all(conditions)
        else "One or more deterministic harness normalizations is missing.",
    )


def write_reports(payload: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / "deterministic_fairness_report.json"
    md_path = REPORT_DIR / "deterministic_fairness_report.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Lua Deterministic Fairness Report",
        "",
        f"- Verdict: `{payload['verdict']}`",
        f"- Blocking failures: `{payload['blocking_failures']}`",
        f"- Warnings: `{payload['warnings']}`",
        f"- Generated cases: `{payload['counts']['generated_case_count']}`",
        f"- Upstream Lua input scripts: `{payload['counts']['upstream_user_suite_file_count']}`",
        f"- Native fixture files not compiled by tests: `{payload['counts']['native_fixture_count']}`",
        "",
        "## Checks",
    ]
    for check in payload["checks"]:
        lines.extend(["", f"### {check['id']}", "", f"- Status: `{check['status']}`", f"- Evidence: {check['evidence']}"])
    if payload["notes"]:
        lines.extend(["", "## Notes"])
        for note in payload["notes"]:
            lines.append(f"- {note}")
    md_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    checks: list[Check] = []
    counts: dict[str, Any] = {}
    audit_python_wrappers(checks)
    counts.update(audit_generated_cases(checks))
    counts.update(audit_fixture_surface(checks))
    audit_docs_surface(checks)
    audit_cleanroom_image(checks)
    audit_runner_budget_guards(checks)
    audit_determinism(checks)

    notes = [
        "This deterministic audit proves the hidden tests are black-box executable interactions, not direct candidate-source checks.",
        "It cannot prove that a short agent run will infer the full Lua language and standard library; it checks only that the behavior is observable through docs plus normal oracle execution.",
    ]
    statuses = [check.status for check in checks]
    failures = sum(status == "fail" for status in statuses)
    warnings = sum(status == "warn" for status in statuses)
    verdict = "pass" if failures == 0 else "fail"
    payload = {
        "verdict": verdict,
        "blocking_failures": failures,
        "warnings": warnings,
        "counts": counts,
        "checks": [asdict(check) for check in checks],
        "notes": notes,
    }
    write_reports(payload)
    print(json.dumps(payload, indent=2))
    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
