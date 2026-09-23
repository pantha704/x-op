#!/usr/bin/env python3
"""Engagement audit + proposed source-of-truth updates (owner directive 2026-09-21).

Reads the Reply Ledger (measured entries), aggregates performance by engine/slot,
tier, length, hour; scans for bot-tells in what we fired; writes:
  - vault: PARA/3. Resources/audits/audit-<date>.md
  - vault: PARA/3. Resources/audits/proposed-source-updates-<date>.md  (NEVER auto-applied)

Usage: audit_run.py [--days 3] [--no-push]
"""
import json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

VAULT = "/home/ubuntu/obsidian"
LEDGER = f"{VAULT}/PARA/3. Resources/Operator - Reply Ledger.json"
OUTDIR = f"{VAULT}/PARA/3. Resources/audits"
ENGINES = ("joke", "take", "relatable", "emotional", "selfai", "midnight")


def parse_dt(s):
    try:
        d = datetime.fromisoformat((s or "").replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def bucket_len(n):
    return "<50" if n < 50 else "50-80" if n < 80 else "80-110" if n < 110 else ">110"


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 3
    push = "--no-push" not in sys.argv
    led = json.load(open(LEDGER))
    entries = led["entries"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = [e for e in entries if (parse_dt(e.get("firedAt")) or cutoff) >= cutoff]
    measured = [e for e in recent if e.get("likes") is not None]
    all_measured = [e for e in entries if e.get("likes") is not None]

    L = []
    A = L.append
    A(f"# Engagement Audit - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    A("")
    A(f"Window: last {days}d | fired: {len(recent)} | measured: {len(measured)} | coverage: {len(measured)*100//max(1,len(recent))}%")
    A(f"All-time measured: {len(all_measured)}")
    A("")

    # winners
    top = sorted(measured, key=lambda e: -(e.get("likes") or 0))[:12]
    A("## Winners (this window)")
    for e in top:
        A(f"- {e.get('likes')}L / {e.get('repliesBack')}R | {bucket_len(len(e.get('text','')))}c | {e.get('tag','?')} | likes_parent={e.get('parentLikes')} | {e.get('text','')[:90]}")
    A("")

    # engine/slot performance
    by = defaultdict(lambda: [0, 0, 0])  # n, likes_sum, winners
    for e in measured:
        b = by[e.get("tag") or "?"]
        b[0] += 1; b[1] += (e.get("likes") or 0); b[2] += 1 if (e.get("likes") or 0) >= 10 else 0
    A("## Engine performance (measured)")
    for k, (n, ls, w) in sorted(by.items(), key=lambda x: -x[1][1] / max(1, x[1][0])):
        A(f"- {k}: n={n} avg_likes={ls/n:.1f} winners={w} ({w*100//max(1,n)}%)")
    A("")

    # length performance
    bl = defaultdict(lambda: [0, 0, 0])
    for e in measured:
        b = bl[bucket_len(len(e.get("text", "")))]
        b[0] += 1; b[1] += (e.get("likes") or 0); b[2] += 1 if (e.get("likes") or 0) >= 10 else 0
    A("## Length performance")
    for k in ("<50", "50-80", "80-110", ">110"):
        n, ls, w = bl[k]
        if n: A(f"- {k} chars: n={n} avg_likes={ls/n:.1f} winners={w} ({w*100//max(1,n)}%)")
    A("")

    # tier performance vs parent likes
    def tier(p):
        p = p or 0
        return "big(1000+)" if p >= 1000 else "mid(500-999)" if p >= 500 else "small(<500)" if p > 0 else "unknown"
    bt = defaultdict(lambda: [0, 0, 0])
    for e in measured:
        b = bt[tier(e.get("parentLikes"))]
        b[0] += 1; b[1] += (e.get("likes") or 0); b[2] += 1 if (e.get("likes") or 0) >= 10 else 0
    A("## Parent tier performance")
    for k, (n, ls, w) in bt.items():
        A(f"- {k}: n={n} avg_likes={ls/n:.1f} winners={w} ({w*100//max(1,n)}%)")
    A("")

    # cadence
    hrs = Counter()
    for e in recent:
        d = parse_dt(e.get("firedAt"))
        if d: hrs[d.strftime("%H")] += 1
    hot = [f"{h}:{n}" for h, n in sorted(hrs.items()) if n > 60]
    dark_hours = [f"{h:02d}" for h in range(24) if f"{h:02d}" not in hrs]
    A("## Cadence")
    A(f"- fires/hour histogram: {dict(sorted(hrs.items()))}")
    A(f"- bursty hours >60: {hot or 'none'} | dark hours today: {dark_hours or 'none (flag: no sleep window)'}")
    A("")

    # bot-tell scan over recent fired text
    texts = [e.get("text", "") for e in recent if e.get("text")]
    firstw = Counter((t.split()[0] if t.split() else "") for t in texts)
    grams = Counter()
    for t in texts:
        w = re.findall(r"[a-z0-9']+", t.lower())
        for i in range(len(w) - 2):
            grams[" ".join(w[i:i+3])] += 1
    rep = [(g, n) for g, n in grams.most_common(25) if n >= 3]
    A("## Bot-tell scan (recent fired)")
    A(f"- most common openers: {firstw.most_common(8)}")
    A(f"- repeated 3-grams (n>=3): {rep[:12] or 'none'}")
    A(f"- capitalized starts: {sum(1 for t in texts if t[:1].isupper())} | dashes: {sum(1 for t in texts if any(c in t for c in '—-–'))} | emoji-replies: {sum(1 for t in texts if any(ord(c) > 0x1F000 for c in t))}")
    A("")

    report = "\n".join(L) + "\n"
    os.makedirs(OUTDIR, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    rp = f"{OUTDIR}/audit-{day}.md"
    open(rp, "w").write(report)

    # proposed updates: suggestions only, never auto-applied
    props = []
    for k, (n, ls, w) in sorted(by.items(), key=lambda x: -x[1][1] / max(1, x[1][0])):
        if n >= 5 and w == 0:
            props.append(f"- RETIRE CHECK: engine '{k}' has n={n}, 0 winners, avg {ls/n:.1f} - candidate for graveyard if this repeats next audit.")
    if len(recent) >= 20:
        cov = len(measured) * 100 // max(1, len(recent))
        if cov < 60:
            props.append(f"- MEASURE COVERAGE low ({cov}%) - run measure_ledger.py --resolve more aggressively before judging anything.")
    if hot:
        props.append(f"- PACING: bursty hours detected {hot}; keep 140/75min soft window enforced in worker state.")
    if not dark_hours:
        props.append("- HUMAN: no dark window in the last window - enforce 23:30-06:30 UTC dark in worker state.")
    if rep:
        props.append(f"- REPETITION: repeated constructions found ({rep[0][0]!r} etc.) - add to the banned-phrase list.")
    A2 = props or ["- No changes proposed this cycle (data insufficient or clean)."]
    pp = f"{OUTDIR}/proposed-source-updates-{day}.md"
    open(pp, "w").write(f"# Proposed source-of-truth updates - {day}\n\nSuggestions only; apply after review (single-variable, documented).\n\n" + "\n".join(A2) + "\n")

    print(report[:1200])
    print("wrote:", rp, "|", pp)
    if push:
        subprocess.run(["git", "-C", VAULT, "add", "PARA/3. Resources/audits"]) 
        subprocess.run(["git", "-C", VAULT, "commit", "-m", f"audit: engagement report + proposed source updates ({day})"])
        subprocess.run(["git", "-C", VAULT, "push", "origin", "master"])


if __name__ == "__main__":
    main()
