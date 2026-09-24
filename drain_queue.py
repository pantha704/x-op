#!/usr/bin/env python3
"""drain_queue.py - throttle-aware poster for the queued post goals.

X soft-throttles this account: bursts allow ~1 post, then the composer sticks.
Strategy: on 'post button stuck', wait and retry the SAME item (the tap reopens
after a while); give up after 3 waits or a total runtime budget, keeping the
rest queued. Single-flight via flock so overlapping cron ticks skip.

- 'screen blocked'     -> drop permanently (NSFW gate)
- 'duplicate blocked'  -> drop permanently (already posted)
- 'OUTCOME: hit'       -> posted
Prints a completion note when the queue empties; silent otherwise.
"""
import fcntl
import json
import os
import subprocess
import time

os.chdir("/home/ubuntu/x-op")
MANIFESTS = ["worker/final10-manifest.jsonl", "worker/char-batch.jsonl"]
WAIT_ON_STUCK = 480          # 8 min between retries of the same item
MAX_RETRIES = 3              # per item
BUDGET = 2700                # total runtime budget (45 min)
START = time.time()

_lock = open("/tmp/x-post-drain.lock", "w")
try:
    fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(0)

entries = []
for _m in MANIFESTS:
    if os.path.exists(_m):
        entries += [json.loads(l) for l in open(_m) if l.strip()]
if not entries:
    raise SystemExit(0)

remaining = []
posted = 0
stopped_throttled = False
for i, e in enumerate(entries):
    if time.time() - START > BUDGET:
        remaining.append(e)
        remaining.extend(entries[i + 1:])
        stopped_throttled = True
        break
    if not os.path.exists(e["image"]):
        continue
    retries = 0
    while True:
        cmd = ["./venv/bin/python", "aesthetic_publish.py", e["image"]]
        if e.get("text"):
            cmd.append(e["text"])
        if e.get("tag"):
            cmd += ["--tag", e["tag"], "--fallback-text", e["tag"]]
        if e.get("url"):
            cmd += ["--src", e["url"]]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
            out = (r.stdout or "") + (r.stderr or "")
        except Exception:
            remaining.append(e)
            break
        low = out.lower()
        if "outcome: hit" in low:
            posted += 1
            break
        if "post button stuck" in low:
            if retries < MAX_RETRIES and time.time() - START < BUDGET:
                retries += 1
                time.sleep(WAIT_ON_STUCK)
                continue
            remaining.append(e)
            remaining.extend(entries[i + 1:])
            stopped_throttled = True
            break
        if "screen blocked" in low or "duplicate blocked" in low:
            break  # drop permanently
        remaining.append(e)
        break
    if stopped_throttled:
        break

with open(MANIFESTS[0], "w") as fh:
    for e in remaining:
        fh.write(json.dumps(e) + "\n")
for m in MANIFESTS[1:]:
    if os.path.exists(m):
        open(m, "w").write("")

if posted:
    print(f"drain: posted {posted} | remaining {len(remaining)} | {'throttled' if stopped_throttled else 'queue done'}")
if not remaining and posted:
    print("queue drained - post goal complete.")
