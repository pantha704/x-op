#!/usr/bin/env python3
"""Delete the OLD (watermarked) post with a given caption, keeping the fresher duplicate.
Targets by caption text, picks the article with the OLDEST timestamp, opens its caret menu,
clicks Delete, confirms. Owner-authorized deletion only.

Usage: post_delete_old.py "<caption text>"
Prints what it found (timestamps) and the outcome.
"""
import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
CAPTION = sys.argv[1]

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def ev(s, pid, js):
    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": js})
    try:
        return json.loads(json.loads(raw).get("result", "null"))
    except Exception:
        return {"raw": raw[:300]}

FIND_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const out = [];
  arts.forEach((a, i) => {
    const t = (a.innerText||'');
    if (!t.includes(%s)) return;
    const time = a.querySelector('time');
    out.push({ idx: i, dt: time ? time.getAttribute('datetime') : null, snippet: t.replace(/\n/g,' ').slice(0,80) });
  });
  return { found: out, total: arts.length };
})())""" % json.dumps(CAPTION)

async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/your_handle"}))
            pid = np.get("page_id") or np.get("id")
            print("page:", pid)
            await asyncio.sleep(6)
            found = await ev(s, pid, FIND_JS)
            print("found:", json.dumps(found)[:500])
            items = (found or {}).get("found") or []
            if len(items) < 2:
                print("NOTE: fewer than 2 matches - check manually before deleting")
            if not items:
                await call(s, "cloak_close_page", {"page_id": pid}); return
            # oldest = the one to remove
            target = sorted(items, key=lambda x: x["dt"] or "")[0]
            print("deleting target:", target)
            old_dt = target["dt"]
            # click the caret of that article
            ck = await ev(s, pid, r"""JSON.stringify((() => {
              const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
              const a = arts.find(x => { const t = x.querySelector('time'); return t && t.getAttribute('datetime') === %s; });
              if (!a) return {ok:false};
              const c = a.querySelector('[data-testid="caret"]') || a.querySelector('[aria-label*="More"]');
              if (!c) return {ok:false, why:'no caret'};
              c.click(); return {ok:true};
            })())""" % json.dumps(old_dt))
            print("caret:", ck)
            await asyncio.sleep(1.5)
            dl = await ev(s, pid, r"""JSON.stringify((() => {
              const items = [...document.querySelectorAll('[role="menuitem"]')];
              const del = items.find(i => /^delete$/i.test((i.innerText||'').trim()));
              if (!del) return {ok:false, seen: items.map(i=>(i.innerText||'').trim()).slice(0,8)};
              del.click(); return {ok:true};
            })())""")
            print("menu:", dl)
            await asyncio.sleep(1.5)
            cf = await ev(s, pid, r"""JSON.stringify((() => {
              const c = document.querySelector('[data-testid="confirmationSheetConfirm"]');
              if (!c) return {ok:false};
              c.click(); return {ok:true};
            })())""")
            print("confirm:", cf)
            await asyncio.sleep(3)
            # verify: caption should now appear once
            left = await ev(s, pid, FIND_JS)
            print("after:", json.dumps(left)[:400])
            await call(s, "cloak_close_page", {"page_id": pid})

asyncio.run(main())
