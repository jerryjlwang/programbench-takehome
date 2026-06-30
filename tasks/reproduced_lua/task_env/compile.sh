#!/usr/bin/env bash
set -euo pipefail

# Build the solver's replacement executable at ./executable.
# Fill this in during a ProgramBench solver run.
cc -O2 -std=c99 -o executable *.c -lm -ldl
