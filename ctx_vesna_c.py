#!/usr/bin/env python3
import asyncio, json, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

READ_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return arts.slice(0, 8).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    const link = [...a.querySelectorAll('a')].map(x => x.href).filter(x => x.includes('/status/'))[0] || '';
    return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.slice(0,300) : '', link};
  });
})())"""

Q = "https://x.com/search?" + urllib.parse.urlencode({"q": "vesna trailer", "f": "live"})


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
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]

            # 1) official Vesna trailer post -> then its replies
            await call(s, "cloak_navigate", {"page_id": page, "url": Q})
            await asyncio.sleep(5.0)
            d = await ev(s, page, READ_JS)
            print("=" * 70)
            print("SEARCH vesna trailer:")
            print(json.dumps(d, indent=1)[:2500])

            # find official trailer link
            trailer = ''
            for it in (d or []):
                if it.get('who', '').startswith('Genshin Impact') and 'Trailer' in it.get('txt', ''):
                    trailer = it.get('link', '')
            print("TRAILER LINK:", trailer)
            if trailer:
                await call(s, "cloak_navigate", {"page_id": page, "url": trailer})
                await asyncio.sleep(5.0)
                d2 = await ev(s, page, READ_JS)
                print("=" * 70)
                print("TRAILER POST + REPLIES:")
                print(json.dumps(d2, indent=1)[:3500])

asyncio.run(main())
