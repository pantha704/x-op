#!/usr/bin/env python3
"""Build the retry manifest from the failed items of the last bulk run."""
import json
import re

fails = []
for line in open("logs/aesthetic-bulk-run.log"):
    m = re.search(r"FAIL (images/aesthetic/bulk-\d+\.jpg)", line)
    if m:
        fails.append(m.group(1))
fails = sorted(set(fails))
print("failed:", len(fails))

man = {}
for line in open("worker/aesthetic-bulk-manifest.jsonl"):
    if line.strip():
        e = json.loads(line)
        man[e["image"]] = e

retry = [man[f] for f in fails if f in man]
with open("worker/aesthetic-retry-manifest.json", "w") as fh:
    json.dump(retry, fh, indent=1)
print("retry entries:", len(retry))
for r in retry:
    print(" ", r["image"].split("/")[-1], "|", (r.get("tag") or "-")[:18], "|", (r.get("text") or "")[:32])
