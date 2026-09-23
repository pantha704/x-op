#!/usr/bin/env bash
# x-op rig watchdog - keeps the MCP server (:8932) + browser alive so worker cycles never stall.
# Deterministic, no LLM. Silent when healthy (watchdog pattern: empty stdout = no notification).
# Restarts: (1) MCP server if the port is dead; (2) browser if the server is up but chromium is gone.
# Never touches the X session/login (a logged-out session needs a human; reported, not fixed).
set -uo pipefail

X=/home/ubuntu/x-op
CTL="$X/cloak-mcp-http-ctl.sh"
PY="$HOME/.local/share/uv/tools/cloakbrowsermcp/bin/python"
LOG="$X/logs/rig-watchdog.log"
mkdir -p "$X/logs"

ts() { date -u +%FT%TZ; }
say() { echo "[$(ts)] $*" | tee -a "$LOG"; }

port_up=$(ss -tln 2>/dev/null | grep -c ':8932 ')
server_proc=$(pgrep -fc "vps_mcp_launcher" 2>/dev/null || true)
chrome_proc=$(pgrep -fc "cloakbrowser/chromium.*/chrome --" 2>/dev/null || true)

if [ "$port_up" -eq 0 ] || [ "$server_proc" -eq 0 ]; then
  say "RIG DOWN: port_up=$port_up server_proc=$server_proc -> restarting via ctl"
  bash "$CTL" start >> "$LOG" 2>&1
  sleep 10
  if ss -tln 2>/dev/null | grep -q ':8932 '; then
    say "RIG RECOVERED: server listening again"
  else
    say "RIG RESTART FAILED: port still down - manual check needed (tail $LOG)"; exit 1
  fi
  exit 0
fi

if [ "$chrome_proc" -eq 0 ]; then
  say "BROWSER GONE (server up): restarting server+browser"
  bash "$CTL" stop >> "$LOG" 2>&1
  sleep 3
  bash "$CTL" start >> "$LOG" 2>&1
  sleep 12
  if pgrep -fc "cloakbrowser/chromium.*/chrome --" >/dev/null 2>&1; then
    say "BROWSER RECOVERED"
  else
    say "BROWSER RESTART FAILED - manual check needed"; exit 1
  fi
  exit 0
fi

# second instance (:8933, post-side rig) - keep its server alive too
port2_up=$(ss -tln 2>/dev/null | grep -c ':8933 ')
if [ "$port2_up" -eq 0 ]; then
  say "SECOND RIG DOWN: :8933 not listening -> restarting"
  "$PY" "$X/start_mcp_8933.py" >> "$LOG" 2>&1
  sleep 8
  if ss -tln 2>/dev/null | grep -q ':8933 '; then
    say "SECOND RIG RECOVERED: :8933 listening"
  else
    say "SECOND RIG RESTART FAILED: manual check needed"
    exit 1
  fi
fi

# stalled-wave guard: a hung fire_driver holds the x-fire flock forever and silently stalls the lane.
# A normal wave = 14-16 min for 20 targets (gaps 15-35s). A driver alive >25 min is hung
# (dead MCP page, frozen nav). Kill it: the flock frees and the next cycle resumes via pending_verify.
fd=$(pgrep -f "fire_driver.py" | head -1 || true)
if [ -n "$fd" ]; then
  fd_age=$(ps -o etimes= -p "$fd" 2>/dev/null | tr -d ' ' || echo 0)
  if [ -n "$fd_age" ] && [ "$fd_age" -gt 1500 ]; then
    say "WAVE STALLED: fire_driver pid=$fd alive ${fd_age}s (>25min) -> killing (flock frees, next cycle resumes)"
    kill "$fd" 2>/dev/null || true
    sleep 3
    kill -9 "$fd" 2>/dev/null || true
  fi
fi

# healthy -> stay silent
exit 0
