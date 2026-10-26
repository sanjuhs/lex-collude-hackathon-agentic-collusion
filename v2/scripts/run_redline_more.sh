#!/usr/bin/env bash
# Extra Scenario C seeds (5-9) to tighten the leaderboard intervals.
set -euo pipefail
cd "$(dirname "$0")/.."
R="python3 -m lexcollude_v2.runner redline --tiers tier1_inadvertent tier2_incentive tier3_instructed --seeds 5 6 7 8 9 --rounds 2 --out data/redline_main"
for m in "$@"; do $R --models "$m"; done
