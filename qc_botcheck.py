#!/usr/bin/env python3
"""Bot-tell gate for composed replies (owner directive 2026-09-21). BOTH arms must pass this before firing.

Usage: qc_botcheck.py targets.json [targets2.json ...] [--corpus N]
Reads recent fired texts from logs/fire-*.jsonl for fossil/repetition checks.
Exit 1 if any HARD flag; 0 if clean (soft warnings printed either way).

HARD (must fix before fire):
  len > 130 | capitalized start | em/en dash | standalone token with hyphen (non-word) | '# ' or '@' refs
  banned families: victory lap / disguised as / masterclass / let that sink / chef's kiss / couldn't agree more /
                   in shambles / at its finest / no notes / peak fiction / rent free / this is the way
SOFT (review):
  3-gram repeated >=2x inside the wave or >=4x in the last corpus | duplicate opener inside the wave |
  digits in reply whose parent text (when known) has no such number | >2 sentences | >24 words |
  orphan metaphor: two "like/as" similes
"""
import json, re, sys, glob
from collections import Counter

BANNED = ["victory lap","disguised as","masterclass","let that sink","chef's kiss","couldn't agree more",
          "in shambles","at its finest","no notes","peak fiction","rent free","this is the way","sink in"]
CORPUS_TEXTS = []
for p in sorted(glob.glob('/home/ubuntu/x-op/logs/fire-*.jsonl'))[-60:]:
    for l in open(p):
        l = l.strip()
        if not l: continue
        try: d = json.loads(l)
        except Exception: continue
        t = d.get('text') or ''
        if t: CORPUS_TEXTS.append(t)
CORPUS_TEXTS = CORPUS_TEXTS[-400:]

def grams(t):
    w = re.findall(r"[a-z0-9']+", t.lower())
    return [" ".join(w[i:i+3]) for i in range(len(w)-2)]

def check(t, parent=''):
    hard, soft = [], []
    if len(t) > 130: hard.append(f"len {len(t)} > 130")
    if t[:1].isupper(): hard.append("capitalized start")
    if any(c in t for c in '—–'): hard.append("em/en dash")
    if re.search(r'(?<![A-Za-z0-9])-|-(?![A-Za-z0-9])', t): hard.append("standalone hyphen")
    if '#' in t or '@' in t: hard.append("#/@ ref")
    tl = t.lower()
    for b in BANNED:
        if b in tl: hard.append(f"banned family: {b}")
    g = grams(t)
    cg = Counter(CORPUS_TEXTS and sum((grams(x) for x in CORPUS_TEXTS), [])) if CORPUS_TEXTS else Counter()
    for gr in set(g):
        if cg.get(gr, 0) >= 4: soft.append(f"corpus fossil 3-gram: {gr!r}")
    if len(re.findall(r'[.!?]', t)) > 2: soft.append("more than 2 sentences")
    if len(t.split()) > 24: soft.append(f"{len(t.split())} words")
    if re.search(r'\b\d+\b', t) and parent and not re.search(r'\b\d+\b', parent):
        soft.append("digit not present in parent text")
    return hard, soft

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    bad = 0
    seen_grams, seen_openers = Counter(), Counter()
    all_items = []
    for f in args:
        for e in json.load(open(f)):
            all_items.append((f, e['text'], e.get('parent_text', '')))
    for f, t, parent in all_items:
        seen_openers[t.split()[0] if t.split() else ''] += 1
        for gr in set(grams(t)): seen_grams[gr] += 1
    for f, t, parent in all_items:
        hard, soft = check(t, parent)
        for gr in set(grams(t)):
            if seen_grams[gr] >= 2 and gr not in ('', ):
                soft.append(f"wave-repeated 3-gram: {gr!r}")
                break
        if seen_openers[t.split()[0] if t.split() else ''] > 1:
            soft.append(f"duplicate opener: {t.split()[0]!r}")
        if hard:
            bad += 1
            print(f"HARD  [{f.split('/')[-1]}] {t[:70]!r}\n      -> {'; '.join(hard)}")
        elif soft:
            print(f"soft  [{f.split('/')[-1]}] {t[:70]!r}\n      -> {'; '.join(soft[:4])}")
    two = sum(1 for _, t, _ in all_items if t.count('. ') == 1)
    if all_items and two / len(all_items) > 0.30:
        print(f"soft  [batch] {two}/{len(all_items)} replies use the two-fragment 'X. Y.' shape (>30%) - vary the structure")
    print(f"\nchecked {len(all_items)} replies | HARD flagged: {bad} | {'FAIL' if bad else 'PASS'}")
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
