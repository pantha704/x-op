#!/bin/bash
# Fire wave L with retry: back off politely while another wave (worker/key) holds the flock.
set -u
for i in $(seq 1 60); do
  out=$(bash /home/ubuntu/x-op/run_wave.sh /home/ubuntu/x-op/targets/campaign-compose-l.json --max 10 --gap-min 25 --gap-max 50 2>&1)
  echo "--- try $i"; echo "$out" | tail -4
  if ! echo "$out" | grep -q "REFUSED"; then
    echo "L WAVE EXECUTED (try $i)"
    exit 0
  fi
  sleep 100
done
echo "L WAVE GAVE UP after 60 tries"
exit 1
