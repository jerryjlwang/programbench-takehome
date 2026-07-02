#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TASK_ENV="$ROOT/tasks/reproduced_janet/task_env"
IMAGE="${1:-programbench-janet-cleanroom:local}"

if [[ ! -x "$TASK_ENV/executable" ]]; then
  echo "missing executable oracle at $TASK_ENV/executable" >&2
  exit 1
fi

build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT

mkdir -p "$build_dir/task_env"
cp -R "$TASK_ENV"/. "$build_dir/task_env"/

cat > "$build_dir/Dockerfile" <<'DOCKERFILE'
FROM gcc:13-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends git python3 ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -m -s /bin/bash agent \
  && mkdir -p /workspace \
  && chown agent:agent /workspace

WORKDIR /workspace
COPY task_env/ /workspace/

RUN chown -R agent:agent /workspace \
  && chown root:agent /workspace \
  && chmod 1775 /workspace \
  && chown root:root /workspace/executable \
  && chmod 0111 /workspace/executable \
  && chmod +x /workspace/compile.sh \
  && printf 'executable\ncandidate\n*.o\n*.a\n*.so\n*.dylib\n*.out\n*.jimage\n' > /workspace/.gitignore \
  && chown agent:agent /workspace/.gitignore

USER agent
ENV PAGER=cat \
  MANPAGER=cat \
  LESS=-R \
  PIP_PROGRESS_BAR=off \
  TQDM_DISABLE=1
DOCKERFILE

docker build --platform linux/amd64 -t "$IMAGE" "$build_dir"
printf '%s\n' "$IMAGE"
