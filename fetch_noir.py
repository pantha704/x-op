#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
ARTICLES = {
    "noir-1-outplaying-algorithm": "https://x.com/noironx/status/2013078582608966104",
    "noir-2-reply-guy-7-days": "https://x.com/noironx/status/2006618437242540180",
    "noir-3-quality-content-garbage": "https://x.com/noironx/status/2009199066010538177",
}

JS = r"""JSON.stringify({ title: document.title, text: (document.body.innerText || '').slice(0, 30000) })"""


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
            for name, u in ARTICLES.items():
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(4.5)
                # scroll to load full article
                for _ in range(6):
                    await call(s, "cloak_evaluate", {"page_id": page, "expression": "window.scrollBy(0, 1600); 'ok'"})
                    await asyncio.sleep(0.7)
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
                try:
                    d = json.loads(json.loads(r3).get("result", "{}"))
                except Exception:
                    d = {}
                body = d.get("text", "")
                fn = f"/home/ubuntu/x-op/reports/{name}.txt"
                open(fn, "w").write(d.get("title", "") + "\n\n" + body)
                print(f"=== {name} | {len(body)} chars | saved {fn}")
                print(body[:300].replace("\n", " | "))

asyncio.run(main())
