#!/usr/bin/env bash
# x-op worker-model watcher: pings LO ONLY when the WORKER's pinned model degrades.
# Worker pin: grok-4.7 / xai-oauth / medium (set 2026-09-22). Silent when clean
# (empty stdout = no notification). Deterministic, no LLM. State = last processed
# agent.log line count.
#
# 2026-09-22 rewrite (noise fix): the previous filter counted ANY error line
# mentioning opencode-go|deepseek|grok|xai, so deepseek HTTP-429s in interactive
# sessions (this chat's own quota) fired "degradation" pings every 20 min while
# the worker rode grok with no problem. Now it watches exactly three things:
#   (1) error lines inside the worker job's own runs (cron_fff4b48b1810 sessions)
#   (2) grok/xai CALL failures anywhere (needs 'API call failed' or 'error_type=',
#       so chat fallback notices and 429s on other providers do NOT count)
#   (3) the runtime switching AWAY from grok (source model in the switch marker)
# Keep the marker + session tag in sync if the worker's pin changes again.
set -uo pipefail

X=/home/ubuntu/x-op
AL=/home/ubuntu/.hermes/profiles/bounty/logs/agent.log
ST=/home/ubuntu/.hermes/profiles/bounty/state/xop-grok-watch.state
LOG=$X/logs/grok-watch.log
mkdir -p "$(dirname "$ST")" "$X/logs"

total=$(wc -l < "$AL" 2>/dev/null || echo 0)
seen=$(cat "$ST" 2>/dev/null || echo 0)
case "$seen" in ''|*[!0-9]*) seen=0 ;; esac
[ "$total" -lt "$seen" ] && seen=0   # log rotated/truncated

new=$(sed -n "$((seen+1)),${total}p" "$AL" 2>/dev/null || true)
echo "$total" > "$ST"

[ -z "$new" ] && exit 0

TOK='timed? ?out|rate.?limit|error_type=|HTTP [45][0-9][0-9]|status[=: ]+[45][0-9][0-9]'
WORKER_TAG='cron_fff4b48b1810'

worker_errs=$(printf '%s\n' "$new" | grep -E "$WORKER_TAG" | grep -icE "$TOK" || true)
grok_fails=$(printf '%s\n' "$new" | grep -E 'API call failed|error_type=' | grep -icE 'xai-oauth|grok-4' || true)
grok_switches=$(printf '%s\n' "$new" | grep -cE 'Model switched in-place: grok' || true)

if [ "${worker_errs:-0}" -gt 0 ] || [ "${grok_fails:-0}" -gt 0 ] || [ "${grok_switches:-0}" -gt 0 ]; then
  echo "[x-op model watch $(date -u +%FT%TZ)] worker model degradation"
  [ "${worker_errs:-0}" -gt 0 ] && echo "worker-session error lines: ${worker_errs}"
  [ "${grok_fails:-0}" -gt 0 ] && echo "grok/xai call-failure lines: ${grok_fails}"
  [ "${grok_switches:-0}" -gt 0 ] && echo "switches away from grok: ${grok_switches}"
  echo "worker retries n/8 on its own; worst case one wave slips this cycle."
  echo "[$(date -u +%FT%TZ)] ---" >> "$LOG"
  printf '%s\n' "$new" | grep -E "$WORKER_TAG" | grep -iE "$TOK" | tail -4 >> "$LOG" 2>/dev/null || true
  printf '%s\n' "$new" | grep -E 'API call failed|error_type=' | grep -iE 'xai-oauth|grok-4' | tail -4 >> "$LOG" 2>/dev/null || true
  printf '%s\n' "$new" | grep -E 'Model switched in-place: grok' >> "$LOG" 2>/dev/null || true
fi
exit 0
