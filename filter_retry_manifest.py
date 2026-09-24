#!/usr/bin/env python3
"""Filter the retry manifest: drop any image already posted (by filename)."""
import json

posted = set()
for line in open("logs/aesthetic-20260924.jsonl"):
    if line.strip():
        e = json.loads(line)
        if e.get("image"):
            posted.add(e["image"].split("/")[-1])

retry = json.load(open("worker/aesthetic-retry-manifest.json"))
clean = [r for r in retry if r["image"].split("/")[-1] not in posted]
dropped = [r for r in retry if r["image"].split("/")[-1] in posted]
print("retry:", len(retry), "| already posted (dropped):", len(dropped), "| to fire:", len(clean))
for r in dropped:
    print("  dropped:", r["image"].split("/")[-1], r.get("tag", ""))
with open("worker/aesthetic-retry-manifest.json", "w") as fh:
    json.dump(clean, fh, indent=1)
for r in clean:
    print("  fire:", r["image"].split("/")[-1], "|", (r.get("tag") or "-")[:18], "|", (r.get("text") or "")[:30])
