#!/usr/bin/env python3
"""Round 3 (e-slice): caseohOOC post + profile for game context."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

JOBS = [
    ("caseoh_post", "https://x.com/caseohOOC/status/2101902335828218236", r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const who = a ? a.querySelector('[data-testid="User-Name"]') : null;
  const links = a ? [...a.querySelectorAll('a[href]')].map(x => x.getAttribute('href')).filter(h=>h&&!h.includes('/photo/')) : [];
  return {
    author: who ? who.innerText.split('\n')[0] : '',
    full: a ? a.innerText.slice(0, 1200) : 'none',
    links: [...new Set(links)].slice(0, 10),
    n: arts.length,
    replies: arts.slice(1, 10).map(x => {const t = x.querySelector('[data-testid="tweetText"]'); const h = x.querySelector('[data-testid="User-Name"]'); return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.slice(0, 330) : ''};})
  };
})())"""),
    ("caseoh_profile", "https://x.com/caseohOOC", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const bio = (document.querySelector('[data-testid="UserDescription"]') || {innerText:''}).innerText;
  return {bio: bio, posts: arts.slice(0, 20).map(a => {const t = a.querySelector('[data-testid="tweetText"]'); return (t ? t.innerText : '').slice(0, 200);})};
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
                await asyncio.sleep(6.0)
                out[tag] = await ev(s, page, js)
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e-caseoh-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:3000])

asyncio.run(main())
