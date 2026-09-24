#!/usr/bin/env python3
"""Post the aesthetic batch from the manifest with human-ish gaps + adaptive backoff.
Each item: subprocess aesthetic_publish.py (proven flow: attach -> tag-in-image ->
optional fallback text -> Post -> verify). Progress to stdout + per-post rows to
logs/aesthetic-YYYYMMDD.jsonl (written by aesthetic_publish itself).

Usage: aesthetic_bulk_post.py [--manifest worker/aesthetic-bulk-manifest.jsonl]
                              [--gap-min 40] [--gap-max 75]
"""
import json
import random
import subprocess
import sys
import time

argv = sys.argv[1:]
def opt(name, default):
    return int(argv[argv.index(name) + 1]) if name in argv else default

gap_min = opt("--gap-min", 40)
gap_max = opt("--gap-max", 75)
man = argv[argv.index("--manifest") + 1] if "--manifest" in argv else "worker/aesthetic-bulk-manifest.jsonl"

entries = [json.loads(l) for l in open(man) if l.strip()]
print(f"bulk post: {len(entries)} entries | gaps {gap_min}-{gap_max}s", flush=True)

ok = 0
fail = 0
consec = 0
for i, e in enumerate(entries):
    cmd = ["./venv/bin/python", "aesthetic_publish.py", e["image"]]
    if e.get("text"):
        cmd.append(e["text"])

    if e.get("tag"):
        cmd += ["--tag", e["tag"], "--fallback-text", e["tag"]]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    hit = "OUTCOME: hit" in out
    if hit:
        ok += 1
        consec = 0
        print(f"[{i+1}/{len(entries)}] hit  {e['image']} {e.get('tag','')} src={e.get('source','')}", flush=True)
    else:
        fail += 1
        consec += 1
        tail = out.strip().splitlines()[-1] if out.strip() else "no output"
        print(f"[{i+1}/{len(entries)}] FAIL {e['image']} :: {tail[:140]}", flush=True)
        if consec >= 2:
            print(f"backoff 300s after {consec} consecutive fails", flush=True)
            time.sleep(300)
            consec = 0
    if i < len(entries) - 1:
        time.sleep(random.uniform(gap_min, gap_max))

print(f"DONE ok={ok} fail={fail} of {len(entries)}", flush=True)
