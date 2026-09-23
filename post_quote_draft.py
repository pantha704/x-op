#!/usr/bin/env python3
"""Save a QUOTE post as a native X DRAFT (comment + embedded target post).

Like quote_publish.py but instead of publishing, saves the draft into the account's
drafts folder (visible in the owner's app, card attached).

Usage: post_quote_draft.py <target_url> "<comment text>"

Flow: target permalink -> retweet -> Quote menu -> composer (card auto-attached) ->
type -> verify card -> close -> Save sheet. Never publishes.
"""
import asyncio
import json
import re
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
  if (q) { q.click(); return {ok:true, via:'menuitem'}; }
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
  return {ok:true, len: (ed.innerText || '').length};
})())"""

APPEND_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  ed.focus();
  document.execCommand('insertText', false, %s);
  return {ok:true, len: (ed.innerText || '').length};
})()"""

CARD_JS = r"""JSON.stringify((() => {
  const d = document.querySelector('[role="dialog"]') || document;
  const byAvatar = !!d.querySelector('[data-testid="UserAvatar-Container-__HANDLE__"]');
  const byText = (d.innerText || '').includes('__HANDLE__');
  return {ok: byAvatar || byText, byAvatar, byText};
})())"""

CLOSE_JS = r"""JSON.stringify((() => {
  const c = document.querySelector('[data-testid="app-bar-close"]') || document.querySelector('[aria-label="Close"]');
  if (c) { c.click(); return {ok:true, via:'close'}; }
  return {ok:false};
})())"""

CONFIRM_JS = r"""JSON.stringify((() => {
  const c = document.querySelector('[data-testid="confirmationSheetConfirm"]');
  if (c) { c.click(); return {ok:true, clicked:'confirm-sheet'}; }
  const btns = [...document.querySelectorAll('[role="button"],button')];
  const save = btns.find(b => /^(save|save draft)$/i.test((b.innerText||'').trim()));
  if (save) { save.click(); return {ok:true, clicked:'save-text'}; }
  return {ok:false, why:'no save button', texts: btns.map(b=>(b.innerText||'').trim()).filter(Boolean).slice(0,12)};
})())"""


async def main():
    target, text = sys.argv[1], sys.argv[2]
    handle = target.split("/")[3] if "/status/" in target else ""
    # HARD RULE (owner 2026-09-23): quote drafts carry the target tweet URL as the last line.
    if not text.rstrip().endswith(target):
        text = text.rstrip() + "\n" + target

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
            await asyncio.sleep(2.4)
            # NATIVE TYPE (2026-09-23): stable with "\n" (JS inserts get mangled by linkify/autosave).
            ref = None
            try:
                snap_raw = await call(s, "cloak_snapshot", {"page_id": pid})
                try:
                    snap = json.loads(snap_raw).get("snapshot", snap_raw)
                except Exception:
                    snap = snap_raw.replace("\\n", "\n")
                idx = snap.find("[Modal/Dialog]")
                seg = snap[idx:idx+1500] if idx != -1 else snap
                m = re.search(r'\[@(e\d+)\] div\[textbox\]', seg)
                ref = m.group(1) if m else None
            except Exception as e:
                print("snapshot err:", str(e)[:80])
            if ref:
                tr = await call(s, "cloak_type", {"page_id": pid, "ref": ref, "text": text, "clear": True})
                print("type:", tr[:120])
            else:
                print("no ref; fallback JS insert")
                tp = await ev(s, pid, TYPE_JS % json.dumps(text))
                print("type:", tp)
            await asyncio.sleep(1.2)
            card = await ev(s, pid, CARD_JS.replace("__HANDLE__", handle))
            print("card:", card)
            # save as draft: close -> confirm sheet
            cl = await ev(s, pid, CLOSE_JS)
            print("close:", cl)
            await asyncio.sleep(1.6)
            sv = await ev(s, pid, CONFIRM_JS)
            print("save:", sv)
            await asyncio.sleep(1.2)
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass
            ok = isinstance(card, dict) and card.get("ok")
            print("DONE" if ok else "WARN: card not confirmed - check the draft in the app")


if __name__ == "__main__":
    asyncio.run(main())
