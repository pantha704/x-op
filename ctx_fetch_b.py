#!/usr/bin/env python3
import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
URLS = json.load(open(sys.argv[1]))
OUT = sys.argv[2]

READ_JS = r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return null;
  const tx = a.querySelector('[data-testid="tweetText"]');
  const un = a.querySelector('[data-testid="User-Name"]');
  const imgs = [...a.querySelectorAll('img')].map(i => i.src).filter(s => s.includes('media') || s.includes('twimg'));
  return { text: tx ? tx.innerText : '', who: un ? un.innerText.slice(0, 60) : '', imgs: imgs.slice(0,4) };
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    out = []
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for u in URLS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(3.5)
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                try:
                    d = json.loads(json.loads(r3).get("result", "null") or "null")
                except Exception:
                    d = None
                rec = {"url": u, "data": d}
                out.append(rec)
                print("=" * 66)
                print(u)
                if d:
                    print("WHO:", d.get("who", "").replace("\n", " | ")[:80])
                    print("TXT:", d.get("text", "").replace("\n", " ")[:600])
                    print("IMGS:", d.get("imgs"))
                else:
                    print("(no data)")
    json.dump(out, open(OUT, "w"), indent=1)

asyncio.run(main())
