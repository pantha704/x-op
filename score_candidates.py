#!/usr/bin/env python3
"""Curated-track scorer (owner directive 2026-09-21). Ranks candidate posts + composed replies.

A reply is only posted if the CONDITIONS are met; the system picks the best-scoring one per slot.
Usage:
  score_candidates.py pool.json                 # rank candidates (needs: url, likes, replies, ratio, age/t, trend flag)
  score_candidates.py composed.json --lines     # rank composed replies (needs: url, text, tag, + pool meta)

Formula (transparent, from analysis + bible + Noir):
  tier:   big>=1000L +40 | mid 500-999 +25 | small 200-499 +10 | <200 disqualify
  ratio:  sparse reply section: min(ratio,500)/500*20
  fresh:  <30m +25 | <2h +15 | <6h +8 | <24h +3 | >=48h disqualify
  window: live/airing/event/breaking/teaser +20 ; trend-match +10
  noise:  replies>1000 -10 ; replies>5000 -20
  line score (--lines): base 10 | len<=90 +5 | len>130 -20 | soft botflag -5 | HARD botflag disqualify
  PUNCH (owner 2026-09-21: "curated replies are not banging enough"):
    +8 edge marker (nobody/someone/explain/who decided/and still/except/somehow/meanwhile)
    +6 twist marker in the line
    +5 deadpan approval (honestly/correct/fair) counts as edge, kills the flat penalty
    +4 shares a concrete noun (6+ chars) with the parent
    -10 compliment-shaped (great/amazing/respect/legend/best/perfect/love it/goat/masterclass)
    -8 flat observational (no edge AND no twist)  <- the exact failure mode of the 15:56-17:02 fires
    -4 invented precision (digits the parent never had)
  --lines gate: punch >= 6 AND final >= 55, else SKIP the slot (never post a flat line).
Final = candidate + line. Threshold: 55. Below -> do not post (skip is correct).
"""
import json, re, sys

EDGE_RE = re.compile(r"\b(nobody|no one|someone|explain|who decided|except|somehow|meanwhile|for no reason|not once|we need to talk|wait)\b", re.I)
TWIST_RE = re.compile(r"\b(and still|but|except|somehow|yet|meanwhile|instead|anyway)\b", re.I)
PRAISE_RE = re.compile(r"\b(great|amazing|incredible|respect|legend|best|perfect|love (this|it|that)|no notes|masterclass|goat|iconic)\b", re.I)
DEADPAN_RE = re.compile(r"\b(honestly|correct|fair|as it should|we deserve|deserved|right call|valid|no argument|understood|respectfully)\b", re.I)


def cand_score(c):
    L = c.get('likes') or 0
    R = c.get('replies') or 0
    ratio = c.get('ratio') or (L / max(1, R))
    age = (c.get('age') or '').lower()
    t = (c.get('t') or '') + ' ' + (c.get('text') or '')
    s = 0
    if L >= 1000: s += 40
    elif L >= 500: s += 25
    elif L >= 200: s += 10
    else: return None
    s += min(ratio, 500) / 500 * 20
    m = re.search(r'(\d+)\s*m', age)
    h = re.search(r'(\d+)\s*h', age)
    d = re.search(r'(\d+)\s*d', age)
    mins = int(m.group(1)) if m else (int(h.group(1))*60 if h else (int(d.group(1))*1440 if d else 999))
    if mins < 30: s += 25
    elif mins < 120: s += 15
    elif mins < 360: s += 8
    elif mins < 1440: s += 3
    else: return None
    if re.search(r'\b(live|premiere|airs?|episode (today|tonight)|finale|reveal|teaser|trailer|drop|just announced|breaking)\b', t, re.I):
        s += 20
    if c.get('trend'):
        s += 10
    if R > 5000: s -= 20
    elif R > 1000: s -= 10
    return round(s, 1)


def punch_score(e):
    t = (e.get('text') or '').strip()
    parent = e.get('parent_text') or ''
    p = 0.0
    if EDGE_RE.search(t): p += 8
    if TWIST_RE.search(t): p += 6
    if DEADPAN_RE.search(t): p += 5
    ptoks = {w.lower() for w in re.findall(r"[A-Za-z']{6,}", parent)}
    ttoks = {w.lower() for w in re.findall(r"[A-Za-z']{6,}", t)}
    if ptoks & ttoks: p += 4
    if PRAISE_RE.search(t): p -= 10
    if not EDGE_RE.search(t) and not TWIST_RE.search(t) and not DEADPAN_RE.search(t): p -= 8
    if re.search(r"\d", t) and not re.search(r"\d", parent): p -= 4
    return round(p, 1)


def line_score(e):
    t = e.get('text') or ''
    s = 10.0
    if len(t) <= 90: s += 5
    if len(t) > 130: s -= 20
    if e.get('soft'): s -= 5
    if e.get('hard'): return None, None
    p = punch_score(e)
    return s + p, p


def main():
    f = sys.argv[1]
    lines = '--lines' in sys.argv
    rows = json.load(open(f))
    ranked = []
    for r in rows:
        cs = cand_score(r)
        if cs is None: continue
        ls, punch = line_score(r) if lines else (0, None)
        if ls is None: continue
        if lines and punch < 6:
            print(f"SKIP(flat) {r.get('text','')[:60]!r}  punch={punch}")
            continue
        ranked.append((round(cs + ls, 1), r.get('likes'), (r.get('text') or r.get('t', '')[:60]), r.get('url'), punch))
    ranked.sort(key=lambda x: -x[0])
    for s, L, t, u, punch in ranked[:15]:
        pt = f" punch={punch}" if punch is not None else ""
        print(f"{s:>6}  {L:>6}L{pt}  {t[:70]}  {u}")
    print(f"\n{len(ranked)} scored | threshold 55 | lines gate: punch>=6 | top: {ranked[0][0] if ranked else 'none'}")


if __name__ == '__main__':
    main()
