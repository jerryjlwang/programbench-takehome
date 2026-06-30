#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
IMAGE="${IMAGE:-programbench-lua-cleanroom:local}"
MODEL="${MODEL:-gemini/gemini-3.5-flash}"
OUTPUT="${OUTPUT:-$ROOT/runs/lua_miniswe_$(date +%Y%m%d_%H%M%S)}"

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

uv run --with mini-swe-agent --with programbench \
  python "$ROOT/tasks/reproduced_lua/scripts/run_miniswe_lua.py" "${args[@]}"
