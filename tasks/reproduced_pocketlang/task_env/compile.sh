#!/usr/bin/env bash
set -euo pipefail

# Build the solver's replacement executable.
#
# In the solver cleanroom, ./executable starts as the protected black-box oracle.
# While that oracle is present, this template builds ./candidate so observation
# can continue after compile/test cycles. The evaluator removes any submitted
# executable before running compile.sh, so the same script builds ./executable
# during final scoring.
out=executable
if [[ -e executable && ! -w executable ]]; then
  out=candidate
  echo "protected oracle detected at ./executable; building ./$out for development checks" >&2
fi

sources=()
while IFS= read -r -d '' source; do
  sources+=("$source")
done < <(find . -maxdepth 3 -type f -name '*.c' -not -path './build/*' -not -path './obj/*' -print0 | sort -z)

if [[ ${#sources[@]} -eq 0 ]]; then
  echo "no C source files found; add a replacement implementation before compiling" >&2
  exit 2
fi

cc -O2 -std=c99 -Wall -Wextra -I. -o "$out" "${sources[@]}" -lm -ldl

if [[ "$out" != executable ]]; then
  echo "run ./$out to test your candidate; final scoring will build ./executable" >&2
fi
