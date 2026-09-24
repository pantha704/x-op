#!/bin/bash
# run_quote_wave.sh — the ONLY way to launch QUOTE waves (owner directive 2026-09-23:
# the fire arm switches from replies to quotes - quotes count toward verified Home
# Timeline impressions, replies never do). Enforces:
#   * single-flight (flock): reply and quote waves share /tmp/x-fire.lock, so only
#     one posting wave ever runs at a time
# Usage: run_quote_wave.sh <targets.json> [--max N] [--gap-min S] [--gap-max S] [--detach]
#   --detach: nohup the driver, print "detached pid=NNN", return immediately.
set -euo pipefail
if [ $# -lt 1 ]; then echo "usage: run_quote_wave.sh <targets.json> [--max N] [--gap-min S] [--gap-max S] [--detach]"; exit 2; fi

DETACH=0
ARGS=()
for a in "$@"; do
  if [ "$a" = "--detach" ]; then DETACH=1; else ARGS+=("$a"); fi
done

LOCK=/tmp/x-fire.lock
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "REFUSED: another fire wave is already running (flock $LOCK held)"
  exit 3
fi

if [ "$DETACH" = "1" ]; then
  LOG=/home/ubuntu/x-op/logs/quote-wave-detached-$(date -u +%Y%m%d-%H%M%S).log
  logger -t x-fire "quote wave start (detached): ${ARGS[*]}" 2>/dev/null || true
  # fd 9 is inherited by the child, so the flock stays held until the driver exits
  nohup /home/ubuntu/x-op/venv/bin/python /home/ubuntu/x-op/quote_driver.py "${ARGS[@]}" >"$LOG" 2>&1 &
  PID=$!
  echo "detached pid=$PID log=$LOG"
  exit 0
fi

logger -t x-fire "quote wave start: $*" 2>/dev/null || true
/home/ubuntu/x-op/venv/bin/python /home/ubuntu/x-op/quote_driver.py "${ARGS[@]}"
rc=$?
logger -t x-fire "quote wave end rc=$rc: $*" 2>/dev/null || true
exit $rc
