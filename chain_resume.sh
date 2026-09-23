#!/bin/bash
set -u
LOGDIR=/home/ubuntu/x-op/logs
run() {
  f="$1"; max="$2"; gmin="$3"; gmax="$4"
  echo "=== wave $(basename $f) ($max) gaps $gmin-$gmax"
  bash /home/ubuntu/x-op/run_wave.sh "$f" --max "$max" --gap-min "$gmin" --gap-max "$gmax" | tail -4
  last=$(ls -t $LOGDIR/fire-*.jsonl | head -1)
  if tail -3 "$last" | grep -q THROTTLED; then echo "THROTTLE in $(basename $f) -> abort chain"; exit 9; fi
}
sleep 540
run /home/ubuntu/x-op/targets/campaign-compose-test.json 1 25 45
sleep 75
run /home/ubuntu/x-op/targets/campaign-compose-resume2.json 23 30 55
sleep 75
run /home/ubuntu/x-op/targets/campaign-compose-i.json 18 22 40
sleep 75
run /home/ubuntu/x-op/targets/campaign-compose-j.json 8 22 40
sleep 75
run /home/ubuntu/x-op/targets/campaign-compose-k.json 8 22 40
echo "CHAIN COMPLETE"
