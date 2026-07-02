#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="${IMAGE:-programbench-lua-cleanroom:local}"
MODEL="${MODEL:-gemini/gemini-3.5-flash}"
OUTPUT="${OUTPUT:-$ROOT/runs/lua_miniswe_$(date +%Y%m%d_%H%M%S)}"
MINISWE_MAX_TOKENS="${MINISWE_MAX_TOKENS:-2048}"
MINISWE_REASONING_EFFORT="${MINISWE_REASONING_EFFORT:-none}"
MINISWE_TOOL_CHOICE="${MINISWE_TOOL_CHOICE:-bash}"
MINISWE_OBSERVATION_CHAR_LIMIT="${MINISWE_OBSERVATION_CHAR_LIMIT:-4000}"
MINISWE_STEP_LIMIT="${MINISWE_STEP_LIMIT:-1000}"
MINISWE_WALL_TIME_LIMIT_SECONDS="${MINISWE_WALL_TIME_LIMIT_SECONDS:-7200}"

"$ROOT/tasks/reproduced_lua/scripts/build_miniswe_cleanroom_image.sh" "$IMAGE" >/dev/null

args=("$@")
has_arg() {
  local needle="$1"
  local arg
  ((${#args[@]})) || return 1
  for arg in "${args[@]}"; do
    [[ "$arg" == "$needle" ]] && return 0
  done
  return 1
}

prepend_arg_pair() {
  local key="$1"
  local value="$2"
  if ((${#args[@]})); then
    args=("$key" "$value" "${args[@]}")
  else
    args=("$key" "$value")
  fi
}

if ! has_arg "--model" && ! has_arg "-m"; then
  prepend_arg_pair --model "$MODEL"
fi
if ! has_arg "--image"; then
  prepend_arg_pair --image "$IMAGE"
fi
if ! has_arg "--output"; then
  prepend_arg_pair --output "$OUTPUT"
fi
if ! has_arg "--max-tokens"; then
  prepend_arg_pair --max-tokens "$MINISWE_MAX_TOKENS"
fi
if ! has_arg "--reasoning-effort"; then
  prepend_arg_pair --reasoning-effort "$MINISWE_REASONING_EFFORT"
fi
if [[ -n "$MINISWE_TOOL_CHOICE" ]] && ! has_arg "--tool-choice"; then
  prepend_arg_pair --tool-choice "$MINISWE_TOOL_CHOICE"
fi
if ! has_arg "--observation-char-limit"; then
  prepend_arg_pair --observation-char-limit "$MINISWE_OBSERVATION_CHAR_LIMIT"
fi
if ! has_arg "--step-limit"; then
  prepend_arg_pair --step-limit "$MINISWE_STEP_LIMIT"
fi
if ! has_arg "--wall-time-limit-seconds"; then
  prepend_arg_pair --wall-time-limit-seconds "$MINISWE_WALL_TIME_LIMIT_SECONDS"
fi

uv run --with mini-swe-agent --with programbench \
  python "$ROOT/tasks/reproduced_lua/scripts/run_miniswe_lua.py" "${args[@]}"
