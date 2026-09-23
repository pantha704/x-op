#!/bin/bash
# Queued reddit.py calls, ~65s apart to respect the anonymous ~1 req/min limit.
cd /home/ubuntu/.hermes/profiles/bounty/skills/social-media/reddit-reading
OUT=/home/ubuntu/x-op/research/ht-research/raw
mkdir -p "$OUT"
run() {
  name="$1"; shift
  echo "=== $(date -u +%H:%M:%S) $name : $* ==="
  timeout 170 python3 scripts/reddit.py --json "$@" > "$OUT/$name.json" 2> "$OUT/$name.err"
  rc=$?
  echo "rc=$rc size=$(wc -c < "$OUT/$name.json" 2>/dev/null)"
  sleep 65
}
run 01_sub_Twitter_new sub Twitter --sort new --limit 30
run 02_sub_Twitter_top_month sub Twitter --sort top --time month --limit 30
run 03_sub_xTwitter_new sub xTwitter --sort new --limit 30
run 04_sub_xTwitter_top_month sub xTwitter --sort top --time month --limit 30
run 05_search_Twitter_monetization search monetization --sub Twitter --sort new --limit 30
run 06_search_Twitter_ocr search "original content rewards" --sub Twitter --sort new --limit 30
run 07_search_Twitter_impressions search impressions --sub Twitter --sort new --limit 30
run 08_search_xTwitter_monetization search monetization --sub xTwitter --sort new --limit 30
run 09_sub_TwitterRevenue_new sub TwitterRevenue --sort new --limit 30
run 10_search_TwitterRevenue_mon search monetization --sub TwitterRevenue --sort new --limit 30
run 11_search_Entrepreneur search "twitter monetization" --sub Entrepreneur --sort new --limit 25
run 12_search_socialmedia search "twitter monetization" --sub socialmedia --sort new --limit 25
run 13_search_juststart search "twitter monetization" --sub juststart --sort new --limit 25
run 14_search_CreatorEconomy search "twitter monetization" --sub CreatorEconomy --sort new --limit 25
run 15_search_Twitter_payout search payout --sub Twitter --sort new --limit 30
echo "=== DONE $(date -u +%H:%M:%S) ==="
