#!/usr/bin/env python3
"""Round 9 (e-slice): quotes of the clip post with URLs + rio post."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

QUOTES_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, posts: arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    const link = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href'))[0] || '';
    return {who: h ? h.innerText.split('\n')[0] : '', url: link, txt: t ? t.innerText.replace(/\n/g, ' / ').slice(0, 400) : ''};
  })};
})())"""

POST_JS = r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return {err: 'none'};
  const h = a.querySelector('[data-testid="User-Name"]');
  const t = a.querySelector('[data-testid="tweetText"]');
  const time = a.querySelector('time');
  return {who: h ? h.innerText : '', time: time ? time.getAttribute('datetime') : '', txt: t ? t.innerText : '', full: a.innerText.slice(0, 800)};
})())"""

JOBS = [
    ("clip_quotes", "https://x.com/caseohOOC/status/2101902335828218236/quotes", QUOTES_JS),
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
    seen = set()
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
                # follow-up: fetch each quoted post
                for p in (out[tag].get("posts") or [])[:4]:
                    u2 = p.get("url")
                    if u2 and u2 not in seen:
                        seen.add(u2)
                        await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com" + u2})
                        await asyncio.sleep(6.0)
                        out["post:" + u2] = await ev(s, page, POST_JS)
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e-quotes2-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:2500])

asyncio.run(main())
