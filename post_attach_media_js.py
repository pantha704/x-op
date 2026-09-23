#!/usr/bin/env python3
"""Attach media to X drafts by INJECTING the file into the composer's file input via JS
(DataTransfer), all through the rig MCP - no CDP, no native file chooser.

Flow per draft: open drafts -> click the matching draft -> inject image -> wait for preview
-> Escape -> Save -> back to drafts. Never posts.

Usage: post_attach_media_js.py <pairs.json>
"""
import asyncio, base64, json, sys
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

OPEN_DRAFTS = r"""JSON.stringify((() => {
  const c = [...document.querySelectorAll('a,button,div[role="button"],span')].filter(e => /^drafts$/i.test((e.innerText||'').trim()));
  if (c.length) c[0].click();
  return {n: document.querySelectorAll('[data-testid="unsentTweet"]').length};
})())"""

PUSH_CHUNK = "window.__up = window.__up || {parts: []}; window.__up.parts.push(%s); window.__up.parts.length"

ATTACH_JS = r"""JSON.stringify((() => {
  const parts = (window.__up && window.__up.parts) || [];
  const b64 = parts.join('');
  if (!b64) return {ok:false, why:'no data'};
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i=0;i<bin.length;i++) bytes[i]=bin.charCodeAt(i);
  const f = new File([bytes], "image.jpg", {type: "image/jpeg"});
  const dt = new DataTransfer(); dt.items.add(f);
  const inputs = [...document.querySelectorAll('input[type="file"]')];
  if (!inputs.length) return {ok:false, why:'no file input'};
  let done = 0;
  for (const inp of inputs) {
    try { inp.files = dt.files; inp.dispatchEvent(new Event('change', {bubbles:true})); done++; } catch(e){}
  }
  return {ok: done>0, inputs: inputs.length, bytes: bytes.length};
})())"""

CHECK_JS = r"""JSON.stringify((() => {
  const modal = document.querySelector('[role="dialog"], [aria-labelledby]') || document;
  const imgs = [...modal.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:') || (i.src||'').includes('pbs.twimg.com/media'));
  const bar = modal.querySelector('[role="progressbar"]');
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  return {blob: imgs.length, progress: !!bar, editor: !!ed, txt: ed ? ed.innerText.slice(0,40) : ''};
})())"""

async def main():
    pairs = json.load(open(sys.argv[1]))
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/compose/post"}))
            pid = np.get("page_id") or np.get("id")
            print("page:", pid)
            await asyncio.sleep(5)
            print("drafts open:", await ev(s, pid, OPEN_DRAFTS))
            await asyncio.sleep(2.5)
            for it in pairs:
                snip, media = it["snippet"], it["media"]
                # click the draft item whose text matches
                click_js = r"""JSON.stringify((() => {
                  const items = [...document.querySelectorAll('[data-testid="unsentTweet"]')];
                  const el = items.find(e => (e.innerText||'').includes(%s));
                  if (!el) return {ok:false, n: items.length};
                  el.click(); return {ok:true};
                })())""" % json.dumps(snip)
                res = await ev(s, pid, click_js)
                print("open draft:", res)
                await asyncio.sleep(2.5)
                # push base64 in chunks (~120KB each)
                b64 = base64.b64encode(open(media, "rb").read()).decode()
                chunks = [b64[i:i+120000] for i in range(0, len(b64), 120000)]
                for ch in chunks:
                    await ev(s, pid, PUSH_CHUNK % json.dumps(ch))
                at = await ev(s, pid, ATTACH_JS)
                print("attach:", at)
                ok = False
                for _ in range(25):
                    st = await ev(s, pid, CHECK_JS)
                    if isinstance(st, dict) and (st.get("blob") or 0) > 0:
                        ok = True; break
                    await asyncio.sleep(1.2)
                print("preview:", st if isinstance(st, dict) else st)
                if not ok:
                    print("FAIL attach:", snip[:40]); continue
                await asyncio.sleep(7)   # settle: let X finish processing the media
                # close -> save
                close_js = r"""JSON.stringify((() => { const c = document.querySelector('[data-testid="app-bar-close"]'); if (c){c.click(); return {ok:true};} return {ok:false}; })())"""
                await ev(s, pid, close_js)
                await asyncio.sleep(1.5)
                conf_js = r"""JSON.stringify((() => {
                  const c = document.querySelector('[data-testid="confirmationSheetConfirm"]');
                  if (c) { c.click(); return {via:'sheet'}; }
                  const b = [...document.querySelectorAll('[role="button"],button')].find(x => /^save$/i.test((x.innerText||'').trim()));
                  if (b) { b.click(); return {via:'save-btn'}; }
                  return {via:'none'};
                })())"""
                print("save:", await ev(s, pid, conf_js))
                await asyncio.sleep(2)
                # cleanup state + reopen drafts for next
                await ev(s, pid, "window.__up = null; 1")
                await ev(s, pid, OPEN_DRAFTS)
                await asyncio.sleep(2)
            await call(s, "cloak_close_page", {"page_id": pid})
            print("done")

asyncio.run(main())
