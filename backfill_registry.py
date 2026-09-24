#!/usr/bin/env python3
"""Backfill the posted-image registry from today's logs (hash every image ever posted)."""
import hashlib
import json
import os

REG = "worker/aesthetic-posted.jsonl"
have = set()
if os.path.exists(REG):
    for line in open(REG):
        if line.strip():
            have.add(json.loads(line)["sha256"])

added = 0
for fn in sorted(os.listdir("logs")):
    if not (fn.startswith("aesthetic-") and fn.endswith(".jsonl")):
        continue
    for line in open("logs/" + fn):
        if not line.strip():
            continue
        e = json.loads(line)
        if e.get("outcome") != "hit" or not e.get("image"):
            continue
        p = e["image"]
        if not os.path.exists(p):
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h in have:
            continue
        have.add(h)
        with open(REG, "a") as fh:
            fh.write(json.dumps({"sha256": h, "file": p, "ts": e.get("ts", ""), "src": e.get("url", "")}) + "\n")
        added += 1

print("registry entries:", len(have), "| added now:", added)
