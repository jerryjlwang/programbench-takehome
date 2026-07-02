#!/usr/bin/env python3
"""Run the mini-SWE-agent ProgramBench scaffold on the local PocketLang cleanroom."""

from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import os
import re
import shlex
import sys
import tarfile
import time
import traceback
from typing import Any
from pathlib import Path

from minisweagent.config import builtin_config_dir, get_config_from_spec
from minisweagent.environments import get_environment
from minisweagent.exceptions import FormatError
from minisweagent.models import get_model
from minisweagent.run.benchmarks.programbench import ProgramBenchAgent, copy_submission
from minisweagent.utils.log import add_file_handler, logger
from minisweagent.utils.serialize import UNSET, recursive_merge


INSTANCE_ID = "thakeenathees__pocketlang.cc73ca6"
DEFAULT_MODEL = "gemini/gemini-3.5-flash"
DEFAULT_CONFIG = builtin_config_dir / "benchmarks" / "programbench.yaml"
GEMINI_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")
DEFAULT_MAX_TOKENS = 2048
DEFAULT_REASONING_EFFORT = "none"
DEFAULT_OBSERVATION_CHAR_LIMIT = 4000
DEFAULT_STEP_LIMIT = 1000
DEFAULT_WALL_TIME_LIMIT_SECONDS = 7200
MAX_CONSECUTIVE_IDENTICAL_COMMANDS = 5
ORACLE_ONLY_STAGNATION_LIMIT = 200
NONPRODUCTIVE_COMMAND_LIMIT = 80
OBSERVATION_PHASE_COMMAND_LIMIT = 30
BUILD_PHASE_COMMAND_LIMIT = 45
SOURCE_BUILD_GRACE_COMMANDS = 12
MIN_IMPLEMENTATION_BYTES = 2000
CANDIDATE_SMOKE_TIMEOUT_SECONDS = 5
COMMAND_CYCLE_WINDOW = 4
MAX_REPEATED_COMMAND_CYCLES = 3
MAX_FORMAT_REPAIR_COMMANDS = 8
POST_COMPILE_ORACLE_LIMIT = 20
ORACLE_BURST_AFTER_CANDIDATE_LIMIT = 3
FORMAT_REPAIR_COMMANDS = (
    "./compile.sh",
    "test -x ./candidate && ./candidate -v || true",
    "test -x ./candidate && ./candidate -c 'print(2 + 3)' || true",
    "find . -maxdepth 2 -type f -not -path './docs/*' -print",
    "sed -n '1,140p' main.c 2>/dev/null || sed -n '1,140p' pocket.c 2>/dev/null || true",
)
POCKETLANG_CANDIDATE_BEHAVIOR_CASES = [
    {
        "name": "multiple arithmetic command statements",
        "argv": ["./candidate", "-c", "print(7 + 11 + 13); print(3 * 5 * 7); print(100 - 9 - 8)"],
        "stdout": "31\n105\n83\n",
    },
    {
        "name": "string methods",
        "argv": [
            "./candidate",
            "-c",
            "s = 'red-green-blue'; print(s.upper()); print(s.replace('-', '|'))",
        ],
        "stdout": "RED-GREEN-BLUE\nred|green|blue\n",
    },
    {
        "name": "lists and maps",
        "argv": [
            "./candidate",
            "-c",
            "l = [3, 5]; l.append(8); print(l.length); print(l.pop()); m = {'alpha': 17, 'beta': 29}; print(m['alpha'] + m['beta'])",
        ],
        "stdout": "3\n8\n46\n",
    },
    {
        "name": "long command flag",
        "argv": ["./candidate", "--cmd", "print('long-cmd'); print(6 * 7)"],
        "stdout": "long-cmd\n42\n",
    },
    {
        "name": "version flag",
        "argv": ["./candidate", "--version"],
        "stdout": "pocketlang 0.1.0\n",
    },
    {
        "name": "debug command flag",
        "argv": ["./candidate", "--debug", "--cmd", "print(14 + 28)"],
        "stdout": "42\n",
    },
    {
        "name": "script file functions",
        "command": "\n".join(
            [
                "tmp=$(mktemp ./pocketlang-smoke.XXXXXX.pk)",
                "cat > \"$tmp\" <<'PK'",
                "def fib(n)",
                "  if n < 2 then return n end",
                "  return fib(n-1) + fib(n-2)",
                "end",
                "for i in 0..6",
                "  print(fib(i))",
                "end",
                "PK",
                "./candidate \"$tmp\"",
                "rc=$?",
                "rm -f \"$tmp\"",
                "exit $rc",
            ]
        ),
        "stdout": "0\n1\n1\n2\n3\n5\n",
    },
    {
        "name": "script file while loop",
        "command": "\n".join(
            [
                "tmp=$(mktemp ./pocketlang-loop.XXXXXX.pk)",
                "cat > \"$tmp\" <<'PK'",
                "i = 0",
                "acc = 0",
                "while i < 5 do",
                "  acc += i * i",
                "  i += 1",
                "end",
                "print(acc)",
                "PK",
                "./candidate \"$tmp\"",
                "rc=$?",
                "rm -f \"$tmp\"",
                "exit $rc",
            ]
        ),
        "stdout": "30\n",
    },
]
POCKETLANG_GATE_HARDCODE_NEEDLES = [
    "print(7 + 11 + 13)",
    "print(3 * 5 * 7)",
    "red-green-blue",
    "red|green|blue",
    "{'alpha': 17, 'beta': 29}",
    "long-cmd",
    "fib(n-1) + fib(n-2)",
    "acc += i * i",
]
POCKETLANG_GATE_HARDCODE_REGEXES = [
    r"\b(?:strstr|strcasestr|strcmp|strncmp|memcmp|memmem)\s*\(\s*(?:expr|code|source|cmd|command|input|program|script|line|text|buffer|buf|src)\b",
    r"\b(?:strstr|strcasestr|strcmp|strncmp|memcmp|memmem)\s*\(\s*argv\s*\[\s*(?:[2-9]|\d{2,})\s*\]",
    r"\b(?:const\s+)?char\s*\*+\s*(?:expr|code|source|cmd|command|input|program|script|line|text|buffer|buf|src)\s*=\s*argv\s*\[\s*(?:[2-9]|\d{2,})\s*\]",
]
POCKETLANG_GATE_DELEGATION_REGEXES = [
    r"\b(?:system|popen)\s*\(",
    r"\b(?:execl|execlp|execle|execv|execvp|execve|posix_spawn|posix_spawnp)\s*\(",
    r"\b(?:fork|vfork)\s*\(",
    r"['\"]/usr/bin/(?:python3?|perl|ruby|node|bash|sh|lua|janet)['\"]",
    r"['\"]/(?:bin|usr/bin)/(?:python3?|perl|ruby|node|bash|sh|lua|janet)['\"]",
    r"\b(?:python3?|perl|ruby|node|lua|janet)\b",
    r"\b(?:fopen|open)\s*\([^)]*['\"][^'\"]+\.(?:py|sh|lua|janet|pk)['\"]",
    r"\b(?:fprintf|fputs|write)\s*\([^)]*(?:python_source|runner|script)",
]
AGENT_GUARDRAIL_APPENDIX = """

## PocketLang cleanroom guardrails

The cleanroom intentionally contains no PocketLang source tree, package-cache source,
or hidden source archive. Do not search system directories, package caches, /tmp,
/opt, /usr/src, /usr/local/src, or similar locations for original PocketLang source.

The provided ./executable is an execute-only black-box oracle. You may run it
with CLI arguments, stdin, scripts, and temporary data files to observe behavior.
You must not inspect or preserve the binary itself. Do not use strings, objdump,
readelf, xxd, hexdump, od, strace, ltrace, gdb, raw byte reads, hashing, copying,
renaming, permission changes, embedded byte arrays, or temp-file delegation on
./executable. If a command is blocked by the benchmark guard, abandon that line
of attack and continue with ordinary behavioral observation.

The expected valid strategy is to write original replacement source that matches
as much observed behavior as possible, then submit a compiling implementation.

Do not use bash tool calls as a scratchpad. A bash command should inspect files,
run the oracle, edit source, build, test, or submit. Put reasoning in normal
assistant text, not in python -c comments, shell comments, or here-doc comments.
The harness rejects source heredocs dominated by notes like "let's think",
"wait", or "can we", and rejects throwaway source files removed in the same
command. Write persistent implementation code directly.

Do not run git init, git add, git commit, or create a new repository. The
benchmark captures the workspace automatically after you submit.

Do not spend time looking for installed PocketLang source, system package caches,
network mirrors, local package-manager databases, or source archives. They are
not available in the cleanroom, and those commands are treated as benchmark
escape hatches. After reading docs and observing a small set of behaviors,
create replacement source. A partial interpreter that handles CLI, arithmetic,
strings, lists/maps, functions, loops, and simple scripts is better than a version-only
placeholder. Do not submit a placeholder that only prints the version.

Before final submission, ./candidate must run generalized PocketLang behavior, not
only a version string or a few exact examples. The submit harness checks varied
arithmetic, multiple statements in one command string, lists, maps, strings,
short and long command flags, script execution, functions, loops, and mutable
variables. Each smoke command has a short timeout so infinite loops do not count
as progress. The exact smoke inputs are intentionally not listed. Hardcoding
full eval strings or matching whole argv[2] snippets is rejected; implement
parsing and evaluation. Do not branch on exact command substrings with
strstr/strcmp/strncmp over variables such as cmd, input, source, line, or
argv[2], including copied or normalized buffers derived from argv[2]; parse
tokens and evaluate expressions/statements generally.

You must start writing persistent source by command 30. After that point, observation-only
commands may be blocked until you create implementation files. After you have
source, compile within about 12 more commands and debug the candidate instead of returning to broad oracle
probing. In the solve cleanroom, ./compile.sh builds ./candidate while the
protected oracle is still present at ./executable; run ./candidate for
development checks. After the first compile, oracle queries are limited: run
./candidate first, use ./executable only for a narrow mismatch, then return to
source edits and ./candidate checks. Final scoring removes the oracle and rebuilds ./executable.
Submissions without a nontrivial source implementation are rejected by the solve
harness before scoring.

The final scored artifact is only the compiled ./executable. The evaluator runs
./compile.sh, then copies only ./executable into the hidden-test container. Do
not make the executable depend on sibling runtime files such as pocketlang.py,
scripts/, source files, generated data files, or files under /workspace. If you
prototype in another language, compile/embed that implementation into the
executable or make compile.sh generate a self-contained executable that can run
after all other submitted files are absent. Do not call external interpreters or
tools at runtime with system, popen, exec*, posix_spawn, /usr/bin/python,
python3, bash, sh, node, ruby, perl, lua, or janet; final scoring may run where
those programs or sibling runner files are absent.
"""
DISALLOWED_COMMAND_PATTERNS = [
    (re.compile(r"\b(?:strings|objdump|readelf|ldd|gdb|r2|radare2?|ghidra|strace|ltrace)\b[^\n;&|]*\b(?:\./)?executable\b", re.I), "binary analysis of ./executable is disallowed"),
    (re.compile(r"\b(?:xxd|hexdump|od|base64|sha(?:sum|1sum|256sum|512sum)|md5sum)\b[^\n;&|]*\b(?:\./)?executable\b", re.I), "raw-byte/hash inspection of ./executable is disallowed"),
    (re.compile(r"\b(?:cat|less|more|head|tail)\b[^\n;&|]*\b(?:\./)?executable\b", re.I), "reading ./executable bytes is disallowed"),
    (re.compile(r"\b(?:cp|install|dd|mv)\s+(?:-[^\s]+\s+)*(?:\./)?executable\b", re.I), "copying or renaming the oracle executable is disallowed"),
    (re.compile(r"\bchmod\b[^\n;&|]*\b(?:\./)?executable\b", re.I), "changing oracle executable permissions is disallowed"),
    (re.compile(r"open\(\s*[\"'](?:\./)?executable[\"']\s*,\s*[\"'][^\"']*[rb]", re.I), "opening ./executable for byte reads is disallowed"),
    (re.compile(r"Path\(\s*[\"'](?:\./)?executable[\"']\s*\)\.(?:read_bytes|read_text)", re.I), "reading ./executable through pathlib is disallowed"),
    (re.compile(r"\bexecutable_orig\b|\bbinary_data\b|\bbinary_size\b", re.I), "embedding or preserving oracle bytes is disallowed"),
    (re.compile(r"\bexecv\s*\(\s*tmp_path\b|\bexecl\s*\(\s*tmp_path\b|\bexecve\s*\(\s*tmp_path\b", re.I), "temp-file delegation to embedded bytes is disallowed"),
    (re.compile(r"\bgit\s+(?:init|add|commit)\b", re.I), "git repository commands are unnecessary in this benchmark"),
    (re.compile(r"\bpython3?\s+-c\s+[\"'][\s\S]{0,500}#\s*(?:wait|let'?s|this is|wonderful|awesome|oh!?|ah!?)", re.I), "scratchpad-only python -c commands are disallowed"),
    (re.compile(r"\b(?:curl|wget)\b|\burllib\.request\b|\brequests\.\b|\bsocket\.gethostbyname\b", re.I), "network probing or downloading is disallowed"),
    (re.compile(r"\b(?:apt|apt-get|apt-cache|dpkg|pip|npm|cargo|go)\b", re.I), "package manager and package-cache probing is disallowed"),
    (re.compile(r"\bpkg-config\b[^\n;&|]*(?:pocketlang|pocket)\b", re.I), "system PocketLang package probing is disallowed"),
    (re.compile(r"\bfind\s+/(?:\s|$)|\bfind\s+/(?:usr|opt|tmp|var|root|home|lib|lib64|bin|sbin|etc)\b", re.I), "searching system directories for source or runtimes is disallowed"),
    (re.compile(r"\b(?:grep|rg|ls|du)\b[\s\S]{0,80}\s/(?:usr|opt|tmp|var|root|home|lib|lib64|bin|sbin|etc)\b", re.I), "probing system directories for source or runtimes is disallowed"),
]
SOURCE_REDIRECT_PATTERN = re.compile(
    r"(?:>|>>)\s*(?:\./)?(?P<path>(?!AGENT_REPORT\b)[\w./-]+\.(?:c|h|py|pk|sh))\b",
    re.I,
)
SCRATCHPAD_COMMENT_PATTERN = re.compile(
    r"^\s*(?://|#)\s*(?:let'?s think|wait[,\s!]|can we\b|what if\b|"
    r"the prompt says\b|the benchmark wants\b|is the provided\b|"
    r"we need to\b|this is\b|oh[!,]|yes[!,]|no,|hmm\b)",
    re.I,
)
SCRATCHPAD_PHRASE_PATTERN = re.compile(
    r"\b(?:let'?s think|wait[,\s!]|can we\b|what if\b|the prompt says\b|"
    r"the benchmark wants\b|is the provided\b|this is incredibly|"
    r"writing a whole PocketLang interpreter|extremely difficult|incredibly smart)\b",
    re.I,
)
PRODUCTIVE_COMMAND_PATTERNS = [
    re.compile(r"(?:^|[;&|]\s*)\.?/compile\.sh\b"),
    re.compile(r"\b(?:cc|gcc|clang|make|cmake|ninja)\b"),
    re.compile(r"\b(?:cat|tee|printf|echo)\b[\s\S]*(?:>|>>)\s*(?:\./)?[\w./-]+\.(?:c|h|py|pk|sh|md)\b"),
    re.compile(r"\b(?:sed\s+-i|perl\s+-0pi)\b"),
    re.compile(r"\bpython3?\b[\s\S]*(?:write_text|open\s*\([\s\S]*[\"']w|Path\s*\([\s\S]*\)\.write_text)"),
]
SOURCE_WRITE_COMMAND_PATTERNS = [
    re.compile(r"(?:>|>>)\s*(?:\./)?(?!AGENT_REPORT\b)[\w./-]+\.(?:c|h|py|pk)\b", re.I),
    re.compile(r"\b(?:touch|cp)\b[\s\S]*(?:\./)?(?!AGENT_REPORT\b)[\w./-]+\.(?:c|h|py|pk)\b", re.I),
    re.compile(r"\b(?:sed\s+-i|perl\s+-0pi)\b[\s\S]*(?:\./)?(?!AGENT_REPORT\b)[\w./-]+\.(?:c|h|py|pk)\b", re.I),
    re.compile(r"\bpython3?\b[\s\S]*(?:write_text|open\s*\([\s\S]*[\"']w|Path\s*\([\s\S]*\)\.write_text)[\s\S]*(?:\.c|\.h|\.py|\.pk)", re.I),
]
BUILD_COMMAND_PATTERN = re.compile(r"(?:^|[;&|]\s*)\.?/compile\.sh\b|\b(?:cc|gcc|clang|make|cmake|ninja)\b", re.I)
ORACLE_COMMAND_PATTERN = re.compile(r"(^|[\s;&|])(?:\./)?executable(\s|$)", re.I)
CANDIDATE_COMMAND_PATTERN = re.compile(r"(^|[\s;&|])(?:\./)?candidate(\s|$)", re.I)
SUBMIT_TOKEN = "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"
SUBMIT_COMMAND_PATTERN = re.compile(
    r"(?:^|[\n;&|]\s*)(?:echo|printf)\s+(?:-[^\s]+\s+)*(?:[\"'])?"
    + re.escape(SUBMIT_TOKEN)
    + r"(?:[\"'])?(?:\s|[;&|]|$)"
)


