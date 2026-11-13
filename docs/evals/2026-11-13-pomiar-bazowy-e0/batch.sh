#!/usr/bin/env bash
# Pomiar bazowy E0: 3 historyjki × 5 powtórzeń, kolejno; stop, gdy łączny koszt przekroczy LIMIT (USD).
# Płatne — uruchamiaj tylko za zgodą człowieka. Wyniki: $E0_OUT/results.jsonl.
HERE="$(cd "$(dirname "$0")" && pwd)"
export E0_OUT="${E0_OUT:-$(mktemp -d)}"
cd "$E0_OUT"
LIMIT="${LIMIT:-15}"
for rep in 1 2 3 4 5; do
  for story in S1 S2 S3; do
    spent=$(python3 -c "
import json,os
print(sum((json.loads(l).get('cost_usd') or 0) for l in open('results.jsonl')) if os.path.exists('results.jsonl') else 0)")
    if python3 -c "import sys; sys.exit(0 if float('$spent') >= $LIMIT else 1)"; then echo "STOP: koszt $spent >= $LIMIT"; exit 0; fi
    python3 "$HERE/e0_run.py" $story $rep --model sonnet --budget 3 --timeout 1800 > runs-$story-$rep.log 2>&1
    echo "$story r$rep done, spent before: $spent"
  done
done
echo "ALL DONE"
