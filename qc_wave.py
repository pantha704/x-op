#!/usr/bin/env python3
"""QC + assemble a wave: compose files -> linted, deduped, restricted-aware targets file.

Usage: qc_wave.py <out.json> <compose1.json> [compose2.json ...]
- lints: lowercase start, no em/en dashes, no standalone hyphen punctuation, <=275 chars, banned phrases
- dedupes: same url twice in wave; urls already fired (fire logs + ledger); restricted-urls.json
- adds parent stats from the harvest pool
Prints a verdict per draft; writes out.json for firing.
"""
import glob
import json
import os
import re
import sys

BANNED = ["this is the way", "chef's kiss", "peak fiction", "goated", "rent free",
          "it's giving", "the way this", "core memory"]
RESTRICTED = "/home/ubuntu/x-op/targets/restricted-urls.json"


def main():
    out_path, compose_files = sys.argv[1], sys.argv[2:]
    if not compose_files:
        print("usage: qc_wave.py <out.json> <compose...json>")
        return 2

    pool = {}
    for f in glob.glob("/home/ubuntu/x-op/targets/harvest-2026*.json"):
        for r in json.load(open(f)):
            pool.setdefault(r["url"], r)

    fired = set()
    for f in glob.glob("/home/ubuntu/x-op/logs/fire-*.jsonl"):
        for l in open(f):
            if l.strip():
                fired.add(json.loads(l)["url"])

    try:
        restricted = set(json.load(open(RESTRICTED)).keys()) if os.path.exists(RESTRICTED) else set()
    except Exception:
        restricted = set()

    drafts = []
    for f in compose_files:
        drafts += json.load(open(f))

    ok, problems = [], []
    seen = set()
    for d in drafts:
        t = (d.get("text") or "").strip()
        u = d.get("url") or ""
        tag = d.get("tag", "take")
        why = []
        if not u or u in seen or u in fired or u in restricted or u not in pool:
            why.append("url-skip")
        seen.add(u)
        if not t or (t[0].isalpha() and not t[0].islower()):
            why.append("caps-start")
        if "\u2014" in t or "\u2013" in t or re.search(r"\s-\s", t):
            why.append("dash")
        if len(t) > 140:
            why.append(f"too-long({len(t)})")
        lt = t.lower()
        for b in BANNED:
            if b in lt:
                why.append(f"banned:{b}")
        if why:
            problems.append((u.split("/")[-1], ",".join(why), t[:60]))
            continue
        r = pool.get(u, {})
        ok.append({"url": u, "text": t, "lang": "en",
                   "tags": d.get("tags") or [tag],
                   "parent_likes": r.get("likes"), "parent_replies": r.get("replies"),
                   "ratio": r.get("ratio", 0)})

    json.dump(ok, open(out_path, "w"), indent=1, ensure_ascii=False)
    print(f"PASS: {len(ok)} | SKIP: {len(problems)} | saved: {out_path}")
    for p in problems:
        print("  skip:", *p)
    for t in sorted(ok, key=lambda x: -(x.get("ratio") or 0)):
        print(f"  [{t['tags'][0][:4]}] {t.get('ratio') or 0:7.1f}  {t['text'][:78]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
