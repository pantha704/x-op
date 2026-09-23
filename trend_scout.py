#!/usr/bin/env python3
"""Trend scout for the post feed (owner directive 2026-09-21).

Scans f=live across the primary lanes (tech, ai, anime, games, pc) + one experimental slot,
finds posts that are TRENDING or ABOUT TO TREND (teasers, announcements, drops, first looks, leaks),
computes velocity (likes/hour) and writes targets/trend-ideas.json sorted by score.

Usage: trend_scout.py [extra query ...]
Output item: {url, handle, text, likes, replies, age_min, velocity, kind, lane}
kind: announced | teaser | drop | firstlook | leak | viral
"""
import asyncio, json, re, sys, urllib.parse, time
from datetime import datetime, timezone
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"
OUT = "/home/ubuntu/x-op/targets/trend-ideas.json"

LANES = {
    # owner focus (2026-09-21): games + anime specifics first, tech added with a knowledge bar
    "anime": "(anime OR manga OR seiyuu OR episode) lang:en min_faves:1000 -filter:replies",
    "anime2": "(premiere OR finale OR \"season 2\" OR trailer OR announced) (anime OR manga) lang:en min_faves:800 -filter:replies",
    "games": "(game OR gaming OR ps5 OR xbox OR steam OR nintendo) lang:en min_faves:1000 -filter:replies",
    "games2": "(update OR patch OR delay OR launch OR trailer OR roadmap) (game OR gaming) lang:en min_faves:800 -filter:replies",
    "tech": "(chip OR silicon OR model OR release OR benchmark OR open source) (tech OR AI OR hardware) lang:en min_faves:800 -filter:replies",
    "experimental": "(announced OR \"first look\" OR teaser OR \"release date\" OR delayed OR leaked) lang:en min_faves:2000 -filter:replies",
}
KIND_PATTERNS = [
    ("leak", r"\b(leak|leaked|datamine|datamined|rumou?r)\b"),
    ("teaser", r"\b(teaser|teases|sneak peek|first look|preview)\b"),
    ("drop", r"\b(drops?|dropping|out now|available now|launches?|launching)\b"),
    ("announced", r"\b(announc|confirms?|reveals?|officially)\b"),
    ("delay", r"\b(delayed|postponed|pushed back)\b"),
]

JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 20).map(a => {
  const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
  const tx = a.querySelector('[data-testid="tweetText"]');
  const user = a.querySelector('[data-testid="User-Name"] a[href^="/"]');
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
  let likes = null, replies = null;
  for (const l of labels) {
    let m = l.match(/^([\d,]+)\s+likes?/i); if (m) likes = parseInt(m[1].replace(/,/g, ''));
    m = l.match(/^([\d,]+)\s+repl/i); if (m) replies = parseInt(m[1].replace(/,/g, ''));
  }
  return { url: tl ? tl.href.split('?')[0] : null, ts: t ? t.getAttribute('datetime') : null,
           handle: user ? user.getAttribute('href').slice(1) : null,
           likes, replies, text: tx ? tx.innerText.replace(/\n/g, ' ') : '' };
}).filter(x => x.url && x.ts))"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


def kind_of(text):
    tl = text.lower()
    for k, pat in KIND_PATTERNS:
        if re.search(pat, tl):
            return k
    return "viral"


async def main():
    extra = sys.argv[1:]
    queries = dict(LANES)
    for i, q in enumerate(extra):
        queries[f"extra{i+1}"] = q
    rows = []
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            pages = json.loads(lp).get("pages", [])
            # dedicated tab for the scout: never touch the reply driver's page
            try:
                np = json.loads(await call(s, "cloak_new_page", {"url": "about:blank"}))
                page = np.get("page_id") or np.get("id")
            except Exception:
                page = None
            if not page:
                page = pages[0]["page_id"] if pages else json.loads(await call(s, "cloak_launch", {"user_data_dir": PROFILE})).get("page_id")
            for lane, q in queries.items():
                nav = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=live"
                try:
                    await call(s, "cloak_navigate", {"page_id": page, "url": nav})
                    await asyncio.sleep(3.4)
                    r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
                    items = json.loads(json.loads(r3).get("result", "[]"))
                except Exception as ex:
                    print("lane fail:", lane, ex)
                    continue
                now = datetime.now(timezone.utc)
                for it in items:
                    try:
                        dt = datetime.fromisoformat(it["ts"].replace("Z", "+00:00"))
                        age_min = max(1, (now - dt).total_seconds() / 60)
                    except Exception:
                        continue
                    if age_min > 360:  # older than 6h: not a trend lead anymore
                        continue
                    it["age_min"] = round(age_min)
                    it["velocity"] = round((it.get("likes") or 0) / age_min, 1)
                    it["kind"] = kind_of(it.get("text") or "")
                    it["lane"] = lane
                    rows.append(it)
                print(f"{lane}: {len(items)} items")
    # dedup by url, rank: velocity first, kind bonus, likes floor
    seen, out = set(), []
    for it in sorted(rows, key=lambda x: -x["velocity"]):
        if it["url"] in seen: continue
        seen.add(it["url"])
        if (it.get("likes") or 0) < 300: continue
        bonus = {"leak": 25, "teaser": 20, "announced": 15, "drop": 12, "delay": 8, "viral": 0}[it["kind"]]
        it["score"] = round(it["velocity"] + bonus, 1)
        out.append(it)
    out.sort(key=lambda x: -x["score"])
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    for it in out[:15]:
        print(f"{it['score']:>7} v={it['velocity']:>6}/h {it['age_min']:>4}m {it['kind']:<9} [{it['lane']:<12}] @{it['handle']:<16} {(it['text'] or '')[:70]}")
    print(f"\n{len(out)} trend leads -> {OUT}")


asyncio.run(main())
