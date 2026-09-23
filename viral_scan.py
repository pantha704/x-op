#!/usr/bin/env python3
"""Fresh virality scan: what is actually breaking out RIGHT NOW (last 3 days) across lanes.
Runs on its OWN page so it never disturbs the worker's fire page. Read-only, no writes to X.
Output: research/viral-scan-<date>.json
"""
import asyncio, json, random, sys, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
OUT = "/home/ubuntu/x-op/research/viral-scan-20260922.json"

EXTRACT = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].map(a => {
  const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
  const un = a.querySelector('[data-testid="User-Name"]');
  const tx = a.querySelector('[data-testid="tweetText"]');
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label')||'');
  let likes=null;
  const num = s => { const m = (s||'').replace(/,/g,'').match(/([\d.]+)\s*([KM])?/i); if(!m) return null; let v=parseFloat(m[1]); if(m[2]&&m[2].toUpperCase()==='K') v*=1000; if(m[2]&&m[2].toUpperCase()==='M') v*=1000000; return Math.round(v); };
  for (const l of labels) { let m=l.match(/^([\d,]+)\s+likes?/i); if(m && likes===null) likes=parseInt(m[1].replace(/,/g,'')); }
  const media = a.querySelectorAll('[data-testid="tweetPhoto"], video, [data-testid="card.wrapper"]').length;
  return { url: link ? link.href.split('?')[0] : null, handle: un ? (un.innerText.match(/@[A-Za-z0-9_]+/)||[''])[0] : '',
           likes: likes===null?-1:likes, media, text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,220) : '',
           age: t ? t.getAttribute('datetime') : '' };
}).filter(p => p.url))"""

QUERIES = [
    ("anime",     '(anime OR manga OR "one piece") min_faves:40000 since:2026-09-19 -filter:replies'),
    ("gaming",    '(gaming OR xbox OR playstation OR nintendo OR steam) min_faves:40000 since:2026-09-19 -filter:replies'),
    ("ai",        '(AI OR chatgpt OR "artificial intelligence" OR openai) min_faves:30000 since:2026-09-19 -filter:replies'),
    ("movies",    '(movie OR netflix OR cinema OR trailer) min_faves:50000 since:2026-09-19 -filter:replies'),
    ("sports",    '(football OR soccer OR nba OR nfl OR f1) min_faves:60000 since:2026-09-19 -filter:replies'),
    ("animals",   '(cat OR dog OR animals OR kitten) min_faves:60000 since:2026-09-19 -filter:replies'),
    ("japan",     '(japan OR japanese OR tokyo) min_faves:40000 since:2026-09-19 -filter:replies'),
    ("memes",     '(memes OR funny OR lol) min_faves:80000 since:2026-09-19 -filter:replies'),
]

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def main():
    out = {}
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            page = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            pid = page.get("page_id") or page.get("id")
            print("page:", pid)
            await asyncio.sleep(3)
            for name, q in QUERIES:
                url = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=top"
                try:
                    await call(s, "cloak_navigate", {"page_id": pid, "url": url})
                    await asyncio.sleep(random.uniform(4.0, 6.0))
                    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": EXTRACT})
                    posts = json.loads(json.loads(raw).get("result", "[]"))
                    out[name] = posts[:12]
                    print("== %s: %d posts" % (name, len(posts)))
                    for p in posts[:5]:
                        print("   %7s  @%s  %s" % (p.get("likes"), (p.get("handle") or "")[:18], (p.get("text") or "")[:90]))
                except Exception as e:
                    print("FAIL", name, str(e)[:100])
                    out[name] = []
                await asyncio.sleep(random.uniform(2.5, 4.5))
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass
    json.dump(out, open(OUT, "w"), indent=1)
    print("saved:", OUT)

asyncio.run(main())
