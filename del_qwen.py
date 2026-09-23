#!/usr/bin/env python3
"""Delete our reply on the Qwen post, verify gone."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "https://x.com/QwenDevs/status/2101917379785838660"

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
            await call(s, "cloak_navigate", {"page_id": page, "url": URL})
            await asyncio.sleep(5)
            # find our reply's caret
            js = """(() => {
              const arts = Array.from(document.querySelectorAll('article[data-testid=\\"tweet\\"]'));
              for (const a of arts) {
                const link = a.querySelector('a[href*="your_handle"]');
                if (link) {
                  const caret = a.querySelector('[data-testid="caret"]');
                  if (caret) { caret.click(); return 'clicked-caret'; }
                }
              }
              return 'no-caret-found';
            })()"""
            r1 = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
            print("step1:", json.loads(r1).get("result"))
            await asyncio.sleep(2)
            # click Delete in menu
            js2 = """(() => {
              const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
              const del = items.find(i => /delete/i.test(i.innerText));
              if (del) { del.click(); return 'clicked-delete'; }
              return 'no-delete-item';
            })()"""
            r2 = await call(s, "cloak_evaluate", {"page_id": page, "expression": js2})
            print("step2:", json.loads(r2).get("result"))
            await asyncio.sleep(2)
            # confirm dialog
            js3 = """(() => {
              const btn = document.querySelector('[data-testid="confirmationSheetConfirm"]');
              if (btn) { btn.click(); return 'confirmed'; }
              return 'no-confirm';
            })()"""
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": js3})
            print("step3:", json.loads(r3).get("result"))
            await asyncio.sleep(4)
            # verify our reply gone
            js4 = """(() => {
              const arts = Array.from(document.querySelectorAll('article[data-testid=\\"tweet\\"]'));
              const mine = arts.filter(a => a.querySelector('a[href*="your_handle"]'));
              return JSON.stringify({count: mine.length});
            })()"""
            r4 = await call(s, "cloak_evaluate", {"page_id": page, "expression": js4})
            print("verify:", json.loads(r4).get("result"))

asyncio.run(main())