class ConsoleProgress:
    def update_instance_status(self, instance_id: str, status: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {instance_id}: {status}", flush=True)


def require_model_credentials(model: str) -> None:
    if "gemini" in model.lower() and not any(os.getenv(key) for key in GEMINI_KEYS):
        keys = ", ".join(GEMINI_KEYS)
        raise SystemExit(
            f"Refusing to start Gemini run: none of {keys} is set in this shell. "
            "Export a key, then rerun this command."
        )


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer, got {value!r}") from exc


def parse_tool_choice(value: str) -> str | dict[str, Any] | None:
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.lower() in {"bash", "function:bash"}:
        return {"type": "function", "function": {"name": "bash"}}
    if normalized.startswith("{"):
        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"MINISWE_TOOL_CHOICE is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise SystemExit("MINISWE_TOOL_CHOICE JSON must decode to an object")
        return parsed
    return normalized


def compact_tool_call_id(tool_call_id: Any) -> Any:
    if not isinstance(tool_call_id, str):
        return tool_call_id
    if len(tool_call_id) <= 80 and "__thought__" not in tool_call_id:
        return tool_call_id
    digest = hashlib.sha256(tool_call_id.encode("utf-8")).hexdigest()[:16]
    return f"tc_{digest}"


def strip_gemini_message_payloads(message: dict[str, Any]) -> dict[str, Any]:
    """Drop Gemini thought-signature fields that otherwise balloon context."""
    msg = copy.deepcopy(message)
    msg.pop("provider_specific_fields", None)
    msg.pop("thinking_blocks", None)
    msg.pop("reasoning_content", None)
    if msg.get("function_call") is None:
        msg.pop("function_call", None)
    if msg.get("images") == []:
        msg.pop("images", None)

    if "tool_call_id" in msg:
        msg["tool_call_id"] = compact_tool_call_id(msg["tool_call_id"])

    for tool_call in msg.get("tool_calls") or []:
        if not isinstance(tool_call, dict):
            continue
        tool_call.pop("provider_specific_fields", None)
        if "id" in tool_call:
            tool_call["id"] = compact_tool_call_id(tool_call["id"])

    extra = msg.get("extra")
    if isinstance(extra, dict):
        extra.pop("response", None)
        for action in extra.get("actions") or []:
            if isinstance(action, dict) and "tool_call_id" in action:
                action["tool_call_id"] = compact_tool_call_id(action["tool_call_id"])
    return msg


def install_gemini_context_guards(model: Any) -> None:
    """Keep Gemini provider-specific thought metadata out of subsequent turns."""
    original_prepare = model._prepare_messages_for_api
    original_query = model.query
    repair_state = {"missing_tool_calls": 0}

    def guarded_prepare(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        stripped = [strip_gemini_message_payloads(message) for message in messages]
        return original_prepare(stripped)

    def guarded_query(messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        try:
            response = strip_gemini_message_payloads(original_query(messages, **kwargs))
        except FormatError as exc:
            repair_state["missing_tool_calls"] += 1
            if repair_state["missing_tool_calls"] > MAX_FORMAT_REPAIR_COMMANDS:
                return synthesize_missing_tool_call_response(
                    f"echo {SUBMIT_TOKEN}",
                    repair_state["missing_tool_calls"],
                    format_error_messages=list(exc.messages),
                )
            command = FORMAT_REPAIR_COMMANDS[
                (repair_state["missing_tool_calls"] - 1) % len(FORMAT_REPAIR_COMMANDS)
            ]
            return synthesize_missing_tool_call_response(
                command,
                repair_state["missing_tool_calls"],
                format_error_messages=list(exc.messages),
            )
        if has_bash_tool_call(response):
            repair_state["missing_tool_calls"] = 0
            return response

        repair_state["missing_tool_calls"] += 1
        if repair_state["missing_tool_calls"] > MAX_FORMAT_REPAIR_COMMANDS:
            return synthesize_missing_tool_call_response(
                f"echo {SUBMIT_TOKEN}",
                repair_state["missing_tool_calls"],
            )
        command = FORMAT_REPAIR_COMMANDS[
            (repair_state["missing_tool_calls"] - 1) % len(FORMAT_REPAIR_COMMANDS)
        ]
        return synthesize_missing_tool_call_response(command, repair_state["missing_tool_calls"])

    model._prepare_messages_for_api = guarded_prepare
    model.query = guarded_query


def has_bash_tool_call(response: dict[str, Any]) -> bool:
    for tool_call in response.get("tool_calls") or []:
        function = tool_call.get("function") if isinstance(tool_call, dict) else None
        if isinstance(function, dict) and function.get("name") == "bash":
            return True
    return False


def synthesize_missing_tool_call_response(
    command: str,
    repair_count: int,
    *,
    format_error_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tool_call_id = f"tc_format_repair_{repair_count}_{int(time.time() * 1000)}"
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "index": 0,
                "function": {"arguments": json.dumps({"command": command}), "name": "bash"},
                "id": tool_call_id,
                "type": "function",
            }
        ],
        "extra": {
            "actions": [{"command": command, "tool_call_id": tool_call_id}],
            "format_repair": "format_error_to_bash_tool_call",
            "format_error_messages": [strip_gemini_message_payloads(msg) for msg in (format_error_messages or [])],
            "repair_command": command,
            "cost": 0.0,
            "timestamp": time.time(),
        },
    }


def redirected_source_paths(command: str) -> list[str]:
    return [match.group("path").lstrip("./") for match in SOURCE_REDIRECT_PATTERN.finditer(command)]


def scratchpad_source_command_reason(command: str) -> str | None:
    paths = redirected_source_paths(command)
    if not paths:
        return None

    for path in paths:
        name = Path(path).name
        if name.startswith(("test_", "tmp_", "scratch_")) or name in {"test.c", "parser.py", "eval.py"}:
            return (
                f"throwaway source file {path!r} is disallowed; write persistent implementation "
                "source such as main.c or runtime files that will remain in the submission"
            )
        rm_pattern = re.compile(r"\brm\b[^\n;&|]*\b(?:\./)?" + re.escape(path) + r"\b", re.I)
        if rm_pattern.search(command):
            return (
                f"source file {path!r} is removed in the same command and does not count as "
                "implementation"
            )

    comment_hits = sum(1 for line in command.splitlines() if SCRATCHPAD_COMMENT_PATTERN.search(line))
    phrase_hits = len(SCRATCHPAD_PHRASE_PATTERN.findall(command))
    if comment_hits >= 3 or phrase_hits >= 4:
        return (
            "scratchpad-style source heredocs/comments are disallowed; put reasoning in the "
            "assistant response and write implementation code directly"
        )

    return None


def disallowed_command_reason(command: str) -> str | None:
    scratchpad_reason = scratchpad_source_command_reason(command)
    if scratchpad_reason:
        return scratchpad_reason
    for pattern, reason in DISALLOWED_COMMAND_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def is_productive_command(command: str) -> bool:
    return any(pattern.search(command) for pattern in PRODUCTIVE_COMMAND_PATTERNS)


def is_source_write_command(command: str) -> bool:
    return any(pattern.search(command) for pattern in SOURCE_WRITE_COMMAND_PATTERNS)


def is_build_command(command: str) -> bool:
    return bool(BUILD_COMMAND_PATTERN.search(command))


def is_oracle_command(command: str) -> bool:
    return bool(ORACLE_COMMAND_PATTERN.search(command))


def is_candidate_command(command: str) -> bool:
    return bool(CANDIDATE_COMMAND_PATTERN.search(command))


def is_submit_command(command: str) -> bool:
    return SUBMIT_TOKEN in command and bool(SUBMIT_COMMAND_PATTERN.search(command))


def blocked_command_response(reason: str) -> dict[str, Any]:
    return {
        "output": (
            f"Blocked by benchmark guard: {reason}.\n"
            "Stop repeating observation-only commands. Your next useful step should "
            "write or edit replacement source, run ./compile.sh, record limitations in "
            "AGENT_REPORT.md, or submit with echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT.\n"
        ),
        "returncode": 126,
        "exception_info": "",
        "extra": {"blocked_by_benchmark_guard": True, "reason": reason},
    }


def workspace_implementation_summary(execute: Any) -> dict[str, int | str]:
    script = f"""python3 - <<'PY'
from pathlib import Path
import re
suffixes = {{'.c', '.h', '.py', '.pk', '.sh'}}
excluded = {{'AGENT_REPORT.md'}}
files = []
total = 0
text_parts = []
for path in Path('.').rglob('*'):
    if not path.is_file() or path.name in excluded or path.parts[0] in {{'docs'}}:
        continue
    if path.suffix in suffixes:
        try:
            size = path.stat().st_size
            total += size
            files.append(str(path))
            text_parts.append(path.read_text(errors='ignore')[:50000])
        except OSError:
            pass
text = '\\n'.join(text_parts)
keywords = re.findall(r'\\b(?:parse|parser|lexer|token|eval|evaluate|list|map|table|string|number|function|closure|class|fiber|module|stack|Value|AST|Expr|pocketlang|POCKETLANG|bytecode|vm)\\b', text, re.I)
print(f"source_count={{len(files)}}")
print(f"total_bytes={{total}}")
print(f"keyword_hits={{len(keywords)}}")
print("files=" + ",".join(files[:20]))
PY"""
    result = execute({"command": script})
    summary: dict[str, int | str] = {
        "source_count": 0,
        "total_bytes": 0,
        "keyword_hits": 0,
        "files": "",
    }
    for line in str(result.get("output", "")).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"source_count", "total_bytes", "keyword_hits"}:
            try:
                summary[key] = int(value)
            except ValueError:
                summary[key] = 0
        elif key == "files":
            summary[key] = value
    return summary


