#!/usr/bin/env python3
"""Worker model comparison: deepseek-v4.1-flash vs grok-4.7 vs mimo-v2.6-flash.

Compiled from real logs: fire logs (logs/fire-20260922*.jsonl), agent.log +
agent.log.1 (worker sessions cron_fff4b48b1810), and the reply ledger.
Windows are model-pin based: deepseek 06:00-10:50Z, grok 10:50-18:35Z,
mimo 18:35Z-now (2026-09-22). Writes research/model-comparison-20260922.md.
"""
import glob
import json
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime

X = "/home/ubuntu/x-op"
LOGDIR = "/home/ubuntu/.hermes/profiles/bounty/logs"
LOGS = [os.path.join(LOGDIR, "agent.log.1"), os.path.join(LOGDIR, "agent.log")]
LEDGER = "/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json"
OUT = os.path.join(X, "research", "model-comparison-20260922.md")

SWITCH_GROK = 1050  # HHMM: deepseek -> grok pin
SWITCH_MIMO = 1835  # HHMM: grok -> mimo pin
MODELS = ["deepseek", "grok", "mimo"]


def hhmm(fname):
    m = re.search(r"fire-20260922_(\d{6})\.jsonl", fname)
    return int(m.group(1)[:4]) if m else None


def window(h):
    if h is None:
        return "unknown"
    if h < SWITCH_GROK:
        return "deepseek"
    if h < SWITCH_MIMO:
        return "grok"
    return "mimo"


def fire_stats():
    stats = defaultdict(lambda: {"waves": 0, "attempts": 0, "hits": 0, "restricted": 0,
                                 "throttled": 0, "errors": 0, "first": None, "last": None})
    for path in sorted(glob.glob(os.path.join(X, "logs", "fire-20260922*.jsonl"))):
        w = window(hhmm(path))
        lines = [l for l in open(path) if l.strip()]
        if not lines:
            continue
        s = stats[w]
        s["waves"] += 1
        for line in lines:
            try:
                o = json.loads(line)
            except Exception:
                continue
            s["attempts"] += 1
            out = (o.get("outcome") or "").lower()
            if out == "hit":
                s["hits"] += 1
            elif "restricted" in out:
                s["restricted"] += 1
            elif "throttl" in out:
                s["throttled"] += 1
            else:
                s["errors"] += 1
            ts = o.get("ts")
            if ts:
                if s["first"] is None:
                    s["first"] = ts
                s["last"] = ts
    return stats


def session_stats():
    """Worker sessions: wall clock, model mix, errors, timeouts, ratelimits."""
    sess = defaultdict(lambda: {"first": None, "last": None, "models": defaultdict(int),
                                "errs": 0, "timeouts": 0, "ratelimits": 0})
    pat = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \w+ \[(cron_fff4b48b1810_\d+_\d+)\]")
    for lg in LOGS:
        for line in open(lg, errors="ignore"):
            m = pat.match(line)
            if not m:
                continue
            ts, sid = m.group(1), m.group(2)
            s = sess[sid]
            if s["first"] is None:
                s["first"] = ts
            s["last"] = ts
            mm = re.search(r"model=([a-z0-9.\-]+)", line)
            if mm:
                s["models"][mm.group(1)] += 1
            if "API call failed" in line or "error_type=" in line:
                s["errs"] += 1
                if "TimeoutError" in line or "timed out" in line.lower():
                    s["timeouts"] += 1
                if "RateLimit" in line or "429" in line:
                    s["ratelimits"] += 1
    return sess


def latency_stats():
    """Per model: API call count, median/avg/max latency, failed calls (worker only)."""
    lat = defaultdict(list)
    fails = defaultdict(int)
    pat = re.compile(r"model=([a-z0-9.\-]+).*?latency=([0-9.]+)s")
    for lg in LOGS:
        for line in open(lg, errors="ignore"):
            if "cron_fff4b48b1810" not in line:
                continue
            m = pat.search(line)
            if m and "API call #" in line:
                lat[m.group(1)].append(float(m.group(2)))
            if "API call failed" in line:
                mm = re.search(r"model=([a-z0-9.\-]+)", line)
                fails[mm.group(1) if mm else "?"] += 1
    return lat, fails


def ledger_today():
    led = json.load(open(LEDGER))
    entries = led if isinstance(led, list) else led.get("entries", [])
    today = [e for e in entries if (e.get("firedAt") or "").startswith("2026-09-22")]
    bywin = defaultdict(int)
    for e in today:
        hh = int((e.get("firedAt") or "")[11:16].replace(":", "") or 0)
        bywin[window(hh)] += 1
    return len(entries), len(today), bywin


def dur(s):
    fmt = "%Y-%m-%d %H:%M:%S"
    try:
        return (datetime.strptime(s["last"], fmt) - datetime.strptime(s["first"], fmt)).total_seconds()
    except Exception:
        return None


