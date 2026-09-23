#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def main():
    async with streamable_http_client("http://127.0.0.1:8932/mcp") as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/notifications"})
            await asyncio.sleep(4)
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": "document.body.innerText.slice(0, 6000)"})
            print(json.loads(r3).get("result", ""))

asyncio.run(main())
