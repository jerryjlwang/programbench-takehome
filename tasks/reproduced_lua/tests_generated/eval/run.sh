#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pytest -p no:cacheprovider "$HERE/tests" -v --tb=short
