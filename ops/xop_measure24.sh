#!/usr/bin/env bash
# x-op +24h reply measurement + banger report. Dark-window, no LLM.
# measure_ledger stamps likes/verdicts for replies aged 20h+ (own tab - safe even
# if a wave is live); banger_report renders research/banger-report.md.
set -uo pipefail
cd /home/ubuntu/x-op || exit 1
./venv/bin/python measure_ledger.py --min-age-h 20 --max 120 2>&1 | tail -3
./venv/bin/python banger_report.py 2>&1 | tail -8
