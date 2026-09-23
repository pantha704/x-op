#!/usr/bin/env python3
"""Round 5 (e-slice): find caseohOOC / community posts about the Rewind 99 easter egg."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

JOBS = [
    ("ooc_rewind_search", "https://x.com/search?q=from%3AcaseohOOC%20rewind&src=typed_query&f=live", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, posts: arts.slice(0, 14).map(a => {const t = a.querySelector('[data-testid="tweetText"]'); const h = a.querySelector('[data-testid="User-Name"]'); return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.slice(0, 340) : ''};})};
})())"""),
    ("rewind_egg_search", "https://x.com/search?q=rewind%2099%20easter%20egg%20caseoh&src=typed_query&f=live", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, posts: arts.slice(0, 14).map(a => {const t = a.querySelector('[data-testid="tweetText"]'); const h = a.querySelector('[data-testid="User-Name"]'); return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.slice(0, 340) : ''};})};
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
                d = None
                for attempt in range(3):
                    await call(s, "cloak_navigate", {"page_id": page, "url": u})
                    await asyncio.sleep(6.5)
                    d = await ev(s, page, js)
                    if isinstance(d, dict) and (d.get("n") or 0) > 1:
                        break
                    await asyncio.sleep(2.0)
                out[tag] = d if isinstance(d, dict) else {"err": str(d)}
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e-rewind-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:3500])

asyncio.run(main())
