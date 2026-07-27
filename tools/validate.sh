#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/doc_harness.py" validate --strict