def workspace_has_nontrivial_implementation(execute: Any) -> tuple[bool, str]:
    summary = workspace_implementation_summary(execute)
    source_count = int(summary["source_count"])
    total_bytes = int(summary["total_bytes"])
    keyword_hits = int(summary["keyword_hits"])
    files = str(summary["files"])
    ok = source_count > 0 and total_bytes >= MIN_IMPLEMENTATION_BYTES and keyword_hits >= 3
    evidence = (
        f"source_count={source_count}, total_bytes={total_bytes}, "
        f"keyword_hits={keyword_hits}, files={files or '<none>'}"
    )
    return ok, evidence


def command_returncode(result: dict[str, Any], default: int = 1) -> int:
    try:
        return int(result.get("returncode", default))
    except (TypeError, ValueError):
        return default


def candidate_source_passes_integrity_gate(execute: Any) -> tuple[bool, str]:
    script = f"""python3 - <<'PY'
from pathlib import Path
import json
import re
needles = json.loads({json.dumps(POCKETLANG_GATE_HARDCODE_NEEDLES)!r})
hardcode_regexes = [re.compile(pattern) for pattern in json.loads({json.dumps(POCKETLANG_GATE_HARDCODE_REGEXES)!r})]
delegate_regexes = [re.compile(pattern, re.I) for pattern in json.loads({json.dumps(POCKETLANG_GATE_DELEGATION_REGEXES)!r})]
suffixes = {{'.c', '.h', '.py', '.pk', '.sh'}}
excluded = {{'AGENT_REPORT.md'}}

def parameter_names(param_text):
    names = []
    for raw_param in param_text.split(','):
        param = raw_param.strip()
        if not param or param == 'void':
            continue
        param = param.replace('*', ' ')
        match = re.search(r'([A-Za-z_]\\w*)\\s*(?:\\[[^\\]]*\\])?\\s*$', param)
        if match:
            names.append(match.group(1))
    return names

def command_tainted_identifiers(text):
    tainted = set()
    direct_argv = r'argv\\s*\\[\\s*(?:[2-9]|[0-9][0-9]+)\\s*\\]'
    ident = r'([A-Za-z_]\\w*)'

    for match in re.finditer(r'\\b(?:const\\s+)?char\\s*\\*+\\s*' + ident + r'\\s*=\\s*' + direct_argv, text):
        tainted.add(match.group(1))
    for match in re.finditer(r'\\b' + ident + r'\\s*=\\s*' + direct_argv, text):
        tainted.add(match.group(1))

    function_params = {{}}
    function_def = re.compile(
        r'(?:^|\\n)\\s*(?:static\\s+)?[A-Za-z_][\\w\\s\\*]*\\s+([A-Za-z_]\\w*)\\s*\\(([^;{{}}()]*)\\)\\s*\\{{',
        re.S,
    )
    for match in function_def.finditer(text):
        function_params[match.group(1)] = parameter_names(match.group(2))

    call_with_argv = re.compile(r'\\b([A-Za-z_]\\w*)\\s*\\(\\s*' + direct_argv)
    for match in call_with_argv.finditer(text):
        params = function_params.get(match.group(1), [])
        if params:
            tainted.add(params[0])

    changed = True
    while changed:
        changed = False
        for name in list(tainted):
            escaped = re.escape(name)
            propagation_patterns = [
                r'\\b(?:const\\s+)?char\\s*\\*+\\s*' + ident + r'\\s*=\\s*' + escaped + r'\\b',
                r'\\b' + ident + r'\\s*=\\s*' + escaped + r'\\b',
                r'\\b(?:strcpy|strncpy|memcpy|memmove|snprintf)\\s*\\(\\s*' + ident + r'\\s*,[^;]*\\b' + escaped + r'\\b',
                r'\\b' + ident + r'\\s*\\[[^\\]]+\\]\\s*=\\s*' + escaped + r'\\s*\\[',
            ]
            for pattern in propagation_patterns:
                for match in re.finditer(pattern, text, re.S):
                    new_name = match.group(1)
                    if new_name not in tainted:
                        tainted.add(new_name)
                        changed = True
    return tainted

def tainted_command_dispatch_hits(text):
    tainted = command_tainted_identifiers(text)
    if not tainted:
        return 0
    escaped_names = '|'.join(sorted(re.escape(name) for name in tainted))
    hits = 0
    substring_pattern = re.compile(
        r'\\b(?:strstr|strcasestr|memmem)\\s*\\(\\s*(?:' + escaped_names + r')\\b',
        re.I,
    )
    hits += len(substring_pattern.findall(text))

    whole_input_names = [
        name for name in tainted
        if re.search(r'(?:cmd|command|input|source|src|program|script|line|text|buffer|buf|cleaned|normalized|sanitized)', name, re.I)
    ]
    if whole_input_names:
        whole_alt = '|'.join(sorted(re.escape(name) for name in whole_input_names))
        equality_pattern = re.compile(
            r'\\b(?:strcmp|strncmp|memcmp)\\s*\\(\\s*(?:' + whole_alt + r')\\b',
            re.I,
        )
        hits += len(equality_pattern.findall(text))
    return hits

literal_hits = 0
hardcode_hits = 0
delegate_hits = 0
tainted_dispatch_hits = 0
files = set()
for path in Path('.').rglob('*'):
    if not path.is_file() or path.name in excluded or path.parts[0] in {{'docs'}}:
        continue
    if path.suffix not in suffixes:
        continue
    try:
        text = path.read_text(errors='ignore')
    except OSError:
        continue
    if path.name == 'compile.sh' and text.startswith('#!'):
        text = '\\n'.join(text.splitlines()[1:])
    for needle in needles:
        if needle in text:
            literal_hits += 1
            files.add(str(path))
    for pattern in hardcode_regexes:
        if pattern.search(text):
            hardcode_hits += 1
            files.add(str(path))
    tainted_hits = tainted_command_dispatch_hits(text)
    if tainted_hits:
        tainted_dispatch_hits += tainted_hits
        files.add(str(path))
    for pattern in delegate_regexes:
        if pattern.search(text):
            delegate_hits += 1
            files.add(str(path))
print(f"literal_hits={{literal_hits}}")
print(f"hardcode_hits={{hardcode_hits}}")
print(f"tainted_dispatch_hits={{tainted_dispatch_hits}}")
print(f"delegate_hits={{delegate_hits}}")
print("files=" + ",".join(sorted(files)[:20]))
PY"""
    result = execute({"command": script})
    summary: dict[str, int | str] = {
        "literal_hits": 0,
        "hardcode_hits": 0,
        "tainted_dispatch_hits": 0,
        "delegate_hits": 0,
        "files": "",
    }
    for line in str(result.get("output", "")).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"literal_hits", "hardcode_hits", "tainted_dispatch_hits", "delegate_hits"}:
            try:
                summary[key] = int(value)
            except ValueError:
                summary[key] = 0
        elif key == "files":
            summary[key] = value

    literal_hits = int(summary["literal_hits"])
    hardcode_hits = int(summary["hardcode_hits"])
    tainted_dispatch_hits = int(summary["tainted_dispatch_hits"])
    delegate_hits = int(summary["delegate_hits"])
    files = str(summary["files"])
    ok = literal_hits == 0 and hardcode_hits == 0 and tainted_dispatch_hits == 0 and delegate_hits == 0
    evidence = (
        f"literal_eval_hits={literal_hits}, whole-input_match_hits={hardcode_hits}, "
        f"tainted_command_dispatch_hits={tainted_dispatch_hits}, "
        f"runtime_delegation_hits={delegate_hits}, "
        f"files={files or '<none>'}"
    )
    return ok, evidence


