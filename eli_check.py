#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
POST = "https://x.com/EliraEcwipse_/status/2100175469807341769"
JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].map(a => (a.innerText || '').replace(/\n/g, ' | ').slice(0, 130)))"""

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
            await call(s, "cloak_navigate", {"page_id": page, "url": POST})
            await asyncio.sleep(3.5)
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
            arts = json.loads(json.loads(r3).get("result", "[]"))
            ours = [a for a in arts if "operator" in a.lower()]
            print("our replies on the post:", len(ours))
            for o in ours:
                print("  >", o[:120])

asyncio.run(main())
