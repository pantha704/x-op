#!/usr/bin/env python3
"""Round 10 (e-slice): kitten mentions + caseohOOC timeline with dates."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

SEARCH_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, posts: arts.slice(0, 14).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    const time = a.querySelector('time');
    const link = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href'))[0] || '';
    return {who: h ? h.innerText.split('\n')[0] : '', time: time ? time.getAttribute('datetime') : '', url: link, txt: t ? t.innerText.replace(/\n/g, ' / ').slice(0, 300) : ''};
  })};
})())"""

PROFILE_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, posts: arts.slice(0, 16).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const time = a.querySelector('time');
    const link = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href'))[0] || '';
    return {time: time ? time.getAttribute('datetime') : '', url: link, txt: t ? t.innerText.replace(/\n/g, ' / ').slice(0, 300) : ''};
  })};
})())"""

JOBS = [
    ("kitten_caseoh", "https://x.com/search?q=caseoh%20kitten&src=typed_query&f=live", SEARCH_JS),
    ("clip_meta", "https://x.com/search?q=%22caseohOOC%22%20OR%20%22caseoh%20out%20of%20context%22%20since%3A2026-09-20&src=typed_query&f=live", SEARCH_JS),
    ("ooc_timeline", "https://x.com/caseohOOC", PROFILE_JS),
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
                    if isinstance(d, dict) and (d.get("n") or 0) > 0:
                        break
                    await asyncio.sleep(2.0)
                out[tag] = d if isinstance(d, dict) else {"err": str(d)}
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e-round10-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:3000])

asyncio.run(main())