def candidate_smoke_command(case: dict[str, Any]) -> str:
    command = str(case.get("command") or " ".join(shlex.quote(str(arg)) for arg in case["argv"]))
    if case.get("command"):
        return f"timeout {CANDIDATE_SMOKE_TIMEOUT_SECONDS}s bash -lc {shlex.quote(command)}"
    return f"timeout {CANDIDATE_SMOKE_TIMEOUT_SECONDS}s {command}"


def candidate_has_basic_pocketlang_behavior(execute: Any) -> tuple[bool, str]:
    exists = execute({"command": "test -x ./candidate"})
    if command_returncode(exists) != 0:
        return False, "./candidate is missing or not executable; run ./compile.sh first"

    failures = []
    for case in POCKETLANG_CANDIDATE_BEHAVIOR_CASES:
        command = candidate_smoke_command(case)
        result = execute({"command": command})
        returncode = command_returncode(result)
        output = str(result.get("output", ""))
        expected_stdout = str(case["stdout"])
        if returncode != 0 or output != expected_stdout:
            failures.append(f"{case['name']}: rc={returncode}")

    if failures:
        preview = "; ".join(failures[:4])
        return False, (
            f"{len(failures)} of {len(POCKETLANG_CANDIDATE_BEHAVIOR_CASES)} generalized smoke "
            f"families failed ({preview})"
        )
    return True, f"{len(POCKETLANG_CANDIDATE_BEHAVIOR_CASES)} generalized smoke families passed"


