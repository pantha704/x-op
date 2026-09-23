#!/usr/bin/env python3
"""Rig re-login for @your_handle - restores the cloakbrowser session when X logs the account out.

Reads creds from ~/.config/x-op/x-creds.json (created by save_x_creds.sh; values never printed).
Drives the rig's own browser (MCP :8932, profile operator) through the X login flow.

Usage:
  ./venv/bin/python relogin_rig.py --check          # is the session alive?
  ./venv/bin/python relogin_rig.py                  # full login attempt
  ./venv/bin/python relogin_rig.py --code 123456    # resume with the emailed/app code

The code is one-time; ask LO for it, never store it.
"""
import argparse, asyncio, json, os, re, sys

CREDS = os.path.expanduser("~/.config/x-op/x-creds.json")
MCP = "http://127.0.0.1:8932/mcp"


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def find_ref(s, page, patterns):
    snap = await call(s, "cloak_snapshot", {"page_id": page})
    for line in snap.splitlines():
        low = line.lower()
        if any(p in low for p in patterns):
            m = re.search(r"@(e\d+)", line)
            if m:
                return m.group(1)
    return None


async def state(s, page):
    raw = await call(s, "cloak_evaluate", {"page_id": page, "expression":
        "(()=>{const logged=!!document.querySelector('[data-testid=\"SideNav_AccountSwitcher_Button\"]');"
        "const c=(document.body.innerText||'').slice(0,300);return JSON.stringify({logged,url:location.href,head:c})})()"})
    try:
        return json.loads(json.loads(raw).get("result", "{}"))
    except Exception:
        return {"logged": False, "url": "", "head": raw[:200]}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--code", default=None)
    a = ap.parse_args()

    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(MCP) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np_ = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            page = np_.get("page_id") or np_.get("id")
            await asyncio.sleep(8)
            st = await state(s, page)
            print("session logged_in =", st["logged"], "| url:", st["url"])
            if a.check:
                await call(s, "cloak_close_page", {"page_id": page})
                return
            if st["logged"]:
                print("already logged in - nothing to do")
                await call(s, "cloak_close_page", {"page_id": page})
                return

            if not os.path.exists(CREDS):
                print(f"MISSING CREDS: {CREDS}")
                print("run:  bash /home/ubuntu/x-op/save_x_creds.sh   (LO does this, values stay hidden)")
                await call(s, "cloak_close_page", {"page_id": page})
                sys.exit(2)
            creds = json.load(open(CREDS))
            ident, pwd = creds["identifier"], creds["password"]

            # 1) username step
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/i/flow/login"})
            await asyncio.sleep(7)
            ref = await find_ref(s, page, ["username", "email", "phone", "textbox"])
            if not ref:
                print("could not find the username field - snapshot:")
                print(await call(s, "cloak_snapshot", {"page_id": page}))
                await call(s, "cloak_close_page", {"page_id": page})
                sys.exit(3)
            await call(s, "cloak_type", {"page_id": page, "ref": ref, "text": ident, "clear": True})
            await asyncio.sleep(1.5)
            await call(s, "cloak_press_key", {"page_id": page, "key": "Enter"})
            await asyncio.sleep(5)

            # 2) password step (or code step if X challenges early)
            st2 = await state(s, page)
            if "code" in st2["head"].lower() or "verif" in st2["head"].lower():
                if a.code:
                    ref = await find_ref(s, page, ["textbox", "code", "digit"])
                    if ref:
                        await call(s, "cloak_type", {"page_id": page, "ref": ref, "text": a.code, "clear": True})
                        await call(s, "cloak_press_key", {"page_id": page, "key": "Enter"})
                        await asyncio.sleep(6)
                else:
                    print("NEEDS-CODE (early): X wants a verification code. Ask LO, rerun with --code <digits>")
                    await call(s, "cloak_close_page", {"page_id": page})
                    return

            ref = await find_ref(s, page, ["password"])
            if not ref:
                st3 = await state(s, page)
                print("no password field found. state:", json.dumps(st3)[:300])
                print("if this says code/verification: rerun with --code <digits>")
                await call(s, "cloak_close_page", {"page_id": page})
                sys.exit(4)
            await call(s, "cloak_type", {"page_id": page, "ref": ref, "text": pwd, "clear": True})
            await asyncio.sleep(1.5)
            await call(s, "cloak_press_key", {"page_id": page, "key": "Enter"})
            await asyncio.sleep(8)

            # 3) post-login: code challenge or success
            st4 = await state(s, page)
            if st4["logged"]:
                print("LOGIN OK - session restored")
                await call(s, "cloak_close_page", {"page_id": page})
                return
            head = st4["head"].lower()
            if a.code:
                ref = await find_ref(s, page, ["textbox", "code", "digit"])
                if ref:
                    await call(s, "cloak_type", {"page_id": page, "ref": ref, "text": a.code, "clear": True})
                    await call(s, "cloak_press_key", {"page_id": page, "key": "Enter"})
                    await asyncio.sleep(8)
                    st5 = await state(s, page)
                    print("after code:", "LOGIN OK" if st5["logged"] else json.dumps(st5)[:250])
            elif "code" in head or "verif" in head or "challenge" in head or "unusual" in head:
                print("NEEDS-CODE: X wants a verification code. Ask LO, rerun with --code <digits>")
            else:
                print("not logged in yet. state:", json.dumps(st4)[:300])
            await call(s, "cloak_close_page", {"page_id": page})


asyncio.run(main())
