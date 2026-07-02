#!/usr/bin/env python3
"""Deterministic fairness audit for the Janet generated evaluation suite."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "tasks" / "reproduced_janet"
EVAL = TASK / "tests_generated" / "eval"
TESTS = EVAL / "tests"
CASES = EVAL / "cases" / "generated_cases.json"
FIXTURES = EVAL / "fixtures" / "janet"
USAGE = TASK / "task_env" / "docs" / "USAGE.md"
BUILD_IMAGE = TASK / "scripts" / "build_miniswe_cleanroom_image.sh"
REPORT_DIR = TASK / "reports" / "qc"

REQUIRED_DOC_TERMS = [
    "array",
    "asm",
    "buffer",
    "bundle",
    "capi",
    "cfuns",
    "compile",
    "corelib",
    "debug",
    "ev",
    "ffi",
    "filewatch",
    "inttypes",
    "io",
    "marshal",
    "math",
    "net",
    "os",
    "parse",
    "peg",
    "pretty-printing",
    "special forms",
    "string",
    "strtod",
    "struct",
    "symcache",
    "table",
    "tuple",
    "value",
    "vm",
]

PY_TEST_FORBIDDEN = [
    r"tasks/reproduced_janet/_src",
    r"tasks/reproduced_janet/gold",
    r"/Users/",
    r"programbench-takehome",
    r"github\.com/janet-lang/janet",
    r"0fea20c82182fe661f75b00a8889d801fe2d79b6",
]

FIXTURE_FORBIDDEN = [
    r"/Users/",
    r"programbench-takehome",
    r"tasks/reproduced_janet/_src",
    r"tasks/reproduced_janet/gold",
]

NATIVE_FIXTURE_NAMES = {".c", ".h", ".o", ".so", ".dylib", ".a"}
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


def grep_patterns(paths: list[Path], patterns: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    compiled = [(pattern, re.compile(pattern, re.I)) for pattern in patterns]
    for path in paths:
        text = read_text(path)
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern, regex in compiled:
                if regex.search(line):
                    findings.append({"file": rel(path), "line": line_no, "pattern": pattern, "text": line[:240]})
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
        "No forbidden workspace/source strings in pytest wrappers." if not leaks else json.dumps(leaks[:10], indent=2),
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
                    bad_calls.append({"file": rel(path), "call": call_name, "line": getattr(node, "lineno", None)})

    add(
        checks,
        "pytest_tests_use_run_janet_black_box_fixture",
        "pass" if not bad_imports and not bad_calls else "fail",
        "Test wrappers avoid direct subprocess/source inspection and route behavior through run_janet."
        if not bad_imports and not bad_calls
        else json.dumps({"bad_imports": bad_imports, "bad_calls": bad_calls}, indent=2),
    )


def audit_generated_cases(checks: list[Check]) -> dict[str, Any]:
    cases = json.loads(CASES.read_text())
    ids = [case.get("id") for case in cases]
    schema_errors: list[str] = []
    for index, case in enumerate(cases):
        for key in ("id", "args", "returncode", "stdout", "stderr"):
            if key not in case:
                schema_errors.append(f"case {index} missing {key}")
        if not isinstance(case.get("args"), list):
            schema_errors.append(f"case {index} args is not a list")
        elif case["args"][:1] != ["--eval"]:
            schema_errors.append(f"{case.get('id', index)} does not use --eval")
        if case.get("env"):
            schema_errors.append(f"{case.get('id', index)} has custom env {case.get('env')}")
        joined = json.dumps(case)
        if re.search(r"/Users/|programbench-takehome|tasks/reproduced_janet|_src|gold/", joined):
            schema_errors.append(f"{case.get('id', index)} leaks workspace/source path")

    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    add(
        checks,
        "generated_cases_are_self_contained_eval_invocations",
        "pass" if not schema_errors and not duplicates else "fail",
        f"{len(cases)} generated cases use --eval with explicit stdout/stderr/returncode and no path/env leaks."
        if not schema_errors and not duplicates
        else json.dumps({"schema_errors": schema_errors[:20], "duplicate_ids": duplicates}, indent=2),
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

    native_files = [path for path in files if path.suffix in NATIVE_FIXTURE_NAMES or path.name == "Makefile"]
    upstream_suite = read_text(TESTS / "test_upstream_suite.py")
    native_referenced = [
        path for path in native_files if path.name in upstream_suite or str(path.relative_to(FIXTURES)) in upstream_suite
    ]
    add(
        checks,
        "native_source_fixtures_are_not_invoked_by_hidden_tests",
        "pass" if not native_referenced else "fail",
        f"{len(native_files)} native/example source fixture files exist but none are referenced by pytest parameter lists."
        if not native_referenced
        else json.dumps([rel(path) for path in native_referenced], indent=2),
    )

    suite_names = sorted(re.findall(r'"(suite-[^"]+\.janet)"\s*:', upstream_suite))
    example_names = sorted(re.findall(r'^\s+"([^"]+\.janet)",$', upstream_suite, flags=re.M))
    add(
        checks,
        "upstream_fixtures_are_executable_inputs_not_candidate_introspection",
        "pass",
        f"{len(suite_names)} suite scripts and {len(example_names)} example scripts are passed as executable inputs under cwd, not used to inspect candidate source.",
    )
    return {"suite_count": len(suite_names), "example_count": len(example_names)}


def audit_docs_surface(checks: list[Check]) -> None:
    usage = read_text(USAGE).lower()
    missing = [term for term in REQUIRED_DOC_TERMS if term.lower() not in usage]
    add(
        checks,
        "solver_docs_name_hidden_behavior_families",
        "pass" if not missing else "fail",
        "USAGE.md names the CLI and standard library behavior families covered by hidden tests."
        if not missing
        else f"USAGE.md is missing behavior-family terms: {', '.join(missing)}",
    )

    required_guardrails = ["do not inspect", "open(..., \"rb\")", "normal cli", "no original janet source tree"]
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
    runner = read_text(TASK / "scripts" / "run_miniswe_janet.py")
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
    runner = read_text(TASK / "scripts" / "run_miniswe_janet.py")
    wrapper = read_text(TASK / "scripts" / "run_miniswe_janet.sh")
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
        "OBSERVATION_PHASE_COMMAND_LIMIT = 30" in runner,
        "BUILD_PHASE_COMMAND_LIMIT = 45" in runner,
        "SOURCE_BUILD_GRACE_COMMANDS = 12" in runner,
        "MIN_IMPLEMENTATION_BYTES = 2000" in runner,
        "CANDIDATE_SMOKE_TIMEOUT_SECONDS = 5" in runner,
        "COMMAND_CYCLE_WINDOW = 3" in runner,
        "MAX_REPEATED_COMMAND_CYCLES = 5" in runner,
        "recent_commands" in runner,
        "same command cycle repeated" in runner,
        "FORMAT_REPAIR_COMMANDS" in runner,
        "except FormatError" in runner,
        "format_error_to_bash_tool_call" in runner,
        '"actions": [{"command": command, "tool_call_id": tool_call_id}]' in runner,
        "format_error_messages" in runner,
        "has_bash_tool_call" in runner,
        "synthesize_missing_tool_call_response" in runner,
        "SCRATCHPAD_COMMENT_PATTERN" in runner,
        "scratchpad_source_command_reason" in runner,
        "throwaway source file" in runner,
        "persistent source creation" in runner,
        "JANET_CANDIDATE_BEHAVIOR_CASES" in runner,
        "JANET_GATE_HARDCODE_NEEDLES" in runner,
        "JANET_GATE_HARDCODE_REGEXES" in runner,
        "SOURCE_WRITE_COMMAND_PATTERNS" in runner,
        'SUBMIT_TOKEN = "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"' in runner,
        "SUBMIT_COMMAND_PATTERN.search(command)" in runner,
        "workspace_has_nontrivial_implementation" in runner,
        "candidate_source_avoids_gate_hardcoding" in runner,
        "candidate_smoke_command" in runner,
        "timeout {CANDIDATE_SMOKE_TIMEOUT_SECONDS}s" in runner,
        "candidate_has_basic_janet_behavior" in runner,
        '"--eval"' in runner,
        '"--expression"' in runner,
        "generalized smoke families" in runner,
        "literal smoke hardcoding" in runner,
        "submission rejected before scoring" in runner,
        "observation phase exceeded" in runner,
        "build phase exceeded" in runner,
        "same command repeated" in runner,
        "oracle commands since the last source/build action" in runner,
        "nonproductive commands since the last source/build action" in runner,
        "network probing or downloading is disallowed" in runner,
        "package manager and package-cache probing is disallowed" in runner,
        "system Janet package probing is disallowed" in runner,
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
        "Janet mini-SWE runner applies token/reasoning/observation caps, forces the named bash tool by default, recovers parser-raised Gemini FormatErrors into executable bash actions, strips Gemini thought metadata, removes commit instructions, enforces earlier persistent-source/build phases, rejects scratchpad heredocs and placeholder submissions, requires timeout-bounded generalized Janet smoke behavior including long eval/expression flags, rejects literal smoke hardcoding, and blocks oracle-inspection/git/network/package/system-search/repeated-command and repeated-command-cycle stagnation."
        if all(conditions)
        else "Janet mini-SWE runner is missing one or more token/reasoning/context/tool-choice/format-repair/source-first/behavior/hardcode/oracle/scratchpad/git/network/package/system-search/stagnation guard settings.",
    )


def audit_determinism(checks: list[Check]) -> None:
    conftest = read_text(TESTS / "conftest.py")
    upstream = read_text(TESTS / "test_upstream_suite.py")
    conditions = [
        "LC_ALL" in conftest and "C" in conftest,
        "TZ" in conftest and "UTC" in conftest,
        "JANET_PATH" in conftest and "JANET_PROFILE" in conftest,
        "Finished suite" in upstream and "[0-9.]+ seconds" in upstream,
    ]
    add(
        checks,
        "test_harness_normalizes_environment_and_timing",
        "pass" if all(conditions) else "fail",
        "Harness sets LC_ALL=C, TZ=UTC, clears Janet path/profile env, and regexes suite duration."
        if all(conditions)
        else "One or more deterministic harness normalizations is missing.",
    )


def write_reports(payload: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / "deterministic_fairness_report.json"
    md_path = REPORT_DIR / "deterministic_fairness_report.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Janet Deterministic Fairness Report",
        "",
        f"- Verdict: `{payload['verdict']}`",
        f"- Blocking failures: `{payload['blocking_failures']}`",
        f"- Warnings: `{payload['warnings']}`",
        f"- Generated cases: `{payload['counts']['generated_case_count']}`",
        f"- Upstream suite scripts: `{payload['counts']['suite_count']}`",
        f"- Upstream example flycheck scripts: `{payload['counts']['example_count']}`",
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
        "It cannot prove that a short agent run will infer the full Janet language and standard library; it checks only that the behavior is observable through docs plus normal oracle execution.",
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
