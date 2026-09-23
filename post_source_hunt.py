#!/usr/bin/env python3
"""Post-source hunt: find image candidates in our lanes for the method-driven post batch.
Returns posts with media URLs so we can pick winners + credit artists. Read-only.
Usage: post_source_hunt.py
Output: research/post-sources/batch1-candidates.json + printed table
"""
import asyncio, json, os, random, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
OUT = "/home/ubuntu/x-op/research/post-sources/batch1-candidates.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].map(a => {
  const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
  const un = a.querySelector('[data-testid="User-Name"]');
  const tx = a.querySelector('[data-testid="tweetText"]');
  const imgs = [...a.querySelectorAll('img[src*="pbs.twimg.com/media"]')].map(i => i.src);
  let likes=null;
  for (const b of a.querySelectorAll('[role="group"] [aria-label]')) {
    const m = (b.getAttribute('aria-label')||'').match(/^([\d,]+)\s+likes?/i);
    if (m && likes===null) likes = parseInt(m[1].replace(/,/g,''));
  }
  return { url: link ? link.href.split('?')[0] : null, handle: un ? (un.innerText.match(/@[A-Za-z0-9_]+/)||[''])[0] : '',
           likes: likes===null?-1:likes, text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,180) : '',
           age: t ? t.getAttribute('datetime') : '', img: imgs[0] || null, nimg: imgs.length };
}).filter(p => p.url && p.img))"""

QUERIES = [
    ("art",   '(fanart OR "fan art") (genshin OR "elden ring" OR "monster hunter" OR zelda OR "blue archive") min_faves:1500 -filter:replies'),
    ("art2",  '(art OR drawing OR illustration) (gaming OR anime OR "video game") min_faves:3000 -filter:replies'),
    ("meme",  '(meme OR memes) (gaming OR pc OR steam OR console) min_faves:4000 -filter:replies'),
    ("aiabs", '(ai OR "ai generated" OR chatgpt) (menu OR cafe OR restaurant OR product OR slop OR fail) min_faves:2000 -filter:replies'),
    ("setup", '(setup OR "battlestation" OR "game room") min_faves:3000 -filter:replies'),
    ("wow",   '(screenshot OR "in game" OR "photo mode") (elden ring OR cyberpunk OR "ghost of tsushima" OR red dead) min_faves:3000 -filter:replies'),
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
            pg = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            pid = pg.get("page_id") or pg.get("id")
            print("page:", pid)
            await asyncio.sleep(3)
            for name, q in QUERIES:
                url = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=top"
                try:
                    await call(s, "cloak_navigate", {"page_id": pid, "url": url})
                    await asyncio.sleep(random.uniform(4.0, 6.0))
                    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": JS})
                    posts = json.loads(json.loads(raw).get("result", "[]"))
                    out[name] = posts[:8]
                    print("== %s: %d" % (name, len(posts)))
                    for p in posts[:8]:
                        print("   %7s @%-15s %s | %s" % (p.get("likes"), (p.get("handle") or "")[:15], (p.get("text") or "")[:70], (p.get("url") or "")[-19:]))
                except Exception as e:
                    print("FAIL", name, str(e)[:80]); out[name] = []
                await asyncio.sleep(random.uniform(2.5, 4.0))
            try: await call(s, "cloak_close_page", {"page_id": pid})
            except Exception: pass
    json.dump(out, open(OUT, "w"), indent=1)
    print("saved:", OUT)

asyncio.run(main())
