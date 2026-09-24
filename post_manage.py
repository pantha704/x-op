#!/usr/bin/env python3
"""Manage already-posted tweets: edit text (premium 1h window) or delete.

Usage:
  post_manage.py edit <post_url> "<new text>" [--clear]
  post_manage.py delete <post_url>

Edit flow: post page -> caret (More) -> "Edit post" -> editor -> select all ->
insert new text -> save -> toast verify.
Delete flow: post page -> caret -> "Delete post" -> confirm -> verify.

Prints step-by-step JSON so failures are debuggable.
"""
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, pid, js):
    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": js})
    try:
        return json.loads(json.loads(raw).get("result", "null"))
    except Exception:
        return {"raw": raw[:200]}


CARET_JS = r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  const scope = a || document;
  const b = scope.querySelector('[data-testid="caret"]');
  if (!b) return {ok:false, why:'no caret'};
  b.click(); return {ok:true};
})())"""

MENU_JS = r"""JSON.stringify((() => {
  const items = [...document.querySelectorAll('[role="menuitem"]')].filter(x => x.offsetParent !== null);
  return {ok:true, items: items.map(x => (x.innerText||'').trim().slice(0, 30))};
})())"""

CLICK_ITEM_JS = r"""JSON.stringify((() => {
  const want = __WANT__;
  const items = [...document.querySelectorAll('[role="menuitem"]')].filter(x => x.offsetParent !== null);
  for (const it of items) { if ((it.innerText||'').trim().toLowerCase().includes(want)) { it.click(); return {ok:true, picked:(it.innerText||'').trim().slice(0,30)}; } }
  return {ok:false, n: items.length, seen: items.map(x => (it => (it.innerText||'').trim())(x).slice(0,25))};
})())"""

EDITOR_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  return {ok: !!ed, len: ed ? (ed.innerText || '').length : 0, txt: ed ? (ed.innerText || '').slice(0, 70) : ''};
})())"""

SET_TEXT_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  ed.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('delete', false, null);
  const newText = __TEXT__;
  if (newText.length) document.execCommand('insertText', false, newText);
  return {ok:true, len: (ed.innerText || '').length, txt: (ed.innerText || '').slice(0, 70)};
})())"""

SAVE_JS = r"""JSON.stringify((() => {
  const b = document.querySelector('[data-testid="tweetButton"]') || document.querySelector('[data-testid="tweetButtonInline"]');
  if (!b) return {ok:false, why:'no save button'};
  if (b.getAttribute('aria-disabled') === 'true') return {ok:false, why:'disabled'};
  b.click(); return {ok:true};
})())"""

TOAST_JS = r"""JSON.stringify((() => {
  const t = document.querySelector('[data-testid="toast"]');
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  return {toast: t ? t.innerText.slice(0, 80) : null, editor: !!ed};
})())"""

CONFIRM_JS = r"""JSON.stringify((() => {
  const d = document.querySelector('[role="dialog"]') || document;
  const btns = [...d.querySelectorAll('[data-testid="confirmationSheetConfirm"], button')];
  for (const b of btns) { if ((b.innerText||'').trim().toLowerCase() === 'delete') { b.click(); return {ok:true}; } }
  return {ok:false, seen: btns.map(b => (b.innerText||'').trim().slice(0,20)).slice(0,8)};
})())"""


async def main():
    argv = sys.argv[1:]
    if len(argv) < 2:
        print("usage: post_manage.py edit <url> \"<text>\" [--clear] | post_manage.py delete <url>")
        sys.exit(2)
    mode, url = argv[0], argv[1]
    text = argv[2] if len(argv) > 2 else ""
    clear = "--clear" in argv

    async with streamable_http_client(URL) as ctx:
        async with ClientSession(ctx[0], ctx[1]) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": url}))
            pid = np.get("page_id") or np.get("id")
            await asyncio.sleep(6)

            c = await ev(s, pid, CARET_JS)
            print("caret:", json.dumps(c)[:120])
            await asyncio.sleep(1.2)
            m = await ev(s, pid, MENU_JS)
            print("menu:", json.dumps(m)[:300])

            want = "edit" if mode == "edit" else "delete"
            click = await ev(s, pid, CLICK_ITEM_JS.replace("__WANT__", json.dumps(want)))
            print("pick:", json.dumps(click)[:200])
            await asyncio.sleep(2.0)

            if mode == "edit":
                ed = await ev(s, pid, EDITOR_JS)
                print("editor:", json.dumps(ed)[:200])
                if not (isinstance(ed, dict) and ed.get("ok")):
                    await call(s, "cloak_close_page", {"page_id": pid})
                    sys.exit(5)
                st = await ev(s, pid, SET_TEXT_JS.replace("__TEXT__", json.dumps(text)))
                print("set:", json.dumps(st)[:160])
                await asyncio.sleep(1.4)
                sv = await ev(s, pid, SAVE_JS)
                print("save:", json.dumps(sv)[:140])
                if not (isinstance(sv, dict) and sv.get("ok")):
                    await call(s, "cloak_close_page", {"page_id": pid})
                    sys.exit(6)
                hit = False
                for _ in range(16):
                    t = await ev(s, pid, TOAST_JS)
                    if isinstance(t, dict) and (t.get("toast") or not t.get("editor")):
                        hit = True
                        print("toast:", t.get("toast"))
                        break
                    await asyncio.sleep(1.5)
                print("EDIT", "OK" if hit else "UNVERIFIED")
            else:
                await asyncio.sleep(1.0)
                cf = await ev(s, pid, CONFIRM_JS)
                print("confirm:", json.dumps(cf)[:200])
                await asyncio.sleep(2.5)
                gone = await ev(s, pid, r"""JSON.stringify((() => ({ body: (document.body.innerText||'').includes('This post was deleted'), url: location.href }))())""")
                print("DELETE", "OK" if (isinstance(cf, dict) and cf.get("ok")) else "FAILED", "|", json.dumps(gone)[:160])
            await call(s, "cloak_close_page", {"page_id": pid})


if __name__ == "__main__":
    asyncio.run(main())
