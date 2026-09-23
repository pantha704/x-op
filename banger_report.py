#!/usr/bin/env python3
"""Banger report: per-day reply verdicts + top lines, from the ledger + measures.

Reads the reply ledger (verdicts stamped by measure_ledger.py at +20h:
winner >=10 likes, mid >=1, dead 0) and the raw snapshot measures. Writes
research/banger-report.md. Read-only.
"""
import glob
import json
import os
import re
from collections import Counter, defaultdict

X = "/home/ubuntu/x-op"
LEDGER = "/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json"
OUT = os.path.join(X, "research", "banger-report.md")


def likes_num(s):
    m = re.match(r"([\d,]+)", str(s or "").replace("Like", "").strip())
    return int(m.group(1).replace(",", "")) if m else 0


def main():
    led = json.load(open(LEDGER))
    entries = led if isinstance(led, list) else led.get("entries", [])

    by_day = defaultdict(list)
    for e in entries:
        day = (e.get("firedAt") or "")[:10]
        if day:
            by_day[day].append(e)

    lines = ["# Banger report", "",
             "Verdicts are stamped at +20h by `measure_ledger.py` (winner >=10 likes, mid >=1, dead 0).",
             "Fresh snapshots (measures-*.jsonl) are early reads only - do not judge a day before its +24h pass.", ""]
    lines.append("| day | replies | measured | winner | mid | dead | win rate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for day in sorted(by_day):
        rows = by_day[day]
        stamped = [x for x in rows if x.get("verdict")]
        c = Counter(x.get("verdict") for x in stamped)
        rate = f"{100*c.get('winner',0)/len(stamped):.0f}%" if stamped else "-"
        lines.append("| %s | %d | %d | %d | %d | %d | %s |" % (
            day, len(rows), len(stamped), c.get("winner", 0), c.get("mid", 0), c.get("dead", 0), rate))
    lines.append("")

    winners = [x for x in entries if x.get("verdict") == "winner"]
    winners.sort(key=lambda x: -(x.get("likes") or 0))
    lines.append("## Winners (>=10 likes at +20h)")
    lines.append("")
    if winners:
        for w in winners[:25]:
            lines.append("- **%s likes** | %s | %s" % (
                w.get("likes"), (w.get("firedAt") or "")[:10], (w.get("text") or "")[:100]))
    else:
        lines.append("- none stamped yet - the +20h pass fills these as entries age")
    lines.append("")

    # early snapshot reads (fresh likes, all ages)
    snap = []
    for path in glob.glob(os.path.join(X, "logs", "measures-*.jsonl")):
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            snap.append((likes_num(r.get("likes")), (r.get("time") or "")[:10], (r.get("text") or "")[:90]))
    snap.sort(reverse=True)
    lines.append("## Top early snapshots (not final - measured within ~2h of posting)")
    lines.append("")
    for lk, day, t in snap[:10]:
        lines.append(f"- {lk} likes | {day} | {t}")
    lines.append("")

    text = "\n".join(lines) + "\n"
    open(OUT, "w").write(text)
    print(text)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
