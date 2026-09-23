#!/bin/bash
cd /home/ubuntu/.hermes/profiles/bounty/skills/social-media/reddit-reading
OUT=/home/ubuntu/x-op/research/ht-research/raw
mkdir -p "$OUT"
run() {
  name="$1"; shift
  echo "=== $(date -u +%H:%M:%S) $name : $* ==="
  timeout 170 python3 scripts/reddit.py --json "$@" > "$OUT/$name.json" 2> "$OUT/$name.err"
  echo "rc=$? size=$(wc -c < "$OUT/$name.json" 2>/dev/null)"
  sleep 65
}
run 20_sub_Twitter_new sub Twitter --sort new --limit 40
run 21_sub_xTwitter_new sub xTwitter --sort new --limit 40
run 22_sub_Twitter_top_month sub Twitter --sort top --time month --limit 40
run 23_sub_socialmedia_new sub socialmedia --sort new --limit 30
run 24_sub_Entrepreneur_new sub Entrepreneur --sort new --limit 30
run 25_sub_CreatorEconomy_new sub CreatorEconomy --sort new --limit 30
echo "=== DONE $(date -u +%H:%M:%S) ==="
