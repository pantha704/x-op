#!/usr/bin/env python3
"""goal_watch.py — cron watcher for the reply goal (owner directive 2026-09-24).

Counts reply fires since the goal started; updates worker/goal.json; when the
target is reached: pauses the worker cron and prints a completion note (delivered
to the owner). Silent otherwise.

Runs every 15 min as a no-agent script cron.
"""
import json
import os
import subprocess
import time

os.chdir("/home/ubuntu/x-op")
GOAL = "worker/goal.json"
WORKER_JOB = "fff4b48b1810"

try:
    g = json.load(open(GOAL))
except Exception:
    raise SystemExit(0)

if not g.get("active"):
    raise SystemExit(0)

started = g.get("started_ts") or "1970-01-01T00:00:00Z"
# epoch of goal start
try:
    st = time.mktime(time.strptime(started, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
except Exception:
    st = 0

completed = 0
logdir = "logs"
for fn in os.listdir(logdir):
    if not (fn.startswith("fire-") and fn.endswith(".jsonl")):
        continue
    p = os.path.join(logdir, fn)
    try:
        if os.path.getmtime(p) < st:
            continue
        for line in open(p):
            if not line.strip():
                continue
            e = json.loads(line)
            if str(e.get("outcome", "")).startswith("hit") and e.get("type") != "quote":
                completed += 1
    except Exception:
        continue

g["completed"] = completed
json.dump(g, open(GOAL, "w"), indent=1)

if completed >= g.get("target", 0):
    g["active"] = False
    json.dump(g, open(GOAL, "w"), indent=1)
    subprocess.run(["hermes", "cron", "pause", WORKER_JOB], capture_output=True)
    print(f"reply goal complete: {completed}/{g['target']} — worker stopped. Send the next goal when ready.")
