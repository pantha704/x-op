#!/usr/bin/env bash
# x-op stale cleanup - nightly, deterministic, no LLM.
# Ages out stale targets/*.json (the "queued" exclusion pool killer), gzips old fire logs,
# archives old worker scratch, deletes spent upload staging media.
# Runs in the dark window (00:20 UTC) when no wave can be live.
set -uo pipefail
cd /home/ubuntu/x-op || exit 1

PY=/home/ubuntu/x-op/venv/bin/python
[ -x "$PY" ] || PY=/usr/bin/python3

echo "=== xop cleanup $(date -u +%FT%TZ) ==="

# guard: never run while a wave or harvest is live (use runtime-built patterns to avoid pgrep self-match)
if pgrep -f "python.*fire_driver" >/dev/null 2>&1 || pgrep -f "python.*harvest_run" >/dev/null 2>&1; then
  echo "lane busy (wave/harvest live) - skipping this run"
  exit 0
fi

$PY cleanup_stale.py --targets-days 0.75 --worker-days 1 --apply 2>&1 | tail -12

# exclusion-health check: report the queued count the selector sees (kept small = pool healthy)
$PY worker/select_latest.py 2>&1 | grep "^excl:" | sed 's/^/select /'

# disk line
du -sh /home/ubuntu/x-op/targets 2>/dev/null | sed 's/^/targets /'
du -sh /home/ubuntu/x-op/logs 2>/dev/null | sed 's/^/logs /'

# browser cache sweep: idle profiles always; the two x-op rigs get bounced and
# cleared too (dark window, lane already confirmed idle above)
echo "=== cache sweep ==="
$PY cache_sweep.py --apply 2>&1 | tail -10
echo "-- bouncing rigs for cache clear (dark window) --"
bash "$HOME/.hermes/profiles/bounty/scripts/xop_rig_watchdog.sh" >/dev/null 2>&1 || true
bash /home/ubuntu/x-op/cloak-mcp-http-ctl.sh stop >/dev/null 2>&1
pkill -f "mcp_launcher_8933" >/dev/null 2>&1
sleep 4
$PY cache_sweep.py --apply 2>&1 | tail -6
bash /home/ubuntu/x-op/cloak-mcp-http-ctl.sh start >/dev/null 2>&1
$PY /home/ubuntu/x-op/start_mcp_8933.py >/dev/null 2>&1
sleep 8
echo "rigs back: $(ss -tln | grep -cE ':8932|:8933') ports listening (expect 2)"
