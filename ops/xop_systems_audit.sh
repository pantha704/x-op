#!/usr/bin/env bash
# Hourly x-op systems audit wrapper: quiet mode - prints ONLY problems (empty stdout = silent).
exec bash /home/ubuntu/x-op/systems_audit.sh --quiet