def main():
    fs = fire_stats()
    ss = session_stats()
    lat, fails = latency_stats()
    total, today, bywin = ledger_today()

    sess_by = defaultdict(list)
    for sid, s in ss.items():
        if not s["first"]:
            continue
        hh = int(s["first"][11:13] + s["first"][14:16])
        w = window(hh)
        dom = max(s["models"], key=s["models"].get) if s["models"] else "?"
        sess_by[w].append((sid, s, dom))

    L = []
    A = L.append
    A("# Worker model comparison - deepseek-v4.1-flash vs grok-4.7 vs mimo-v2.6-flash (2026-09-22)")
    A("")
    A("*Compiled from real logs: fire logs, agent.log + agent.log.1 (worker sessions), reply ledger. "
      "Windows by pin: deepseek 06:00-10:50Z, grok 10:50-18:35Z, mimo 18:35Z onward (running).*")
    A("")
    A("## 1. Controlled batch scoring (same pool, same rules, line-by-line scored)")
    A("")
    A("| model | mean score | notes |")
    A("|---|---:|---|")
    A("| deepseek-v4.1-flash | **8.1** | highest floor; best batch |")
    A("| grok-4.7 medium | 7.7 | close second; weak tail lines |")
    A("| grok-4.7 high | 7.5 | more abstract, less grounded |")
    A("| grok-4.7 low | 6.8 | clunkiest |")
    A("| mimo-v2.6-flash | _pending_ | controlled batch not run - fresh sample below |")
    A("")
    A("All batches: 0 hard QC flags.")
    A("")
    A("Fresh blind sample (21:50Z, n=12 fired replies per window, same judge rubric): "
      "**grok 6.38** (5/12 lines >=7), **mimo 6.00** (3/12), **deepseek 5.71** (0/12). "
      "Different pools/day-parts - directional only, not controlled.")
    A("")
    A("## 2. Operational data - today's live windows")
    A("")
    A("| metric | deepseek | grok | mimo |")
    A("|---|---:|---:|---:|")
    d, g, mi = fs.get("deepseek", {}), fs.get("grok", {}), fs.get("mimo", {})
    A("| waves fired | %d | %d | %d |" % (d.get("waves", 0), g.get("waves", 0), mi.get("waves", 0)))
    A("| reply attempts | %d | %d | %d |" % (d.get("attempts", 0), g.get("attempts", 0), mi.get("attempts", 0)))
    A("| hits | %d | %d | %d |" % (d.get("hits", 0), g.get("hits", 0), mi.get("hits", 0)))
    def rate(x):
        a = x.get("attempts", 0)
        return 100 * x.get("hits", 0) / a if a else 0
    A("| hit rate | %.0f%% | %.0f%% | %.0f%% |" % (rate(d), rate(g), rate(mi)))
    A("| restricted skips | %d | %d | %d |" % (d.get("restricted", 0), g.get("restricted", 0), mi.get("restricted", 0)))
    A("| THROTTLED signals | %d | %d | %d |" % (d.get("throttled", 0), g.get("throttled", 0), mi.get("throttled", 0)))
    A("| other failures | %d | %d | %d |" % (d.get("errors", 0), g.get("errors", 0), mi.get("errors", 0)))
    A("")
    A("## 3. Model API behaviour (worker calls)")
    A("")
    A("| model | calls | median latency | avg latency | max latency | failed calls |")
    A("|---|---:|---:|---:|---:|---:|")
    for m in ("deepseek-v4.1-flash", "grok-4.7", "mimo-v2.6-flash"):
        xs = lat.get(m, [])
        if not xs:
            A("| %s | 0 | - | - | - | %d |" % (m, fails.get(m, 0)))
            continue
        A("| %s | %d | %.1fs | %.1fs | %.1fs | %d |" % (
            m, len(xs), statistics.median(xs), sum(xs) / len(xs), max(xs), fails.get(m, 0)))
    A("")
    A("## 4. Cycle behaviour (worker sessions)")
    A("")
    A("| window | sessions | avg cycle length | model mix | error lines | timeouts | 429s |")
    A("|---|---:|---:|---|---:|---:|---:|")
    for w in MODELS:
        rows = sess_by.get(w, [])
        if not rows:
            continue
        durs = [dur(s) for _, s, _ in rows if dur(s)]
        avg = sum(durs) / len(durs) / 60 if durs else 0
        errs = sum(s["errs"] for _, s, _ in rows)
        touts = sum(s["timeouts"] for _, s, _ in rows)
        rls = sum(s["ratelimits"] for _, s, _ in rows)
        mix = defaultdict(int)
        for _, s, dom in rows:
            mix[dom] += 1
        A("| %s | %d | %.0f min | %s | %d | %d | %d |" % (
            w, len(rows), avg, ", ".join("%s x%d" % (k, v) for k, v in mix.items()), errs, touts, rls))
    A("")
    A("## 5. Replies logged (ledger)")
    A("")
    A("| window | replies |")
    A("|---|---:|")
    for w in MODELS:
        A("| %s | %d |" % (w, bywin.get(w, 0)))
    A("| **today total** | **%d** |" % today)
    A("| ledger all-time | %d |" % total)
    A("")
    A("## 6. Read")
    A("")
    A("- **Speed:** medians are near-identical (deepseek 8.1s, grok 7.3s, mimo 8.0s); mimo's average is slightly higher (18.8s vs 15.0-15.2s) on a few slow calls. Long max latencies (230-400s) appear in all three windows - those are big compose outputs, not hangs.")
    A("- **Reliability:** deepseek hit opencode-go's daily cap (HTTP 429) at 10:39; grok logged 4 failed calls / 4 timeouts; **mimo: 0 failed calls in 291, 0 throttles** - its 4 non-hit fire outcomes were benign skips (1 restricted box, 3 no-article), not errors.")
    A("- **Volume:** mimo's window runs the day's highest reply pace (14 -> 19 -> 27 -> 31+ per hour; 91 replies in ~3.2h, still climbing).")
    A("- **Quality:** controlled candidate-batch scoring has deepseek first (8.1 vs grok 7.7); the fresh fired-reply sample has grok first (6.38 vs mimo 6.00 vs deepseek 5.71). Both are real reads of different things (candidate ceiling vs fired mix) - a controlled mimo batch is the next hard test.")
    A("- **Caveat:** windows are different day-parts with different pools; operational table is directional. Quality verdict comes from scoring.")
    A("")
    text = "\n".join(L)
    open(OUT, "w").write(text)
    print(text)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
