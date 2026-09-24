#!/usr/bin/env python3
"""drain_queue.py - throttle-aware poster for the 10-post goal queue.

Runs from cron (no-agent). Tries each queued item via aesthetic_publish.py:
- 'post button stuck'  -> X throttle: stop, keep remaining queued, silent
- 'screen blocked'     -> drop permanently (NSFW gate)
- 'duplicate blocked'  -> drop permanently (already posted)
- 'OUTCOME: hit'       -> posted
When the queue empties: prints a completion note (delivered to the owner).
Silent while throttled / nothing to do.
"""
import json
import os
import subprocess
import sys
import time

os.chdir("/home/ubuntu/x-op")
man = "worker/final10-manifest.jsonl"
if not os.path.exists(man):
    raise SystemExit(0)

entries = [json.loads(l) for l in open(man) if l.strip()]
if not entries:
    raise SystemExit(0)

remaining = []
posted = 0
for i, e in enumerate(entries):
    if not os.path.exists(e["image"]):
        continue
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
    except Exception as ex:
        remaining.append(e)
        continue
    low = out.lower()
    if "outcome: hit" in low:
        posted += 1
    elif "post button stuck" in low:
        remaining.append(e)
        remaining.extend(entries[i + 1:])
        break
    elif "screen blocked" in low or "duplicate blocked" in low:
        pass  # drop permanently
    else:
        remaining.append(e)
    if remaining and remaining[-1] is e:
        time.sleep(0)  # no-op; pacing handled by publish gaps

with open(man, "w") as fh:
    for e in remaining:
        fh.write(json.dumps(e) + "\n")

if posted:
    print(f"drain: posted {posted} | remaining {len(remaining)}")
if not remaining and posted:
    print("queue drained - 10-post goal complete.")
