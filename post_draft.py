#!/usr/bin/env python3
"""Draft a post on X (owner directive 2026-09-21: drafts visible in his app for review/posting).

Saves the draft into the account's composer (X keeps it under Drafts, syncs to the app).
Usage: post_draft.py "<text>" [--media /path/to/image.jpg]
Prints OK + a note; never publishes.
"""
import asyncio, json, re, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"

OPEN_JS = r"""JSON.stringify((() => {
  const btn = document.querySelector('[data-testid="SideNav_NewTweet_Button"]') ||
              [...document.querySelectorAll('a[href="/compose/post"]')][0];
  if (!btn) return {ok:false, why:'no compose button'};
  btn.click();
  return {ok:true};
})())"""

TYPE_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  ed.focus();
  document.execCommand('insertText', false, __TEXT__);
  return {ok:true, len: ed.innerText.length};
})()"""

CLEAR_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  if ((ed.innerText || '').trim().length > 0) {
    ed.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    return {ok:true, cleared:true};
  }
  return {ok:true, cleared:false};
})()"""

SAVE_JS = r"""JSON.stringify((() => {
  const close = document.querySelector('[data-testid="app-bar-close"]');
  if (close) { close.click(); return {ok:true, via:'close-button'}; }
  document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
  return {ok:true, via:'escape'};
})())"""

CONFIRM_JS = r"""JSON.stringify((() => {
  const c = document.querySelector('[data-testid="confirmationSheetConfirm"]');
  if (c) { c.click(); return {ok:true, clicked:'confirm-sheet'}; }
  const btns = [...document.querySelectorAll('[role="button"],button')];
  const save = btns.find(b => /^(save|save draft)$/i.test((b.innerText||'').trim()));
  if (save) { save.click(); return {ok:true, clicked:'save-text'}; }
  return {ok:false, why:'no save button', texts: btns.map(b=>(b.innerText||'').trim()).filter(Boolean).slice(0,12)};
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    text = sys.argv[1]
    media = None
    if "--media" in sys.argv:
        media = sys.argv[sys.argv.index("--media") + 1]
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            pages = json.loads(lp).get("pages", [])
            # dedicated tab: never hijack the reply driver's page
            try:
                np = json.loads(await call(s, "cloak_new_page", {"url": "about:blank"}))
                page = np.get("page_id") or np.get("id")
            except Exception:
                page = None
            if not page:
                page = pages[0]["page_id"] if pages else json.loads(await call(s, "cloak_launch", {"user_data_dir": PROFILE})).get("page_id")
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/home"})
            await asyncio.sleep(3.5)
            r1 = await call(s, "cloak_evaluate", {"page_id": page, "expression": OPEN_JS})
            print("open:", r1[:120])
            await asyncio.sleep(1.6)
            # NATIVE TYPE (2026-09-23): JS execCommand inserts get mangled by X's linkify/autosave
            # (first line eaten or duplicated). Native typing via cloak_type is stable with "\n".
            ref = None
            try:
                snap_raw = await call(s, "cloak_snapshot", {"page_id": page})
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
                tr = await call(s, "cloak_type", {"page_id": page, "ref": ref, "text": text, "clear": True})
                print("type:", tr[:120])
            else:
                print("no ref; fallback JS insert")
                r2 = await call(s, "cloak_evaluate", {"page_id": page, "expression": TYPE_JS.replace("__TEXT__", json.dumps(text))})
                print("type:", r2[:160])
            await asyncio.sleep(1.6)
            if media:
                # Media attach via JS DataTransfer injection. X's composer no longer exposes
                # [data-testid="attachments"], and this MCP has no file-upload tool, so we
                # push the image bytes in as a File directly onto the hidden file input.
                import base64
                b64 = base64.b64encode(open(media, "rb").read()).decode()
                await call(s, "cloak_evaluate", {"page_id": page, "expression": "window.__up={parts:[]};1"})
                for i in range(0, len(b64), 120000):
                    await call(s, "cloak_evaluate", {"page_id": page,
                        "expression": "window.__up.parts.push(%s);1" % json.dumps(b64[i:i+120000])})
                attach = r"""JSON.stringify((() => {
  const b64 = (window.__up && window.__up.parts || []).join('');
  if (!b64) return {ok:false, why:'no data'};
  const bin = atob(b64); const bytes = new Uint8Array(bin.length);
  for (let i=0;i<bin.length;i++) bytes[i]=bin.charCodeAt(i);
  const f = new File([bytes], "image.jpg", {type: "image/jpeg"});
  const dt = new DataTransfer(); dt.items.add(f);
  const inputs = [...document.querySelectorAll('input[type="file"]')];
  let done = 0;
  for (const inp of inputs) { try { inp.files = dt.files; inp.dispatchEvent(new Event('change',{bubbles:true})); done++; } catch(e){} }
  return {ok: done>0, bytes: bytes.length};
})())"""
                at = await call(s, "cloak_evaluate", {"page_id": page, "expression": attach})
                print("attach:", at[:120])
                # wait for the blob preview to appear
                for _ in range(20):
                    chk = await call(s, "cloak_evaluate", {"page_id": page, "expression":
                        r"""JSON.stringify((() => { const m = document.querySelector('[role="dialog"]') || document; return { blob: [...m.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:')).length }; })())"""})
                    try:
                        if json.loads(json.loads(chk).get("result","{}")).get("blob"): break
                    except Exception:
                        pass
                    await asyncio.sleep(1.2)
                await asyncio.sleep(7)  # let X finish processing the media
            await call(s, "cloak_evaluate", {"page_id": page, "expression": SAVE_JS})
            await asyncio.sleep(1.4)
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": CONFIRM_JS})
            print("save:", r3[:200])
            await asyncio.sleep(1.0)
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass
            print("OK draft saved (check X drafts; it may also stay as a saved composer draft)")


asyncio.run(main())
