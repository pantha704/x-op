#!/usr/bin/env python3
"""Aesthetic publisher: post an image (art / scenery / aesthetic) as its own post.

Owner spec (2026-09-24): image posts - no caption by default, only the owner
credit as text (@handle when on X, else "Platform: username"); a short line
(never an essay) only when there is something genuinely about the image.

Usage: aesthetic_publish.py <image_path> ["<text>"] [--dry]

Flow: compose tab -> optional native-typed text -> image via DataTransfer
injection (same proven technique as post_draft.py) -> wait for preview ->
Post -> toast verify -> permalink capture. Logs to logs/aesthetic-*.jsonl.
--dry stops before clicking Post (verifies everything else).
"""
import asyncio
import base64
import json
import os
import random
import sys
import time

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


TYPE_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  ed.focus();
  if ((ed.innerText || '').length > 0) {
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    ed.focus();
  }
  document.execCommand('insertText', false, __TEXT__);
  return {ok:true, len: (ed.innerText || '').length, text: (ed.innerText || '').slice(0,80)};
})())"""

POST_JS = r"""JSON.stringify((() => {
  const b = document.querySelector('[data-testid="tweetButton"]') || document.querySelector('[data-testid="tweetButtonInline"]');
  if (!b) return {ok:false, why:'no button'};
  if (b.getAttribute('aria-disabled') === 'true') return {ok:false, why:'disabled'};
  b.click(); return {ok:true};
})())"""

TOAST_JS = r"""JSON.stringify((() => {
  const toast = document.querySelector('[data-testid="toast"]');
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  const prog = document.querySelector('[data-testid="progressBar"]');
  return { toast: toast ? toast.innerText.slice(0,80) : null, editor: !!ed, prog: !!prog };
})())"""

PROFILE_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const out = [];
  for (const a of arts.slice(0, 8)) {
    const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
    const tx = a.querySelector('[data-testid="tweetText"]');
    out.push({url: link ? link.href.split('?')[0] : null, text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,90) : ''});
  }
  return out;
})())"""


async def main():
    argv = sys.argv[1:]
    dry = "--dry" in argv
    args = [a for a in argv if a != "--dry"]
    if not args:
        print("usage: aesthetic_publish.py <image_path> [\"<text>\"] [--dry]")
        sys.exit(2)
    img_path = args[0]
    text = args[1] if len(args) > 1 else ""
    if not os.path.exists(img_path):
        print("ERR: image not found", img_path)
        sys.exit(2)
    sz = os.path.getsize(img_path)
    print(f"image: {img_path} ({sz/1024:.0f} KB) | text: {text!r}")

    async with streamable_http_client(URL) as ctx:
        async with ClientSession(ctx[0], ctx[1]) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/compose/post"}))
            pid = np.get("page_id") or np.get("id")
            await asyncio.sleep(4)

            if text:
                t = await ev(s, pid, TYPE_JS.replace("__TEXT__", json.dumps(text)))
                if not (isinstance(t, dict) and t.get("ok")):
                    # fallback: JS insert direct
                    await ev(s, pid, TYPE_JS.replace("__TEXT__", json.dumps(text)))
                print("type:", json.dumps(t)[:110])
                await asyncio.sleep(1.2)

            # image attach: chunked base64 -> File -> hidden file input
            b64 = base64.b64encode(open(img_path, "rb").read()).decode()
            await call(s, "cloak_evaluate", {"page_id": pid, "expression": "window.__up={parts:[]};1"})
            for i in range(0, len(b64), 120000):
                await call(s, "cloak_evaluate", {"page_id": pid,
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
            at = await ev(s, pid, attach)
            print("attach:", json.dumps(at)[:110])
            if not (isinstance(at, dict) and at.get("ok")):
                print("ERR: attach failed")
                await call(s, "cloak_close_page", {"page_id": pid})
                sys.exit(4)

            # wait for the image preview (blob img in the dialog)
            ready = False
            for _ in range(25):
                chk = await ev(s, pid, r"""JSON.stringify((() => { const m = document.querySelector('[role="dialog"]') || document; const blobs = [...m.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:')).length; const prog = !!document.querySelector('[data-testid="progressBar"]'); return {blob: blobs, prog}; })())""")
                if isinstance(chk, dict) and chk.get("blob") and not chk.get("prog"):
                    ready = True
                    break
                await asyncio.sleep(1.5)
            print("preview ready:", ready)
            if not ready:
                # give it a last chance even with progress indicator
                await asyncio.sleep(6)

            if dry:
                print("DRY - preview attached, not posting")
                await call(s, "cloak_close_page", {"page_id": pid})
                return

            posted = False
            for _ in range(3):
                po = await ev(s, pid, POST_JS)
                if isinstance(po, dict) and po.get("ok"):
                    posted = True
                    break
                await asyncio.sleep(2.5)
            if not posted:
                print("ERR: post button stuck")
                await call(s, "cloak_close_page", {"page_id": pid})
                sys.exit(5)
            outcome = "unverified"
            for _ in range(20):
                st = await ev(s, pid, TOAST_JS)
                if isinstance(st, dict) and (st.get("toast") or not st.get("editor")):
                    outcome = "hit"
                    break
                await asyncio.sleep(1.5)
            permalink = None
            if outcome == "hit":
                try:
                    await call(s, "cloak_navigate", {"page_id": pid, "url": "https://x.com/your_handle"})
                    await asyncio.sleep(5)
                    rows = await ev(s, pid, PROFILE_JS)
                    if isinstance(rows, list) and rows:
                        permalink = rows[0].get("url")
                except Exception as e:
                    print("permalink fail:", str(e)[:80])
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass

    os.makedirs("logs", exist_ok=True)
    entry = {"ts": time.strftime("%H:%M:%S"), "date": time.strftime("%Y-%m-%d"), "type": "aesthetic",
             "image": img_path, "image_bytes": sz, "text": text, "outcome": outcome, "permalink": permalink}
    with open("logs/aesthetic-%s.jsonl" % time.strftime("%Y%m%d"), "a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("OUTCOME:", outcome, "| permalink:", permalink)


if __name__ == "__main__":
    asyncio.run(main())
