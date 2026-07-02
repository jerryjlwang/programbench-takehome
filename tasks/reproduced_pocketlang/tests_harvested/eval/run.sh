#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 -m pytest -p no:cacheprovider tests -q --tb=short
