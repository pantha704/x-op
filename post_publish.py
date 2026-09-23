#!/usr/bin/env python3
"""Publish a post (text + optional image) to the account via the rig MCP.
Unlike post_draft.py this CLICKS POST and verifies the send. Owner-authorized posts only.

Usage: post_publish.py "<text>" [--media /path.jpg]
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

async def main():
    text = sys.argv[1]
    media = sys.argv[sys.argv.index("--media") + 1] if "--media" in sys.argv else None
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            pid = np.get("page_id") or np.get("id")
            print("page:", pid)
            await asyncio.sleep(4)
            # open composer
            op = await ev(s, pid, r"""JSON.stringify((() => {
              const b = document.querySelector('[data-testid="SideNav_NewTweet_Button"]') || document.querySelector('a[href="/compose/post"]');
              if (!b) return {ok:false}; b.click(); return {ok:true};
            })())""")
            print("open:", op)
            await asyncio.sleep(2)
            # type
            tp = await ev(s, pid, r"""JSON.stringify((() => {
              const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
              if (!ed) return {ok:false};
              ed.focus(); document.execCommand('insertText', false, %s);
              return {ok:true, len: ed.innerText.length};
            })())""" % json.dumps(text))
            print("type:", tp)
            await asyncio.sleep(1.2)
            if media:
                b64 = base64.b64encode(open(media, "rb").read()).decode()
                await ev(s, pid, "window.__up={parts:[]};1")
                for i in range(0, len(b64), 120000):
                    await ev(s, pid, "window.__up.parts.push(%s);1" % json.dumps(b64[i:i+120000]))
                at = await ev(s, pid, r"""JSON.stringify((() => {
                  const b64 = (window.__up && window.__up.parts || []).join('');
                  if (!b64) return {ok:false};
                  const bin = atob(b64); const bytes = new Uint8Array(bin.length);
                  for (let i=0;i<bin.length;i++) bytes[i]=bin.charCodeAt(i);
                  const f = new File([bytes], "image.jpg", {type: "image/jpeg"});
                  const dt = new DataTransfer(); dt.items.add(f);
                  let n = 0;
                  for (const inp of document.querySelectorAll('input[type="file"]')) {
                    try { inp.files = dt.files; inp.dispatchEvent(new Event('change',{bubbles:true})); n++; } catch(e){}
                  }
                  return {ok: n>0};
                })())""")
                print("attach:", at)
                for _ in range(25):
                    st = await ev(s, pid, r"""JSON.stringify((() => {
                      const m = document.querySelector('[role="dialog"]') || document;
                      return { blob: [...m.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:')).length };
                    })())""")
                    if isinstance(st, dict) and st.get("blob"):
                        break
                    await asyncio.sleep(1.2)
                await asyncio.sleep(8)
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
            # verify sent: toast or composer closed
            sent = False
            for _ in range(20):
                st = await ev(s, pid, r"""JSON.stringify((() => {
                  const toast = document.querySelector('[data-testid="toast"]');
                  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
                  return { toast: toast ? toast.innerText.slice(0,60) : null, editor: !!ed };
                })())""")
                if isinstance(st, dict) and (st.get("toast") or not st.get("editor")):
                    sent = True; print("verify:", st); break
                await asyncio.sleep(1.5)
            print("SENT" if sent else "UNVERIFIED - check the profile")
            await call(s, "cloak_close_page", {"page_id": pid})

asyncio.run(main())
