#!/usr/bin/env bash
# Additional gpt-6-sol replicates (seeds 5-9) for the key Scenario A comparisons,
# added after the first 5-seed sweep showed effects with wide intervals.
set -euo pipefail
cd "$(dirname "$0")/.."
R="python3 -m lexcollude_v2.runner"
S="5 6 7 8 9"
$R tender --models gpt-6-sol --n-firms 3 --channels none none_compliance forum --seeds $S --out data/tender_main
$R tender --models gpt-6-sol --n-firms 3 --channels none --rival-policy nash_bot --seeds $S --out data/tender_main
$R tender --models gpt-6-sol --n-firms 3 --channels none --deviation-round 14 --seeds $S --out data/tender_main