def strip_prebuilt_executable_from_submission(submission_path: Path) -> None:
    """Remove solver-cleanroom ./executable from the archived submission."""
    if not submission_path.exists():
        return
    tmp_path = submission_path.with_name(submission_path.name + ".tmp")
    removed = False
    with tarfile.open(submission_path, "r:gz") as src, tarfile.open(tmp_path, "w:gz") as dst:
        for member in src.getmembers():
            normalized = member.name.lstrip("./")
            if normalized == "executable":
                removed = True
                continue
            fileobj = src.extractfile(member) if member.isfile() else None
            try:
                dst.addfile(member, fileobj)
            finally:
                if fileobj is not None:
                    fileobj.close()
    tmp_path.replace(submission_path)
    if removed:
        logger.info("Removed prebuilt ./executable from submission archive %s", submission_path)


def install_environment_command_guards(env: Any) -> None:
    """Block oracle abuse and command loops that burn the whole step budget."""
    original_execute = env.execute
    recent_command_count = COMMAND_CYCLE_WINDOW * MAX_REPEATED_COMMAND_CYCLES
    state = {
        "last_command": "",
        "repeat_count": 0,
        "recent_commands": collections.deque(maxlen=recent_command_count),
        "oracle_since_productive": 0,
        "nonproductive_count": 0,
        "command_count": 0,
        "implementation_actions": 0,
        "build_actions": 0,
        "candidate_actions": 0,
        "first_source_command": 0,
        "first_build_command": 0,
        "post_compile_oracle_count": 0,
        "oracle_since_candidate": 0,
    }

    def guarded_execute(action: dict[str, Any]) -> dict[str, Any]:
        command = action.get("command", "")
        if isinstance(command, str):
            state["command_count"] += 1
            normalized = normalize_command(command)
            if normalized and normalized == state["last_command"]:
                state["repeat_count"] += 1
            else:
                state["last_command"] = normalized
                state["repeat_count"] = 1
            if normalized:
                state["recent_commands"].append(normalized)

            reason = disallowed_command_reason(command)
            if reason:
                return blocked_command_response(
                    reason
                    + ". Run ./executable only through its normal CLI/stdin interface; "
                    + "do not read, copy, hash, disassemble, embed, or delegate to it"
                )

            source_write = is_source_write_command(command)
            build = is_build_command(command)
            submit = is_submit_command(command)
            candidate = is_candidate_command(command)
            productive = is_productive_command(command) or source_write or build or candidate
            oracle = is_oracle_command(command)
            if source_write:
                state["implementation_actions"] += 1
                if state["first_source_command"] == 0:
                    state["first_source_command"] = state["command_count"]
            if build:
                state["build_actions"] += 1
                state["oracle_since_candidate"] = 0
                if state["first_build_command"] == 0:
                    state["first_build_command"] = state["command_count"]
            if candidate:
                state["candidate_actions"] += 1
                state["oracle_since_candidate"] = 0

            if submit:
                ok, evidence = workspace_has_nontrivial_implementation(original_execute)
                missing = []
                if not ok:
                    missing.append(f"nontrivial source implementation ({evidence})")
                if state["build_actions"] == 0:
                    missing.append("a compile/build attempt")
                if ok and state["build_actions"] > 0:
                    source_general_ok, source_general_evidence = candidate_source_passes_integrity_gate(
                        original_execute
                    )
                    if not source_general_ok:
                        missing.append(
                            "self-contained generalized implementation without literal smoke hardcoding "
                            "or external runtime delegation "
                            f"({source_general_evidence})"
                        )
                    behavior_ok, behavior_evidence = candidate_has_basic_pocketlang_behavior(original_execute)
                    if not behavior_ok:
                        logger.info(
                            "Candidate behavior smoke is advisory at submit time: %s",
                            behavior_evidence,
                        )
                if missing:
                    return blocked_command_response(
                        "submission rejected before scoring: missing " + " and ".join(missing)
                    )

            if (
                state["command_count"] > OBSERVATION_PHASE_COMMAND_LIMIT
                and not source_write
            ):
                ok, evidence = workspace_has_nontrivial_implementation(original_execute)
                if not ok:
                    return blocked_command_response(
                        f"observation phase exceeded {OBSERVATION_PHASE_COMMAND_LIMIT} commands "
                        f"without persistent source creation ({evidence})"
                    )
            if (
                state["first_source_command"] > 0
                and state["build_actions"] == 0
                and state["command_count"] - state["first_source_command"] > SOURCE_BUILD_GRACE_COMMANDS
                and not source_write
                and not build
            ):
                return blocked_command_response(
                    f"source was first written {state['command_count'] - state['first_source_command']} "
                    "commands ago without compiling the candidate; run ./compile.sh now"
                )
            if (
                state["command_count"] > BUILD_PHASE_COMMAND_LIMIT
                and state["build_actions"] == 0
                and not source_write
                and not build
            ):
                ok, evidence = workspace_has_nontrivial_implementation(original_execute)
                if ok:
                    return blocked_command_response(
                        f"build phase exceeded {BUILD_PHASE_COMMAND_LIMIT} commands without compiling the candidate"
                    )
                return blocked_command_response(
                    f"build phase exceeded {BUILD_PHASE_COMMAND_LIMIT} commands without nontrivial source "
                    f"or a candidate compile ({evidence})"
                )
            if state["build_actions"] > 0 and oracle:
                if state["candidate_actions"] == 0:
                    return blocked_command_response(
                        "oracle queried after compiling before any ./candidate run; "
                        "test the compiled candidate first"
                    )
                if state["post_compile_oracle_count"] >= POST_COMPILE_ORACLE_LIMIT:
                    return blocked_command_response(
                        f"post-compile oracle budget exceeded ({POST_COMPILE_ORACLE_LIMIT} calls); "
                        "debug ./candidate or submit the best compiled implementation"
                    )
                if state["oracle_since_candidate"] >= ORACLE_BURST_AFTER_CANDIDATE_LIMIT:
                    return blocked_command_response(
                        f"more than {ORACLE_BURST_AFTER_CANDIDATE_LIMIT} oracle calls since the last "
                        "./candidate check; reproduce the behavior in source and test ./candidate"
                    )
                state["post_compile_oracle_count"] += 1
                state["oracle_since_candidate"] += 1

            if productive:
                state["oracle_since_productive"] = 0
                state["nonproductive_count"] = 0
            else:
                state["nonproductive_count"] += 1
                if oracle:
                    state["oracle_since_productive"] += 1

            if state["repeat_count"] > MAX_CONSECUTIVE_IDENTICAL_COMMANDS:
                return blocked_command_response(
                    f"same command repeated {state['repeat_count']} consecutive times"
                )
            recent_commands = list(state["recent_commands"])
            if len(recent_commands) == recent_command_count:
                cycle = recent_commands[-COMMAND_CYCLE_WINDOW:]
                if len(set(cycle)) > 1 and cycle * MAX_REPEATED_COMMAND_CYCLES == recent_commands:
                    return blocked_command_response(
                        "same command cycle repeated "
                        f"{MAX_REPEATED_COMMAND_CYCLES} times: " + " -> ".join(cycle)
                    )
            if oracle and state["oracle_since_productive"] > ORACLE_ONLY_STAGNATION_LIMIT:
                return blocked_command_response(
                    f"{state['oracle_since_productive']} oracle commands since the last source/build action"
                )
            if state["nonproductive_count"] > NONPRODUCTIVE_COMMAND_LIMIT:
                return blocked_command_response(
                    f"{state['nonproductive_count']} nonproductive commands since the last source/build action"
                )

        return original_execute(action)

    env.execute = guarded_execute


