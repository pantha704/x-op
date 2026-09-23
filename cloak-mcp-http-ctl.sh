#!/usr/bin/env bash
# Control the persistent cloakbrowsermcp HTTP server (launcher) on :8932.
set -u
LAUNCHER="/home/ubuntu/x-op/vps_mcp_launcher.py"
PY="$HOME/.local/share/uv/tools/cloakbrowsermcp/bin/python"
LOG="$HOME/.cache/cloak-mcp-http.log"

case "${1:-status}" in
  start)
    if pgrep -f "vps_mcp_launcher" > /dev/null; then
      echo "already running"
    else
      setsid nohup "$PY" "$LAUNCHER" >> "$LOG" 2>&1 < /dev/null &
      sleep 8
      echo "started"
    fi
    ;;
  stop)
    pkill -f "vps_mcp_launcher" && echo "stopped" || echo "not running"
    ;;
  status|*)
    echo "-- procs:"
    pgrep -af "vps_mcp_launcher" | head -3
    echo "-- ports:"
    ss -tln | grep -E ":8932" || echo "no listener"
    echo "-- log:"
    tail -n 8 "$LOG" 2>/dev/null
    ;;
esac
