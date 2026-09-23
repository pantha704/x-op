#!/bin/bash
# Fire wave K with retry (chain aborted on flock; K never fired).
set -u
for i in $(seq 1 60); do
  out=$(bash /home/ubuntu/x-op/run_wave.sh /home/ubuntu/x-op/targets/campaign-compose-k.json --max 8 --gap-min 25 --gap-max 50 2>&1)
  echo "--- try $i"; echo "$out" | tail -4
  if ! echo "$out" | grep -q "REFUSED"; then
    echo "K WAVE EXECUTED (try $i)"
    exit 0
  fi
  sleep 100
done
echo "K WAVE GAVE UP after 60 tries"
exit 1
