#!/usr/bin/env python3
"""Find OUR reply permalink for a fired reply by text search (curated-track link reporting).

Usage: replylink.py "<reply text>" 
Prints the your_handle reply URL, or exits 1 if not found.
Uses the live rig (MCP :8932). Run when no fire wave is live.
"""
import asyncio, json, sys, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
LIST_JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 12).map(a => {
  const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
  const tx = a.querySelector('[data-testid="tweetText"]');
  return { url: tl ? tl.href.split('?')[0] : null, text: tx ? tx.innerText.replace(/\n/g, ' ') : '' };
}).filter(x => x.url))"""

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def main():
    text = sys.argv[1]
    probe = " ".join(text.split()[:5]).lower()
    q = "from:your_handle " + " ".join(text.split()[:6])
    nav = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=live"
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            pages = json.loads(lp).get("pages", [])
            page = pages[0]["page_id"] if pages else json.loads(await call(s, "cloak_launch", {"user_data_dir": "/home/ubuntu/.cloakbrowser/profiles/operator"})).get("page_id")
            await call(s, "cloak_navigate", {"page_id": page, "url": nav})
            await asyncio.sleep(3)
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": LIST_JS})
            rows = json.loads(json.loads(r3).get("result", "[]"))
            for row in rows:
                if probe[:28] in (row.get("text") or "").lower() and "your_handle" in (row.get("url") or ""):
                    print(row["url"]); return
            print("NOT FOUND"); sys.exit(1)

asyncio.run(main())
