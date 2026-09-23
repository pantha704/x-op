#!/usr/bin/env python3
"""Pattern stats over the reply ledger (ground truth = the vault file).

Usage: ledger_stats.py
Prints: volume, format table (N / hit rate >=2 / avg / max), parent-ratio
buckets vs outcome, top replies, and counterexamples (ratio >= 100 but 0 likes)
for falsification tracking.
"""
import json
from collections import defaultdict
from statistics import mean

LEDGER = "/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json"


def main():
    es = json.load(open(LEDGER))["entries"]
    measured = [e for e in es if e.get("likes") is not None]
    pending = [e for e in es if e.get("likes") is None]
    print(f"entries={len(es)}  measured={len(measured)}  pending={len(pending)}")

    by = defaultdict(list)
    for e in measured:
        tag = e.get("tag") or "?"
        by[tag].append(e)
    print("\nFORMAT TABLE (measured only):")
    print(f"{'tag':<12}{'N':>4}{'hits':>6}{'rate':>7}{'avg':>7}{'max':>6}")
    for t, rows in sorted(by.items(), key=lambda kv: -mean([r.get('likes') or 0 for r in kv[1]])):
        lk = [r.get("likes") or 0 for r in rows]
        hits = sum(1 for x in lk if x >= 2)
        print(f"{t:<12}{len(rows):>4}{hits:>6}{hits/len(rows)*100:>6.0f}%{mean(lk):>7.1f}{max(lk):>6}")

    def ratio(e):
        pl, pr = e.get("parentLikes"), e.get("parentReplies")
        if not pl or pr is None:
            return None
        return pl / max(pr, 1)

    def bucket(r):
        if r is None:
            return None
        if r < 50:
            return "<50"
        if r < 100:
            return "50-100"
        if r < 300:
            return "100-300"
        if r < 1000:
            return "300-1000"
        return "1000+"

    b = defaultdict(list)
    for e in measured:
        k = bucket(ratio(e))
        if k:
            b[k].append(e.get("likes") or 0)
    print("\nPARENT RATIO vs OUTCOME (measured):")
    for k in ["<50", "50-100", "100-300", "300-1000", "1000+"]:
        if k in b:
            lk = b[k]
            hits = sum(1 for x in lk if x >= 2)
            print(f"{k:<10} N={len(lk):>3}  hit={hits / len(lk) * 100:>3.0f}%  avg={mean(lk):>6.1f}  max={max(lk):>5}")

    print("\nTOP REPLIES:")
    for e in sorted(measured, key=lambda x: -(x.get("likes") or 0))[:10]:
        print(f"  {e.get('likes'):>4} | {e.get('tag', '?'):<8} | {e.get('text', '')[:62]}")

    print("\nCOUNTEREXAMPLES (ratio >= 100 with 0 likes):")
    n = 0
    for e in measured:
        r = ratio(e)
        if r is not None and r >= 100 and (e.get("likes") or 0) == 0:
            print(f"  ratio {r:>6.0f} | {e.get('tag', '?')} | {e.get('text', '')[:58]}")
            n += 1
    print(f"  ({n} counterexamples)")


if __name__ == "__main__":
    main()
