import json
from pathlib import Path

import pytest


CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "cases" / "generated_cases.json").read_text()
)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_generated_behavior_case(run_janet, case, tmp_path):
    """CATCHES: generated Janet snippets preserve stdout, stderr, and exit code."""
    result = run_janet(
        case["args"],
        input_text=case.get("stdin"),
        cwd=tmp_path,
        env=case.get("env"),
        timeout=15,
    )

    assert result.returncode == case["returncode"]
    assert result.stdout == case["stdout"]
    assert result.stderr == case["stderr"]
