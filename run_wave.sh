#!/bin/bash
# run_wave.sh — the ONLY way to launch reply waves. Enforces:
#   * single-flight (flock): two drivers can never fire the same targets concurrently
#   * duplicate-target protection is handled upstream (pool dedupe), this is the process guard
# Usage: run_wave.sh <targets.json> [--max N] [--gap-min S] [--gap-max S] [--detach]
#   --detach: nohup the driver, print "detached pid=NNN", return immediately.
#             The wave keeps firing after the calling session ends (pipelining:
#             the next cycle harvests+composes while this wave posts).
set -euo pipefail
if [ $# -lt 1 ]; then echo "usage: run_wave.sh <targets.json> [--max N] [--gap-min S] [--gap-max S] [--detach]"; exit 2; fi

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
  LOG=/home/ubuntu/x-op/logs/wave-detached-$(date -u +%Y%m%d-%H%M%S).log
  logger -t x-fire "wave start (detached): ${ARGS[*]}" 2>/dev/null || true
  # fd 9 is inherited by the child, so the flock stays held until the driver exits
  nohup /home/ubuntu/x-op/venv/bin/python /home/ubuntu/x-op/fire_driver.py "${ARGS[@]}" >"$LOG" 2>&1 &
  PID=$!
  echo "detached pid=$PID log=$LOG"
  exit 0
fi

logger -t x-fire "wave start: $*" 2>/dev/null || true
/home/ubuntu/x-op/venv/bin/python /home/ubuntu/x-op/fire_driver.py "${ARGS[@]}"
rc=$?
logger -t x-fire "wave end rc=$rc: $*" 2>/dev/null || true
exit $rc
