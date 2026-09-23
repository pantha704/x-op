#!/bin/bash
set -u
fire() {
  for i in $(seq 1 40); do
    out=$(bash /home/ubuntu/x-op/run_wave.sh "$1" --max 40 --gap-min 20 --gap-max 38 2>&1)
    echo "--- $(basename "$1") try $i"; echo "$out" | tail -2
    echo "$out" | grep -q REFUSED || return 0
    sleep 60
  done
}
fire /home/ubuntu/x-op/targets/campaign-compose-r2-1.json; echo R2A DONE
sleep 45
fire /home/ubuntu/x-op/targets/campaign-compose-r2-2.json; echo R2B DONE
sleep 45
fire /home/ubuntu/x-op/targets/campaign-compose-r2-3.json; echo ALL R2 DONE
