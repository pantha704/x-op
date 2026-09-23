#!/usr/bin/env python3
"""Round 4: rewind 99 context + quotes of caseoh clip post."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

JOBS = [
    ("quotes", "https://x.com/caseohOOC/status/2101902335828218236/quotes", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, items: arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), t: (t ? t.innerText.slice(0, 320) : '')};
  })};
})())"""),
    ("search_rewind", "https://x.com/search?q=%22rewind%2099%22%20caseoh&src=typed_query&f=live", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, items: arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), t: (t ? t.innerText.slice(0, 320) : '')};
  })};
})())"""),
    ("search_clip", "https://x.com/search?q=caseoh%20cat%20dance%20easter%20egg&src=typed_query&f=live", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, items: arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), t: (t ? t.innerText.slice(0, 320) : '')};
  })};
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
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e4-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:2600])

asyncio.run(main())
