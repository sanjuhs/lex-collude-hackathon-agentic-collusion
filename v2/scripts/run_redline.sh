#!/usr/bin/env bash
# Scenario C leaderboard: every model, all three tiers, 5 seeds. Real API + real .docx.
set -euo pipefail
cd "$(dirname "$0")/.."
R="python3 -m lexcollude_v2.runner redline --tiers tier1_inadvertent tier2_incentive tier3_instructed --seeds 0 1 2 3 4 --rounds 2 --out data/redline_main"
for m in "$@"; do $R --models "$m"; done
