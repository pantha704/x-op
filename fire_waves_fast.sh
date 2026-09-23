#!/bin/bash
# Fast push: fire a sequence of wave files back-to-back, flock-retry each, cooldown between waves.
# usage: fire_waves_fast.sh wave1.json wave2.json ...
set -u
for w in "$@"; do
  for i in $(seq 1 40); do
    out=$(bash /home/ubuntu/x-op/run_wave.sh "$w" --max 40 --gap-min 18 --gap-max 34 2>&1)
    echo "--- $(basename "$w") try $i"; echo "$out" | tail -3
    if ! echo "$out" | grep -q "REFUSED"; then break; fi
    sleep 60
  done
  sleep 45
done
echo "ALL WAVES DONE"
