import json
import re
from pathlib import Path

import pytest


CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "cases" / "harvested_cases.json").read_text()
)


def normalize_output(text, fixture_root):
    text = text.replace(str(fixture_root), "/workspace/fixtures/pocketlang")
    return re.sub(r"0x[0-9A-Fa-f]+", "0x<addr>", text)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_upstream_script_behavior(run_pocket, pocket_fixture, case):
    """CATCHES: harvested upstream PocketLang scripts preserve exact process behavior."""
    result = run_pocket(
        case["args"],
        cwd=pocket_fixture,
        input_text=case.get("stdin"),
        timeout=case.get("timeout", 25),
    )

    assert result.returncode == case["returncode"]
    assert normalize_output(result.stdout, pocket_fixture) == case["stdout"]
    assert normalize_output(result.stderr, pocket_fixture) == case["stderr"]
