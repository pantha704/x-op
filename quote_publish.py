#!/usr/bin/env python3
"""Publish a QUOTE post (our comment + embedded target post) via the rig MCP.

Quote posts are ORIGINAL posts: they count toward verified Home Timeline
impressions (replies do not). Owner idea 2026-09-22.

Usage: quote_publish.py <target_url> "<comment text>" [--dry]
  --dry: open the quote composer, type the comment, verify the card attaches,
         then CANCEL (no publish). Safe test.

Flow: target permalink -> retweet button -> Quote menu -> composer -> type ->
verify card -> click Post -> verify toast. Own tab; safe beside live waves,
but fire only when the reply lane is quiet (same discipline as run_wave).
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


OPEN_QUOTE_JS = r"""JSON.stringify((() => {
  const b = document.querySelector('[data-testid="retweet"]');
  if (!b) return {ok:false, why:'no retweet button'};
  b.click(); return {ok:true};
})())"""

MENU_JS = r"""JSON.stringify((() => {
  const items = [...document.querySelectorAll('[role="menuitem"]')];
  const q = items.find(x => /quote/i.test(x.innerText || ''));
  if (q) { q.click(); return {ok:true, via:'menuitem', text:(q.innerText||'').slice(0,20)}; }
  const link = [...document.querySelectorAll('a[href*="/compose/post"]')].find(a => /quote/i.test(a.innerText||''));
  if (link) { link.click(); return {ok:true, via:'link'}; }
  return {ok:false, items: items.map(x => (x.innerText||'').slice(0,24))};
})())"""

TYPE_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  ed.focus();
  if ((ed.innerText || '').length > 0) {
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    ed.focus();
  }
  document.execCommand('insertText', false, %s);
  return {ok:true, len: (ed.innerText || '').length, text: (ed.innerText || '').slice(0, 80)};
})())"""

CARD_JS = r"""JSON.stringify((() => {
  const d = document.querySelector('[role="dialog"]') || document;
  const byAvatar = !!d.querySelector('[data-testid="UserAvatar-Container-__HANDLE__"]');
  const byText = (d.innerText || '').includes('__HANDLE__');
  const hasAttach = !!d.querySelector('[data-testid="attachments"]');
  return {ok: byAvatar || byText, byAvatar, byText, hasAttach};
})())"""

CANCEL_JS = r"""JSON.stringify((() => {
  const c = document.querySelector('[data-testid="app-bar-close"]') || document.querySelector('[aria-label="Close"]');
  if (c) { c.click(); return {ok:true}; }
  return {ok:false};
})())"""


async def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    args = [a for a in args if a != "--dry"]
    target, text = args[0], args[1]
    sid = target.rstrip("/").split("/")[-1]

    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": target}))
            pid = np.get("page_id") or np.get("id")
            print("page:", pid)
            await asyncio.sleep(4.5)
            oq = await ev(s, pid, OPEN_QUOTE_JS)
            print("retweet-click:", oq)
            await asyncio.sleep(1.6)
            mq = await ev(s, pid, MENU_JS)
            print("quote-menu:", mq)
            await asyncio.sleep(2.2)
            tp = await ev(s, pid, TYPE_JS % json.dumps(text))
            print("type:", tp)
            if isinstance(tp, dict) and tp.get("len") and tp["len"] != len(text):
                await asyncio.sleep(0.8)
                tp2 = await ev(s, pid, TYPE_JS % json.dumps(text))
                print("retype:", tp2)
            await asyncio.sleep(1.2)
            handle = target.split("/")[3] if "/status/" in target else ""
            card = await ev(s, pid, CARD_JS.replace("__HANDLE__", handle))
            print("card:", card)
            if dry:
                print("DRY OK - composer ready, card attached" if (isinstance(card, dict) and card.get("ok")) else "DRY - card not confirmed")
                await ev(s, pid, CANCEL_JS)
                await asyncio.sleep(1)
                await call(s, "cloak_close_page", {"page_id": pid})
                return
            # click Post
            for attempt in range(3):
                po = await ev(s, pid, r"""JSON.stringify((() => {
                  const b = document.querySelector('[data-testid="tweetButton"]') || document.querySelector('[data-testid="tweetButtonInline"]');
                  if (!b) return {ok:false, why:'no button'};
                  if (b.getAttribute('aria-disabled') === 'true') return {ok:false, why:'disabled'};
                  b.click(); return {ok:true};
                })())""")
                print("post-click:", po)
                if isinstance(po, dict) and po.get("ok"):
                    break
                await asyncio.sleep(2)
            sent = False
            for _ in range(20):
                st = await ev(s, pid, r"""JSON.stringify((() => {
                  const toast = document.querySelector('[data-testid="toast"]');
                  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
                  return { toast: toast ? toast.innerText.slice(0,60) : null, editor: !!ed };
                })())""")
                if isinstance(st, dict) and (st.get("toast") or not st.get("editor")):
                    sent = True
                    print("verify:", st)
                    break
                await asyncio.sleep(1.5)
            print("SENT" if sent else "UNVERIFIED - check the profile")
            await call(s, "cloak_close_page", {"page_id": pid})


if __name__ == "__main__":
    asyncio.run(main())
