#!/usr/bin/env bash
# LexLeak-Bench full sweep. Each group tracks its own cost and stops at its --budget.
set -euo pipefail
cd "$(dirname "$0")/.."
B="python3 -m lexcollude_v2.bench_runner --out data/leakbench"
