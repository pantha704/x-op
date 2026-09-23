#!/usr/bin/env python3
"""Handover: take control of the @your_handle browser on uwuntu.

Run AFTER the orphaned chrome is killed (ssh pkill). Does:
 1. MCP handshake + tool inventory (proof of the channel)
 2. cloak_launch on the persistent profile  (relaunch under our control)
 3. navigate x.com/home
 4. verify the logged-in account chip
"""
import asyncio
import json
import traceback

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8931/mcp"
PROFILE = "/home/operator/.cloakbrowser/profiles/operator"


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    parts = []
    for c in getattr(res, "content", []) or []:
        parts.append(getattr(c, "text", None) or str(c))
    return "\n".join(parts)


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            si = getattr(init, "server_info", None) or getattr(init, "serverInfo", None)
            print("SERVER:", si)
            tools = await s.list_tools()
            tlist = getattr(tools, "tools", [])
            names = [getattr(t, "name", "?") for t in tlist]
            print("TOOLS(%d): %s" % (len(names), ", ".join(names)))

            print("---- cloak_launch (persistent profile) ----")
            r1 = await call(s, "cloak_launch", {"user_data_dir": PROFILE})
            print("LAUNCH:", r1[:600])
            page_id = None
            try:
                page_id = json.loads(r1).get("page_id")
            except Exception:
                pass
            if not page_id:
                print("NO PAGE_ID — launch failed; stop here")
                return 2

            print("---- navigate x.com/home ----")
            r2 = await call(s, "cloak_navigate", {"page_id": page_id, "url": "https://x.com/home"})
            print("NAV:", r2[:300])
            await asyncio.sleep(7)

            print("---- verify login chip ----")
            expr = (
                "(() => { const el = document.querySelector('[data-testid=\"SideNav_AccountSwitcher_Button\"]');"
                " if (el) return 'CHIP: ' + el.innerText;"
                " return 'NOCHIP | url=' + location.href + ' | body=' + (document.body ? document.body.innerText.slice(0, 200) : 'nobody'); })()"
            )
            r3 = await call(s, "cloak_evaluate", {"page_id": page_id, "expression": expr})
            print("VERIFY:", r3[:800])
            print("PAGE_ID_FOR_LATER:", page_id)
            return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
