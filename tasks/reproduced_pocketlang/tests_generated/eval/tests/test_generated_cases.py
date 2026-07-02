import json
import re
from pathlib import Path

import pytest


CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "cases" / "generated_cases.json").read_text()
)


def normalize_output(text, tmp_path, executable):
    text = text.replace(str(tmp_path), "<tmp>")
    text = text.replace(str(executable), "<executable>")
    return re.sub(r"0x[0-9A-Fa-f]+", "0x<addr>", text)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_generated_behavior_case(run_pocket, executable, case, tmp_path):
    """CATCHES: generated PocketLang snippets preserve stdout, stderr, and exit code."""
    for rel_path, content in case.get("files", {}).items():
        target = tmp_path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    result = run_pocket(
        case["args"],
        input_text=case.get("stdin"),
        cwd=tmp_path,
        env=case.get("env"),
        timeout=case.get("timeout", 15),
    )

    assert result.returncode == case["returncode"]
    assert normalize_output(result.stdout, tmp_path, executable) == case["stdout"]
    assert normalize_output(result.stderr, tmp_path, executable) == case["stderr"]
