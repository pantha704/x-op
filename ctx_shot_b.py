#!/usr/bin/env python3
import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
TARGETS = [
    ("dotty", "https://x.com/Dottyyidi/status/2101929850135249266"),
    ("faith", "https://x.com/faithliannee/status/2101881819784151276"),
]


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            tl = await s.list_tools()
            names = [t.name for t in tl.tools]
            print("TOOLS:", names)
            shot = [n for n in names if "screenshot" in n.lower()]
            print("SHOT TOOL:", shot)
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for tag, u in TARGETS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(4.0)
                if shot:
                    res = await call(s, shot[0], {"page_id": page})
                    print("=" * 60)
                    print(tag, "->", res[:700])

asyncio.run(main())