def observation_template(char_limit: int) -> str:
    head = max(1000, char_limit // 2)
    tail = max(1000, char_limit - head)
    return f"""{{% if output.exception_info is defined and output.exception_info -%}}
<exception>{{{{output.exception_info}}}}</exception>
{{% endif -%}}
<returncode>{{{{output.returncode}}}}</returncode>
{{% if output.output | length < {char_limit} -%}}
<output>
{{{{ output.output -}}}}
</output>
{{%- else -%}}
<warning>
The output of your last command was too long. Use head, tail, sed, or a narrower search.
</warning>
{{%- set elided_chars = output.output | length - {char_limit} -%}}
<output_head>
{{{{ output.output[:{head}] }}}}
</output_head>
<elided_chars>
{{{{ elided_chars }}}} characters elided
</elided_chars>
<output_tail>
{{{{ output.output[-{tail}:] }}}}
</output_tail>
{{%- endif -%}}
{{% if step_limit > 0 and step_limit - n_model_calls < 20 -%}}

<IMPORTANT>
There is a limit to the steps you can take. You are now {{{{ step_limit - n_model_calls }}}} steps away from reaching your limit. Focus on making the solution compile, write remaining limitations to AGENT_REPORT.md, then submit.
</IMPORTANT>
{{%- endif %}}
{{% if wall_time_limit_seconds > 0 and wall_time_limit_seconds - elapsed_seconds < 600 -%}}

<IMPORTANT>
You are running low on time. Ensure the solution compiles, write remaining limitations to AGENT_REPORT.md, then submit.
</IMPORTANT>
{{%- endif %}}
"""


def format_error_template() -> str:
    return """{% if finish_reason is defined and finish_reason in ["length", "tool_calls"] -%}
Your previous response reached the output token limit (finish_reason={{ finish_reason }}) before a bash tool call was accepted. Be brief and end with exactly one bash tool call.
{%- else -%}
Tool call error:

<error>
{{error}}
</error>

Your next response must contain exactly one bash tool call. Do not answer with prose only. If you are stuck, run a small concrete command such as `ls -la`, `./compile.sh`, or `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`.
{%- endif %}"""


def normalize_instance_template(template: str) -> str:
    replacements = {
        "Finally, commit your changes.": (
            "Do not run git init, git add, or git commit. The benchmark captures "
            "the workspace automatically after you submit."
        ),
        (
            "- You SHOULD extensively test the executable to understand its behavior before writing code.\n"
            "  If you are dealing with a TUI, tmux/libtmux has been installed to help you test/inspect/it."
        ): (
            "- Do a short finite observation pass, then implement. After source exists, prefer ./candidate; "
            "query ./executable only for one narrow failing behavior at a time."
        ),
    }
    for old, new in replacements.items():
        template = template.replace(old, new)
    return template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="programbench-pocketlang-cleanroom:local")
    parser.add_argument("--output", type=Path, default=Path(f"runs/pocketlang_miniswe_{int(time.time())}"))
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-class", default="litellm")
    parser.add_argument("--max-tokens", type=int, default=env_int("MINISWE_MAX_TOKENS", DEFAULT_MAX_TOKENS))
    parser.add_argument("--reasoning-effort", default=os.getenv("MINISWE_REASONING_EFFORT", DEFAULT_REASONING_EFFORT))
    parser.add_argument(
        "--tool-choice",
        default=os.getenv("MINISWE_TOOL_CHOICE", ""),
        help="Optional LiteLLM tool_choice override, for example 'required' or 'bash' to force the named bash function.",
    )
    parser.add_argument(
        "--observation-char-limit",
        type=int,
        default=env_int("MINISWE_OBSERVATION_CHAR_LIMIT", DEFAULT_OBSERVATION_CHAR_LIMIT),
    )
    parser.add_argument("--config", action="append", default=[], help="Extra mini-SWE config spec.")
    parser.add_argument("--step-limit", type=int, default=env_int("MINISWE_STEP_LIMIT", DEFAULT_STEP_LIMIT))
    parser.add_argument("--cost-limit", type=float, default=0.0)
    parser.add_argument(
        "--wall-time-limit-seconds",
        type=int,
        default=env_int("MINISWE_WALL_TIME_LIMIT_SECONDS", DEFAULT_WALL_TIME_LIMIT_SECONDS),
    )
    parser.add_argument("--cpus", default="4")
    parser.add_argument("--memory", default="8g")
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--skip-key-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.skip_key_check:
        require_model_credentials(args.model)

    instance_dir = args.output / INSTANCE_ID
    traj_path = instance_dir / f"{INSTANCE_ID}.traj.json"
    submission_path = instance_dir / "submission.tar.gz"
    if submission_path.exists() and not args.redo_existing:
        raise SystemExit(f"{submission_path} already exists; pass --redo-existing to replace it.")

    args.output.mkdir(parents=True, exist_ok=True)
    instance_dir.mkdir(parents=True, exist_ok=True)
    add_file_handler(args.output / "minisweagent.log")

    model_kwargs = {
        "max_tokens": args.max_tokens,
        "reasoning_effort": args.reasoning_effort,
    }
    tool_choice = parse_tool_choice(args.tool_choice)
    if tool_choice is not None:
        model_kwargs["tool_choice"] = tool_choice

    configs = [get_config_from_spec(DEFAULT_CONFIG), *(get_config_from_spec(spec) for spec in args.config)]
    configs.append(
        {
            "agent": {
                "step_limit": args.step_limit,
                "cost_limit": args.cost_limit,
                "wall_time_limit_seconds": args.wall_time_limit_seconds,
            },
            "environment": {
                "image": args.image,
                "run_args": [
                    "--platform",
                    "linux/amd64",
                    "--rm",
                    "--network",
                    "none",
                    "--cpus",
                    args.cpus,
                    "--memory",
                    args.memory,
                    "--memory-swap",
                    args.memory,
                    "--user",
                    "agent",
                    "--cap-drop",
                    "SYS_PTRACE",
                ],
            },
            "model": {
                "model_name": args.model,
                "model_class": args.model_class or UNSET,
                "model_kwargs": model_kwargs,
                "format_error_template": format_error_template(),
                "observation_template": observation_template(args.observation_char_limit),
                "cost_tracking": "ignore_errors",
            },
        }
    )
    config = recursive_merge(*configs)
    config["agent"]["system_template"] = config["agent"]["system_template"].rstrip() + AGENT_GUARDRAIL_APPENDIX
    config["agent"]["instance_template"] = (
        normalize_instance_template(config["agent"]["instance_template"]).rstrip() + AGENT_GUARDRAIL_APPENDIX
    )

    agent = None
    exit_status = None
    extra_info: dict[str, str] = {}
    try:
        model = get_model(config=copy.deepcopy(config.get("model", {})))
        if "gemini" in args.model.lower():
            install_gemini_context_guards(model)
        env = get_environment(copy.deepcopy(config.get("environment", {})), default_type="docker")
        install_environment_command_guards(env)
        env.execute({"command": 'git config user.name "mini-swe-agent" && git config user.email "mini-swe-agent@proton.me"'})

        agent_config = dict(config.get("agent", {}))
        agent_config["output_path"] = traj_path
        agent = ProgramBenchAgent(
            model,
            env,
            progress_manager=ConsoleProgress(),
            instance_id=INSTANCE_ID,
            **agent_config,
        )
        agent.extra_template_vars = {
            "instance": {
                "instance_id": INSTANCE_ID,
                "image_name": args.image,
                "source": "local-reproduced-pocketlang-cleanroom",
            }
        }
        exit_status = agent.run().get("exit_status")
    except Exception as exc:
        logger.error("Error processing %s: %s", INSTANCE_ID, exc, exc_info=True)
        exit_status = type(exc).__name__
        extra_info = {"traceback": traceback.format_exc(), "exception_str": str(exc)}
        if agent is None:
            print(extra_info["traceback"], file=sys.stderr)
    finally:
        if agent is not None:
            try:
                copy_submission(agent.env, submission_path)
                strip_prebuilt_executable_from_submission(submission_path)
            except Exception as exc:
                logger.error("Failed to copy submission for %s: %s", INSTANCE_ID, exc, exc_info=True)
                extra_info["submission_copy_error"] = str(exc)
            agent.save(traj_path, {"info": {"exit_status": exit_status, **extra_info}, "instance_id": INSTANCE_ID})
            agent.env.cleanup()

    print(f"exit_status={exit_status}")
    print(f"trajectory={traj_path}")
    print(f"submission={submission_path if submission_path.exists() else 'not-created'}")
    return 0 if submission_path.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
