#!/usr/bin/env python3
"""Score genre-study raw JSON into a post scorecard.

Reads research/genre-study/raw/*.json (handle, genre, profile.followers,
top[].likes/replies/media/text). Prints a table and writes
research/post-scorecard.md. Does not post. Does not touch the reply rig.
"""
import glob
import json
import os
import re
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "research", "genre-study", "raw")
OUT = os.path.join(ROOT, "research", "post-scorecard.md")


def num(v):
    if isinstance(v, bool):
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    if not v:
        return 0
    s = str(v).lower().replace(",", "").strip()
    m = re.match(r"([\d.]+)\s*([kmb])?", s)
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"k": 1000, "m": 1000000, "b": 1000000000}.get(m.group(2) or "", 1))


def med(xs):
    xs = [x for x in xs if x]
    return statistics.median(xs) if xs else 0


def load():
    rows = []
    for path in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        d = json.load(open(path))
        prof = d.get("profile") or {}
        fol = num(prof.get("followers"))
        tops = d.get("top") or []
        if not tops or not fol:
            continue
        best = max(tops, key=lambda t: num(t.get("likes")))
        likes = [num(t.get("likes")) for t in tops]
        replies = [num(t.get("replies")) for t in tops]
        text = (best.get("text") or "").replace("\n", " ").strip()
        rows.append({
            "handle": d.get("handle") or os.path.basename(path)[:-5],
            "genre": d.get("genre") or "?",
            "followers": fol,
            "best": num(best.get("likes")),
            "breakout": num(best.get("likes")) / fol,
            "reply_ratio": (med(replies) / med(likes)) if med(likes) else 0,
            "words": len(text.split()),
            "media": bool(best.get("media")),
            "text": text[:80],
        })
    return rows


def render(rows):
    lines = ["# Post scorecard", "", "Source: research/genre-study/raw/*.json. Rerun: `./venv/bin/python score_posts.py`.", ""]
    lines.append("| handle | genre | followers | best | breakout | reply/like | words | media | line |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|---|")
    for r in sorted(rows, key=lambda x: -x["breakout"]):
        lines.append(
            "| %s | %s | %d | %d | %.1fx | %.3f | %d | %s | %s |"
            % (r["handle"], r["genre"], r["followers"], r["best"], r["breakout"],
               r["reply_ratio"], r["words"], "yes" if r["media"] else "no", r["text"].replace("|", "/"))
        )
    lines.append("")
    by = defaultdict(list)
    for r in rows:
        by[r["genre"]].append(r)
    lines.append("## Genre medians")
    lines.append("")
    for g, xs in sorted(by.items()):
        lines.append(
            "- %s: n=%d, breakout median %.2fx, reply/like median %.3f, words median %.0f, media %d/%d"
            % (g, len(xs),
               statistics.median([x["breakout"] for x in xs]),
               statistics.median([x["reply_ratio"] for x in xs]),
               statistics.median([x["words"] for x in xs]),
               sum(1 for x in xs if x["media"]), len(xs))
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    rows = load()
    if not rows:
        raise SystemExit("no scored rows in " + RAW)
    text = render(rows)
    open(OUT, "w").write(text)
    print(text)
    print("wrote", OUT, "rows", len(rows))


if __name__ == "__main__":
    main()
