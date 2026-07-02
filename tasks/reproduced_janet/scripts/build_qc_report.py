#!/usr/bin/env python3
"""Build a downstream QC report from Janet quality-gate and coverage artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_LINE_TARGET = 75.0


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_optional_json(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def check_status(ok: bool) -> str:
    return "passed" if ok else "failed"


def local_suite_counts(base: Path, quality: dict | None) -> dict:
    cases_path = base / "tests_generated/eval/cases/generated_cases.json"
    generated_cases = len(load_json(cases_path)) if cases_path.exists() else 0
    total = 0
    if quality:
        total = quality["gold"]["passed"] + quality["gold"]["failed"]
    return {
        "source": "local Janet recreation; no ProgramBench catalog entry",
        "catalog_task": False,
        "generated_cases": generated_cases,
        "active": total,
        "listed": total,
        "ignored": 0,
    }


def coverage_snapshot(path: Path) -> dict:
    if not path.exists():
        return {
            "source": str(path),
            "missing": True,
            "line_percent": 0.0,
            "line_covered": 0,
            "line_total": 0,
            "branch_percent": 0.0,
            "branch_covered": 0,
            "branch_total": 0,
            "files": [],
            "lowest_line_files": [],
        }
    data = load_json(path)
    files = [
        {
            "filename": item["filename"],
            "line_percent": item["line_percent"],
            "line_covered": item["line_covered"],
            "line_total": item["line_total"],
            "branch_percent": item.get("branch_percent", 0.0),
            "branch_covered": item.get("branch_covered", 0),
            "branch_total": item.get("branch_total", 0),
        }
        for item in sorted(data.get("files", []), key=lambda entry: entry["filename"])
    ]
    return {
        "source": str(path),
        "missing": False,
        "line_percent": data["line_percent"],
        "line_covered": data["line_covered"],
        "line_total": data["line_total"],
        "branch_percent": data.get("branch_percent", 0.0),
        "branch_covered": data.get("branch_covered", 0),
        "branch_total": data.get("branch_total", 0),
        "files": files,
        "lowest_line_files": sorted(files, key=lambda item: item["line_percent"])[:10],
    }


def build_linter_checks(quality: dict | None) -> list[dict]:
    if quality is None:
        return [
            {
                "id": "quality_report_present",
                "severity": "HIGH",
                "description": "Generated quality report exists.",
                "blocking": True,
                "findings": 1,
                "blocking_findings": 1,
                "status": "failed",
            }
        ]
    all_findings = Counter(finding["id"] for finding in quality["static_findings"])
    blocking_findings = Counter(finding["id"] for finding in quality["blocking_static_findings"])
    checks = []
    for check in quality.get("static_check_catalog", []):
        blocking_count = blocking_findings[check["id"]]
        finding_count = all_findings[check["id"]]
        checks.append(
            {
                "id": check["id"],
                "severity": check["severity"],
                "description": check["description"],
                "blocking": check["blocking"],
                "findings": finding_count,
                "blocking_findings": blocking_count,
                "status": check_status(blocking_count == 0) if check["blocking"] else "informational",
            }
        )
    return checks


def build_dynamic_checks(quality: dict | None) -> list[dict]:
    if quality is None:
        return [
            {
                "id": "quality_report_present",
                "blocking": True,
                "status": "failed",
                "observed": "missing",
            }
        ]
    gold = quality["gold"]
    dummy = quality["dummy"]
    return [
        {
            "id": "no_blocking_static_linter_findings",
            "blocking": True,
            "status": check_status(len(quality["blocking_static_findings"]) == 0),
            "observed": len(quality["blocking_static_findings"]),
        },
        {
            "id": "gold_suite_passes",
            "blocking": True,
            "status": check_status(gold["returncode"] == 0 and gold["failed"] == 0),
            "passed": gold["passed"],
            "failed": gold["failed"],
            "returncode": gold["returncode"],
        },
        {
            "id": "dummy_suite_rejects",
            "blocking": True,
            "status": check_status(dummy["passed"] == 0),
            "passed": dummy["passed"],
            "failed": dummy["failed"],
            "returncode": dummy["returncode"],
        },
    ]


def build_coverage_checks(root: Path, harvested: dict, generated: dict, line_target: float) -> list[dict]:
    base = root / "tasks/reproduced_janet"
    generated_full = base / "reports/coverage_generated/coverage.json"
    harvested_full = base / "reports/coverage_harvested/coverage.json"
    return [
        {
            "id": "generated_line_coverage_meets_local_target",
            "blocking": True,
            "target_line_percent": line_target,
            "observed_line_percent": generated["line_percent"],
            "status": check_status(not generated["missing"] and generated["line_percent"] >= line_target),
        },
        {
            "id": "generated_line_coverage_not_lower_than_harvested",
            "blocking": True,
            "harvested_line_percent": harvested["line_percent"],
            "generated_line_percent": generated["line_percent"],
            "delta_line_percent": round(generated["line_percent"] - harvested["line_percent"], 3),
            "status": check_status(
                not harvested["missing"]
                and not generated["missing"]
                and generated["line_percent"] >= harvested["line_percent"]
            ),
        },
        {
            "id": "generated_file_line_metrics_logged",
            "blocking": True,
            "files": len(generated["files"]),
            "status": check_status(bool(generated["files"])),
        },
        {
            "id": "generated_full_line_coverage_json_logged",
            "blocking": True,
            "source": str(generated_full),
            "status": check_status(generated_full.exists()),
        },
        {
            "id": "harvested_full_line_coverage_json_logged",
            "blocking": True,
            "source": str(harvested_full),
            "status": check_status(harvested_full.exists()),
        },
    ]


def normalize_audit_status(status: str) -> str:
    return {
        "pass": "passed",
        "fail": "failed",
        "warn": "warning",
    }.get(status, status)


def build_fairness_report_checks(base: Path) -> list[dict]:
    fairness_md = base / "reports/fairness_lm_judge.md"
    return [
        {
            "id": "fairness_report_present",
            "blocking": True,
            "status": check_status(fairness_md.exists()),
            "observed": str(fairness_md),
        }
    ]


def build_deterministic_fairness_checks(review: dict | None) -> list[dict]:
    if review is None:
        return [
            {
                "id": "deterministic_fairness_report_present",
                "blocking": True,
                "status": "failed",
                "observed": "missing",
            }
        ]

    checks = [
        {
            "id": "deterministic_fairness_report_present",
            "blocking": True,
            "status": "passed",
            "observed": review["source"],
        },
        {
            "id": "deterministic_fairness_audit_passed",
            "blocking": True,
            "status": check_status(review.get("verdict") == "pass"),
            "observed": review.get("verdict", "missing"),
            "blocking_failures": review.get("blocking_failures"),
        },
    ]
    for check in review.get("checks", []):
        status = normalize_audit_status(check["status"])
        checks.append(
            {
                "id": f"deterministic_{check['id']}",
                "blocking": check["status"] == "fail",
                "status": status,
                "evidence": check.get("evidence", ""),
            }
        )
    return checks


def build_lm_judge_checks(review: dict | None) -> list[dict]:
    if review is None:
        return [
            {
                "id": "lm_as_judge_review_present",
                "blocking": True,
                "status": "failed",
                "observed": "missing",
            }
        ]
    checks = [
        {
            "id": "lm_as_judge_review_present",
            "blocking": True,
            "status": "passed",
            "observed": review["source"],
        }
    ]
    checks.extend(review.get("checks", []))
    return checks


def markdown(report: dict) -> str:
    lines = [
        "# Janet Generated Suite QC Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Local generated tests: `{report['catalog']['active']}`",
        f"- Generated gold pass count: `{report['quality']['gold']['passed']}`",
        f"- Generated line coverage: `{report['coverage']['generated']['line_percent']}%`",
        f"- Generated branch coverage: `{report['coverage']['generated']['branch_percent']}%`",
        "",
        "## Dynamic Checks",
        "",
        "| Check | Status | Observed |",
        "| --- | --- | ---: |",
    ]
    for check in report["dynamic_checks"]:
        observed = check.get("observed", check.get("passed", ""))
        lines.append(f"| {check['id']} | {check['status']} | {observed} |")

    lines.extend(
        [
            "",
            "## Coverage Checks",
            "",
            "| Check | Status | Observed | Target |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for check in report["coverage_line_checks"]:
        observed = check.get("observed_line_percent", check.get("generated_line_percent", check.get("files", "")))
        target = check.get("target_line_percent", "")
        lines.append(f"| {check['id']} | {check['status']} | {observed} | {target} |")

    lines.extend(
        [
            "",
            "## Linter Checks",
            "",
            "| Check | Severity | Status | Findings | Blocking findings |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for check in report["linter_checks"]:
        lines.append(
            "| {id} | {severity} | {status} | {findings} | {blocking_findings} |".format(**check)
        )

    deterministic = report["deterministic_fairness_review"]
    lines.extend(
        [
            "",
            "## Deterministic Fairness Review",
            "",
            f"- Verdict: `{deterministic['verdict']}`",
            f"- Blocking failures: `{deterministic['blocking_failures']}`",
            f"- Warnings: `{deterministic['warnings']}`",
            "",
            "| Check | Status | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for check in deterministic.get("checks", []):
        lines.append(f"| {check['id']} | {check['status']} | `{check.get('evidence', '')}` |")

    lines.extend(
        [
            "",
            "## LM-as-Judge Fairness Review",
            "",
            f"- Verdict: `{report['lm_as_judge_review']['verdict']}`",
            f"- Subject run: `{report['lm_as_judge_review']['subject_run']}`",
            f"- Latest eval status: `{report['lm_as_judge_review']['latest_eval']['status']}`",
            f"- Latest eval passed: `{report['lm_as_judge_review']['latest_eval']['passed']}/{report['lm_as_judge_review']['latest_eval']['tests']}`",
            "",
            "| Check | Status | Blocking | Evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for check in report["lm_as_judge_checks"]:
        evidence = check.get("evidence", check.get("observed", ""))
        lines.append(f"| {check['id']} | {check['status']} | {check.get('blocking', False)} | `{evidence}` |")

    lines.extend(
        [
            "",
            "### LM judge findings",
            "",
            "| Severity | Status | Finding | Evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for finding in report["lm_as_judge_review"].get("findings", []):
        lines.append(
            f"| {finding['severity']} | {finding['status']} | {finding['finding']} | "
            f"`{finding.get('evidence', '')}` |"
        )

    lines.extend(
        [
            "",
            "## Lowest Generated Line Coverage Files",
            "",
            "| File | Lines | Line coverage | Branch coverage |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in report["coverage"]["generated"]["lowest_line_files"]:
        lines.append(
            f"| {item['filename']} | {item['line_covered']}/{item['line_total']} | "
            f"{item['line_percent']}% | {item['branch_percent']}% |"
        )

    lines.extend(["", "## Raw Artifact Paths", ""])
    for name, path in report["artifacts"].items():
        lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--line-target", type=float, default=DEFAULT_LINE_TARGET)
    args = parser.parse_args()

    root = args.root.resolve()
    base = root / "tasks/reproduced_janet"
    out_dir = base / "reports/qc"
    out_dir.mkdir(parents=True, exist_ok=True)

    quality_path = base / "reports/quality_generated/quality_report.json"
    harvested_coverage_path = base / "reports/coverage_harvested/coverage_summary.json"
    generated_coverage_path = base / "reports/coverage_generated/coverage_summary.json"
    deterministic_fairness_path = base / "reports/qc/deterministic_fairness_report.json"
    lm_judge_path = base / "reports/qc/lm_as_judge_review.json"

    quality = load_optional_json(quality_path)
    harvested = coverage_snapshot(harvested_coverage_path)
    generated = coverage_snapshot(generated_coverage_path)
    deterministic_fairness_review = load_optional_json(deterministic_fairness_path)
    if deterministic_fairness_review is not None:
        deterministic_fairness_review.setdefault("source", str(deterministic_fairness_path))
    lm_judge_review = load_optional_json(lm_judge_path)
    linter_checks = build_linter_checks(quality)
    dynamic_checks = build_dynamic_checks(quality)
    coverage_checks = build_coverage_checks(root, harvested, generated, args.line_target)
    fairness_report_checks = build_fairness_report_checks(base)
    deterministic_fairness_checks = build_deterministic_fairness_checks(deterministic_fairness_review)
    lm_judge_checks = build_lm_judge_checks(lm_judge_review)

    blocking_checks = [
        check
        for check in [
            *linter_checks,
            *dynamic_checks,
            *coverage_checks,
            *fairness_report_checks,
            *deterministic_fairness_checks,
            *lm_judge_checks,
        ]
        if check.get("blocking")
    ]
    failed_blocking = [check for check in blocking_checks if check["status"] != "passed"]

    quality_block = quality or {
        "source": str(quality_path),
        "gold": {"passed": 0, "failed": 0, "returncode": -1},
        "dummy": {"passed": 0, "failed": 0, "returncode": -1},
        "static_findings": [],
        "blocking_static_findings": [],
    }
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed" if not failed_blocking else "failed",
        "failed_blocking_checks": failed_blocking,
        "catalog": local_suite_counts(base, quality),
        "quality": {
            "source": str(quality_path),
            "gold": quality_block["gold"],
            "dummy": quality_block["dummy"],
            "static_findings": quality_block["static_findings"],
            "blocking_static_findings": quality_block["blocking_static_findings"],
        },
        "linter_checks": linter_checks,
        "dynamic_checks": dynamic_checks,
        "coverage_line_checks": coverage_checks,
        "fairness_report_checks": fairness_report_checks,
        "deterministic_fairness_review": deterministic_fairness_review
        or {
            "source": str(deterministic_fairness_path),
            "verdict": "missing",
            "blocking_failures": 1,
            "warnings": 0,
            "counts": {},
            "checks": [],
            "notes": [],
        },
        "deterministic_fairness_checks": deterministic_fairness_checks,
        "lm_as_judge_review": lm_judge_review
        or {
            "source": str(lm_judge_path),
            "verdict": "missing",
            "subject_run": "",
            "latest_eval": {"status": "missing", "passed": 0, "tests": 0},
            "findings": [],
        },
        "lm_as_judge_checks": lm_judge_checks,
        "coverage": {
            "harvested": harvested,
            "generated": generated,
        },
        "artifacts": {
            "quality_report": str(quality_path),
            "quality_log": str(base / "logs/quality_generated.log"),
            "gold_junit": str(base / "reports/quality_generated/gold_results.xml"),
            "dummy_junit": str(base / "reports/quality_generated/dummy_results.xml"),
            "coverage_generated_summary": str(generated_coverage_path),
            "coverage_generated_full": str(base / "reports/coverage_generated/coverage.json"),
            "coverage_generated_log": str(base / "logs/coverage_generated.log"),
            "coverage_harvested_summary": str(harvested_coverage_path),
            "coverage_harvested_full": str(base / "reports/coverage_harvested/coverage.json"),
            "coverage_harvested_log": str(base / "logs/coverage_harvested.log"),
            "fairness_report": str(base / "reports/fairness_lm_judge.md"),
            "deterministic_fairness_report": str(deterministic_fairness_path),
            "lm_as_judge_review": str(lm_judge_path),
        },
    }

    json_path = out_dir / "generated_qc_report.json"
    md_path = out_dir / "generated_qc_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    md_path.write_text(markdown(report))
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
