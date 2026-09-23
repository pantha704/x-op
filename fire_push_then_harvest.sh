#!/bin/bash
# Fire push1a -> push1b (flock-retry), then run the 12-query harvest. No self-matching pgrep waits.
set -u
fire() {
  for i in $(seq 1 40); do
    out=$(bash /home/ubuntu/x-op/run_wave.sh "$1" --max 40 --gap-min 18 --gap-max 34 2>&1)
    echo "--- $(basename "$1") try $i"; echo "$out" | tail -2
    echo "$out" | grep -q REFUSED || return 0
    sleep 60
  done
}
fire /home/ubuntu/x-op/targets/campaign-compose-push1a.json
echo "PUSH1A DONE"
sleep 30
fire /home/ubuntu/x-op/targets/campaign-compose-push1b.json
echo "PUSH1B DONE"
sleep 30
cd /home/ubuntu/x-op
./venv/bin/python harvest_run.py "(anime OR manga) lang:en min_faves:500 -filter:replies" "(gaming OR games OR ps5 OR xbox) lang:en min_faves:500 -filter:replies" "(kpop OR idol OR concert) lang:en min_faves:300 -filter:replies" "(AI OR coding OR developers) lang:en min_faves:400 -filter:replies" "(football OR soccer OR f1) lang:en min_faves:500 -filter:replies" "(cats OR dogs OR animals) lang:en min_faves:400 -filter:replies" 2>&1 | tail -4
echo "H1 DONE"
sleep 15
./venv/bin/python harvest_run.py "(movie OR film OR trailer) lang:en min_faves:500 -filter:replies" "(marvel OR dc OR star wars) lang:en min_faves:500 -filter:replies" "(art OR illustration OR fanart) lang:en min_faves:400 -filter:replies" "(netflix OR series OR tv) lang:en min_faves:500 -filter:replies" "(music OR album) lang:en min_faves:500 -filter:replies" "(science OR space) lang:en min_faves:500 -filter:replies" 2>&1 | tail -4
echo "ALL DONE"
