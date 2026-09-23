#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

READ_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return arts.slice(0, 10).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const tlink = [...a.querySelectorAll('a')].map(x => x.href).filter(h => h.includes('/status/') && !h.includes('photo') && !h.includes('analytics'));
    const vids = [...a.querySelectorAll('video')].map(v => (v.poster||'').slice(0,160));
    const media = [...a.querySelectorAll('img')].filter(i => i.src.includes('media')).map(i => i.src.slice(0,160));
    return {txt: t ? t.innerText.slice(0,120) : '', link: tlink[0] || '', vids, media};
  });
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/yy624022"})
            await asyncio.sleep(5.0)
            r1 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
            print(r1[:4000])

asyncio.run(main())
