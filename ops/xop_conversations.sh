#!/usr/bin/env bash
# x-op conversation farm: refresh worker/conversations.json (replies-back on our replies).
# Own tab; safe beside live waves. Quiet output (local delivery).
set -uo pipefail
cd /home/ubuntu/x-op || exit 1
timeout 360 ./venv/bin/python conversation_farm.py 2>&1 | tail -12
