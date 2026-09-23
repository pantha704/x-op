#!/usr/bin/env python3
"""Full detail on every page: url/title/readyState/busy-ness."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

async def safe(s, name, args, t=25):
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
            lp = json.loads(await safe(s, "cloak_list_pages", {}))
            for i, pg in enumerate(lp.get("pages", [])):
                pid = pg["page_id"]
                js = ("JSON.stringify({url: document.location.href, title: document.title.slice(0,60), "
                      "ready: document.readyState, arts: document.querySelectorAll('article[data-testid=\"tweet\"]').length, "
                      "nav: (performance.getEntriesByType('navigation')[0]||{}).responseEnd||null})")
                st = await safe(s, "cloak_evaluate", {"page_id": pid, "expression": js}, 25)
                print(f"[{i}] {pid} {pg.get('url','')[:100]}")
                print(f"    -> {st[:400]}")

asyncio.run(main())
