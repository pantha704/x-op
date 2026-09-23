#!/usr/bin/env python3
"""Read-only MCP probe: page list + current URL/state. Timeout guarded."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

async def safe(s, name, args, t=20):
    try:
        res = await asyncio.wait_for(s.call_tool(name, args), timeout=t)
        return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])
    except Exception as ex:
        return f"TIMEOUT/ERR: {type(ex).__name__}: {ex}"

async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await safe(s, "cloak_list_pages", {})
            print("PAGES:", lp[:3000])
            try:
                pages = json.loads(lp).get("pages", [])
            except Exception:
                pages = []
            if pages:
                pid = pages[0]["page_id"]
                loc = await safe(s, "cloak_evaluate", {"page_id": pid, "expression": "JSON.stringify({url: document.location.href, title: document.title, ready: document.readyState, articles: document.querySelectorAll('article[data-testid=\"tweet\"]').length})"}, 25)
                print("LOC:", loc[:1500])

asyncio.run(main())
