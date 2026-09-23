#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
POSTS = [
    "https://x.com/TidyWire/status/2101870016656199836",
    "https://x.com/GenshinImpact/status/2101886637714112703",
]

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
            for u in POSTS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(4)
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
                try:
                    arts = json.loads(json.loads(r3).get("result", "[]"))
                except Exception:
                    arts = []
                ours = [a for a in arts if "your_handle" in a or "operator" in a.lower()]
                print("=" * 60)
                print(u.split("/")[-3], "| articles:", len(arts), "| ours-ish:", len(ours))
                for a in ours[:6]:
                    print("  >", a[:120])
                # fuzzy: also search our known texts
                for probe in ["piece is stunning", "more events than the month"]:
                    cnt = sum(1 for a in arts if probe in a)
                    if cnt:
                        print(f"  probe '{probe[:25]}...' appears in {cnt} article(s)")

asyncio.run(main())
