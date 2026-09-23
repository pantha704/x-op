#!/usr/bin/env python3
"""Quick harvest: open search URLs, scroll, extract candidates via JS."""
import asyncio, json, os, random, sys, time, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"

EXTRACT = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].map(a => {
  const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
  const un = a.querySelector('[data-testid="User-Name"]');
  const tx = a.querySelector('[data-testid="tweetText"]');
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label')||'');
  let likes=0, replies=0, rSeen=false;
  for (const l of labels) { let m=l.match(/^([\d,]+)\s+likes?/i); if(m) likes=parseInt(m[1].replace(/,/g,'')); m=l.match(/^([\d,]+)\s+repl/i); if(m){ replies=parseInt(m[1].replace(/,/g,'')); rSeen=true; } }
  return { url: link ? link.href.split('?')[0] : null, handle: un ? (un.innerText.match(/@[A-Za-z0-9_]+/)||[''])[0] : '', likes, replies, ratio: Math.round(likes/Math.max(replies,1)*10)/10, rSeen, text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,150) : '', age: t ? t.getAttribute('datetime') : '' };
}).filter(p => p.url && p.text && p.likes >= 100))"""

import sys
QUERIES = sys.argv[1:] or [
  '(anime OR manga OR gaming) lang:en min_faves:300 -filter:replies',
  '(kpop OR "one piece" OR anime) lang:en min_faves:500 -filter:replies',
]

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def main():
    out = []
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            # Own dedicated tab (never pages[0]): lets the harvest run WHILE a detached
            # fire wave drives the main page. Two X tabs are fine (proven in practice).
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            page = np.get("page_id") or np.get("id")
            await asyncio.sleep(3)
            acc = await call(s, "cloak_evaluate", {"page_id": page, "expression": "(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText||'').trim() === 'Accept all cookies'); if (b) { b.click(); return 'cookie-accepted'; } return 'no-banner'; })()"})
            print("cookie:", acc.strip()[:100])
            seen = set()
            for q in QUERIES:
                url = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=live"
                print("search:", url[:110])
                await call(s, "cloak_navigate", {"page_id": page, "url": url})
                await asyncio.sleep(random.uniform(3.5, 5))
                for i in range(4):
                    r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": EXTRACT})
                    try:
                        rows = json.loads(json.loads(r3).get("result", "[]"))
                    except Exception:
                        rows = []
                    for row in rows:
                        if row["url"] not in seen:
                            seen.add(row["url"]); out.append(row)
                    await call(s, "cloak_evaluate", {"page_id": page, "expression": "window.scrollBy(0, 1400); 'ok'"})
                    await asyncio.sleep(random.uniform(1.2, 2.2))
            print("total distinct candidates:", len(out))
            # close our dedicated tab so tabs never pile up
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass
    def _clean(v):
        if isinstance(v, str):
            return v.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
        return v
    for r in out:
        for k in list(r.keys()):
            r[k] = _clean(r[k])
    out.sort(key=lambda x: -x["ratio"])
    os.makedirs(os.path.expanduser("~/x-op/targets"), exist_ok=True)
    fn = os.path.expanduser("~/x-op/targets/harvest-%s.json" % time.strftime("%Y%m%d-%H%M"))
    with open(fn, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print("saved:", fn)
    print("---- top by ratio ----")
    for row in out[:18]:
        print("%5.1f  %6d L / %5d R  %-18s %s" % (row["ratio"], row["likes"], row["replies"], row["handle"][:18], row["text"][:90]))

asyncio.run(main())
