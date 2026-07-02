import os
import shutil
import subprocess
from pathlib import Path

import pytest


def _default_executable() -> Path:
    for name in ("EXECUTABLE", "EXE"):
        value = os.environ.get(name)
        if value:
            return Path(value)
    workspace_exe = Path("/workspace/executable")
    if workspace_exe.exists():
        return workspace_exe
    return Path.cwd() / "executable"


@pytest.fixture(scope="session")
def executable() -> Path:
    exe = _default_executable()
    assert exe.exists(), f"executable not found at {exe}"
    return exe


@pytest.fixture
def run_janet(executable):
    def _run(args=None, *, input_text=None, input_bytes=None, cwd=None, env=None, timeout=20):
        assert input_text is None or input_bytes is None
        full_env = os.environ.copy()
        full_env.setdefault("LC_ALL", "C")
        full_env.setdefault("TZ", "UTC")
        full_env.pop("JANET_PATH", None)
        full_env.pop("JANET_PROFILE", None)
        if env:
            full_env.update(env)
        data = input_bytes if input_bytes is not None else input_text
        text_mode = input_bytes is None
        return subprocess.run(
            [str(executable), *(args or [])],
            input=data,
            cwd=cwd,
            env=full_env,
            text=text_mode,
            capture_output=True,
            timeout=timeout,
        )

    return _run


@pytest.fixture
def janet_fixture(tmp_path):
    src = Path(__file__).resolve().parents[1] / "fixtures" / "janet"
    dst = tmp_path / "janet"
    shutil.copytree(src, dst)
    return dst
