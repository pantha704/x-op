#!/usr/bin/env python3
"""Fetch full text + stats for specific X status URLs via the research rig (8933)."""
import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8933/mcp"

READ_JS = r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return {err:'no article', body: document.body.innerText.slice(0,600)};
  const tx = a.querySelector('[data-testid="tweetText"]');
  const un = a.querySelector('[data-testid="User-Name"]');
  const grp = a.querySelector('[role="group"]');
  const t = a.querySelector('time');
  return {
    who: un ? un.innerText.replace(/\n/g,' | ') : '',
    text: tx ? tx.innerText : '',
    stats: grp ? grp.getAttribute('aria-label') : '',
    time: t ? t.getAttribute('datetime') : ''
  };
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    urls = json.load(open(sys.argv[1]))
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = await call(s, "cloak_new_page", {})
            page = json.loads(np).get("page_id")
            for u in urls:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(5)
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                try:
                    d = json.loads(json.loads(r3).get("result", "{}") or "{}")
                except Exception:
                    d = {"err": r3[:300]}
                print("=" * 72)
                print("URL:", u)
                print("WHO:", (d.get("who") or "").replace("\n", " "))
                print("TIME:", d.get("time"))
                print("STATS:", (d.get("stats") or "").replace("\n", " "))
                print("TEXT:")
                print(d.get("text") or d.get("err"))
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass

asyncio.run(main())
