#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ is required"'
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir --no-deps -e .
.venv/bin/python -m lexcollude --help

