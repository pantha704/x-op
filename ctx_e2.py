#!/usr/bin/env python3
"""Round 2: LittleRedhoodd profile+thread, roshidere full, JonnyBlox full."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

JOBS = [
    ("redhoodd_profile", "https://x.com/LittleRedhoodd", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const bio = (document.querySelector('[data-testid="UserDescription"]') || {innerText:''}).innerText;
  const posts = arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    return (t ? t.innerText : '').slice(0, 260);
  });
  return {bio: bio, posts: posts};
})())"""),
    ("redhoodd_thread", "https://x.com/LittleRedhoodd/status/2101929876160917670", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, all: arts.slice(1, 22).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), txt: (t ? t.innerText.slice(0, 340) : '')};
  })};
})())"""),
    ("roshidere_full", "https://x.com/roshidere/status/2101945284804882635", r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return {err:'none'};
  const t = a.querySelector('[data-testid="tweetText"]');
  const links = [...a.querySelectorAll('a[href]')].map(x => x.getAttribute('href')).filter(h => h && !h.startsWith('/hashtag') && !h.includes('/photo/'));
  const imgs = [...a.querySelectorAll('img')].map(i => i.src).slice(0, 6);
  const q = a.querySelector('[data-testid="tweetText"]');
  return {full: a.innerText.slice(0, 1500), txt: t ? t.innerText : '', links: [...new Set(links)].slice(0, 12), imgs: imgs};
})())"""),
    ("jonnyblox_full", "https://x.com/JonnyBlox/status/2101930246190633396", r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return {err:'none'};
  const t = a.querySelector('[data-testid="tweetText"]');
  const links = [...a.querySelectorAll('a[href]')].map(x => x.getAttribute('href')).filter(h => h && !h.startsWith('/hashtag') && !h.includes('/photo/'));
  const imgs = [...a.querySelectorAll('img')].map(i => ({src: i.src, alt: i.getAttribute('alt')})).slice(0, 8);
  return {full: a.innerText.slice(0, 1500), txt: t ? t.innerText : '', links: [...new Set(links)].slice(0, 10), imgs: imgs};
})())"""),
]


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, page, js):
    r = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
    try:
        return json.loads(json.loads(r).get("result", "null") or "null")
    except Exception:
        return {"raw": r[:300]}


async def main():
    out = {}
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for tag, u, js in JOBS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(5.5)
                out[tag] = await ev(s, page, js)
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e2-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:3200])

asyncio.run(main())
