#!/usr/bin/env bash
# x-op systems audit: verify the whole rig is autonomous, at max output, and self-healing.
# Read-only. Default: full report. --quiet: print ONLY problems (empty stdout = all green,
# watchdog pattern for cron delivery). Exit 0 = all green, exit 1 = something needs attention.
set -uo pipefail
X=/home/ubuntu/x-op
QUIET=0; [ "${1:-}" = "--quiet" ] && QUIET=1
OK=0; WARN=0
say() { [ "$QUIET" = 1 ] && return 0; printf '%-46s %s\n' "$1" "$2"; }
ok()   { say "$1" "OK"; OK=$((OK+1)); }
warn() { printf '%-46s %s\n' "$1" "WARN: $2"; WARN=$((WARN+1)); }
bad()  { printf '%-46s %s\n' "$1" "FAIL: $2"; WARN=$((WARN+1)); }

[ "$QUIET" = 0 ] && echo "=== x-op SYSTEMS AUDIT $(date -u +%FT%TZ) ==="
[ "$QUIET" = 1 ] && printf ''  # quiet: no header unless something prints below

# 1. MCP rig up?
if ss -tln 2>/dev/null | grep -q ':8932 '; then ok "mcp server :8932"; else bad "mcp server :8932" "port dead - rig watchdog will restart"; fi
if pgrep -fc "cloakbrowser/chromium.*/chrome --" >/dev/null 2>&1; then ok "browser process"; else bad "browser process" "chromium gone"; fi

# 2. Scheduler + gateway
if pgrep -f "hermes.*gateway" >/dev/null 2>&1; then ok "hermes gateway process"; else warn "hermes gateway process" "not found - check lifecycle"; fi

# 3. state.json freshness
last=$(/home/ubuntu/x-op/venv/bin/python -c "import json;print(json.load(open('$X/worker/state.json')).get('last_cycle') or '')" 2>/dev/null)
if [ -n "$last" ]; then
  age=$(( $(date -u +%s) - $(date -u -d "${last%Z}" +%s 2>/dev/null || echo 0) ))
  if [ "$age" -lt 2400 ]; then ok "state last_cycle (${age}s ago)"; else warn "state last_cycle" "${age}s ago (>40min)"; fi
else bad "state last_cycle" "empty"; fi

# 4. throttle state
thr=$(/home/ubuntu/x-op/venv/bin/python -c "import json;print(json.load(open('$X/worker/state.json')).get('throttle_until') or 'none')" 2>/dev/null)
[ "$thr" = "none" ] && ok "throttle state" || warn "throttle state" "cooldown until $thr"

# 5. pool: recent harvest candidates
newest_h=$(ls -t $X/targets/harvest-*.json 2>/dev/null | head -1)
if [ -n "$newest_h" ]; then
  n=$(/home/ubuntu/x-op/venv/bin/python -c "import json;d=json.load(open('$newest_h'));print(len(d if isinstance(d,list) else d.get('targets',[])))" 2>/dev/null || echo 0)
  hage=$(( $(date -u +%s) - $(stat -c %Y "$newest_h") ))
  if [ "$n" -ge 100 ] && [ "$hage" -lt 3600 ]; then ok "harvest pool ($n cands, ${hage}s old)"; else warn "harvest pool" "$n cands, ${hage}s old"; fi
else warn "harvest pool" "no harvest files"; fi

# 6. lane stuck? (driver/harvest older than 25 min)
for pat in fire_driver harvest_run; do
  p=$(pgrep -f "python.*$pat" | head -1 || true)
  if [ -n "$p" ]; then
    et=$(ps -o etimes= -p "$p" 2>/dev/null | tr -d ' ')
    if [ "${et:-0}" -gt 1500 ]; then warn "$pat runtime" "${et}s (>25min) - possible stuck"; else ok "$pat runtime (${et}s)"; fi
  fi
done

# 7. disk
free_g=$(df -BG /home/ubuntu | awk 'NR==2{gsub("G","",$4);print $4}')
if [ "${free_g:-0}" -gt 5 ]; then ok "disk free (${free_g}G)"; else warn "disk free" "${free_g}G"; fi

# 8. stale targets count (older than 12h)
stale=$(find $X/targets -name '*.json' -mmin +720 2>/dev/null | wc -l)
if [ "$stale" -lt 30 ]; then ok "stale target files ($stale)"; else warn "stale target files" "$stale older than 12h"; fi

# 9. watcher state advancing
wst=/home/ubuntu/.hermes/profiles/bounty/state/xop-grok-watch.state
if [ -f "$wst" ]; then w=$(cat "$wst"); tot=$(wc -l < /home/ubuntu/.hermes/profiles/bounty/logs/agent.log); if [ "$tot" -ge "$w" ]; then ok "model watcher state ($w/$tot)"; else warn "model watcher state" "state $w > log $tot (rotation?)"; fi; else warn "model watcher state" "no state file"; fi

# 10. today's output
hits=$(/home/ubuntu/x-op/venv/bin/python - <<'EOF' 2>/dev/null
import json
led = json.load(open('/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json'))
entries = led if isinstance(led, list) else led.get('entries', [])
print(len([e for e in entries if (e.get('firedAt') or '').startswith('2026-09-22')]))
EOF
)
ok "hits today" "${hits:-?}"

# 11. stall check: during the active window, newest fire activity must be < 2.5h old
now_h=$(date -u +%H); now_m=$(date -u +%M)
mins=$((10#$now_h * 60 + 10#$now_m))
if [ "$mins" -ge 390 ] && [ "$mins" -le 1410 ]; then
  newest_f=$(ls -t $X/logs/fire-2026*.jsonl 2>/dev/null | head -1)
  if [ -n "$newest_f" ]; then
    fage=$(( $(date -u +%s) - $(stat -c %Y "$newest_f") ))
    if [ "$fage" -gt 9000 ]; then warn "fire activity" "newest wave ${fage}s old (>2.5h) - stalled?"; else ok "fire activity (${fage}s old)"; fi
  else warn "fire activity" "no fire logs today"; fi
fi

# 12. pending_verify staleness (pipeline handoff must not rot)
pv=$(/home/ubuntu/x-op/venv/bin/python -c "import json;print(json.load(open('$X/worker/state.json')).get('pending_verify') or '')" 2>/dev/null)
if [ -n "$pv" ]; then
  if [ -f "$pv" ]; then
    pvage=$(( $(date -u +%s) - $(stat -c %Y "$pv") ))
    if [ "$pvage" -gt 2700 ]; then warn "pending_verify" "unverified wave ${pvage}s old (>45min) - pipeline handoff stuck"; else ok "pending_verify (${pvage}s old)"; fi
  else warn "pending_verify" "points at missing file: $pv"; fi
else ok "pending_verify (none)"; fi

echo "=== audit done: $OK ok, $WARN warn/fail ==="
exit 0
