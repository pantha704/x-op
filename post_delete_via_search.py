#!/usr/bin/env python3
"""Delete a specific old post found via search (robust to deep timelines).
Usage: post_delete_via_search.py "<caption text>"
Searches from:your_handle for the text, opens the matching post page, deletes it.
If multiple matches, picks the OLDEST by timestamp.
"""
import asyncio, json, sys, urllib.parse
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

async def main():
    q = "from:your_handle " + CAPTION[:60]
    surl = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=live"
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": surl}))
            pid = np.get("page_id") or np.get("id")
            print("page:", pid)
            await asyncio.sleep(7)
            res = await ev(s, pid, r"""JSON.stringify((() => {
              const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
              const out = [];
              arts.forEach(a => {
                const t = (a.innerText||'');
                if (!t.includes(%s)) return;
                const time = a.querySelector('time');
                const link = time ? time.closest('a') : null;
                out.push({ dt: time ? time.getAttribute('datetime') : null, url: link ? link.href.split('?')[0] : null });
              });
              return out;
            })())""" % json.dumps(CAPTION[:50]))
            matches = res if isinstance(res, list) else []
            print("matches:", json.dumps(matches)[:400])
            if not matches:
                print("no matches found via search"); await call(s, "cloak_close_page", {"page_id": pid}); return
            target = sorted(matches, key=lambda x: x.get("dt") or "")[0]
            print("target:", target)
            if not target.get("url"):
                print("no url"); await call(s, "cloak_close_page", {"page_id": pid}); return
            await call(s, "cloak_navigate", {"page_id": pid, "url": target["url"]})
            await asyncio.sleep(5)
            ck = await ev(s, pid, r"""JSON.stringify((() => {
              const a = document.querySelector('article[data-testid="tweet"]');
              if (!a) return {ok:false};
              const c = a.querySelector('[data-testid="caret"]') || a.querySelector('[aria-label*="More"]');
              if (!c) return {ok:false, why:'no caret'};
              c.click(); return {ok:true};
            })())""")
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
            # verify: page should show the post is gone
            gone = await ev(s, pid, r"""JSON.stringify((() => {
              const body = (document.body.innerText||'');
              return { stillThere: body.includes(%s) && !body.includes('This post was deleted'), deletedNote: body.includes('This post was deleted') };
            })())""" % json.dumps(CAPTION[:40]))
            print("verify:", gone)
            await call(s, "cloak_close_page", {"page_id": pid})

asyncio.run(main())
