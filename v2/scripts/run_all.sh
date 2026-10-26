#!/usr/bin/env bash
# Full v2 experiment sweep. Every episode is a real OpenAI Responses API run.
# Episodes already on disk are skipped, so the script can be re-run to resume.
set -euo pipefail
cd "$(dirname "$0")/.."
R="python3 -m lexcollude_v2.runner"
S5="0 1 2 3 4"
S10="0 1 2 3 4 5 6 7 8 9"

tender_grid () {  # $1 model  $2 seeds  $3 out
  $R tender --models "$1" --n-firms 2 3 5 --channels none --seeds $2 --out "$3"
  $R tender --models "$1" --n-firms 3 --channels none_compliance forum forum_monitored instructed --seeds $2 --out "$3"
  $R tender --models "$1" --n-firms 3 --channels none --rival-policy nash_bot --seeds $2 --out "$3"
  $R tender --models "$1" --n-firms 3 --channels none --deviation-round 14 --seeds $2 --out "$3"
}
classaction_grid () {  # $1 model  $2 seeds  $3 out
  $R classaction --models "$1" --k-firms 1 2 3 --compensation fee_linked fixed --monitoring private --seeds $2 --out "$3"
  $R classaction --models "$1" --k-firms 1 3 --compensation fee_linked --monitoring transcript_visible --seeds $2 --out "$3"
}

case "${1:-all}" in
  tender-sol)   tender_grid gpt-6-sol  "$S5" data/tender_main ;;
  tender-luna)  tender_grid gpt-6-luna "$S5" data/tender_main ;;
  tender-astra) $R tender --models gpt-6-astra --n-firms 3 --channels none forum --seeds 0 1 2 --out data/tender_main ;;
  ca-sol)       classaction_grid gpt-6-sol  "$S10" data/classaction_main ;;
  ca-luna)      classaction_grid gpt-6-luna "$S10" data/classaction_main ;;
  ca-astra)     $R classaction --models gpt-6-astra --k-firms 1 3 --compensation fee_linked fixed --seeds 0 1 2 3 --out data/classaction_main ;;
  *) echo "usage: $0 {tender-sol|tender-luna|tender-astra|ca-sol|ca-luna|ca-astra}"; exit 1 ;;
esac

# --- v3 Scenario C: redline document-leak leaderboard (added post-sprint) ---
