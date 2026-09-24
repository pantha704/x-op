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
_DET = None


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


async def attach_tag(s, pid, handle):
    """Tag @handle inside the attached image via the composer's Tag people flow.
    Returns tagged | tagged-unverified | untaggable | notfound | no-ui | failed."""
    clicked = await ev(s, pid, r"""JSON.stringify((() => {
  const cands = [...document.querySelectorAll('[aria-label="Tag people"]')];
  for (const el of cands) { const b = el.closest('a') || el.closest('button') || el; if (b && b.offsetParent !== null) { b.click(); return {ok:true}; } }
  return {ok:false};
})())""")
    if not (isinstance(clicked, dict) and clicked.get("ok")):
        return "no-ui"
    await asyncio.sleep(2.5)
    typed = await ev(s, pid, r"""JSON.stringify((() => {
  const inp = document.querySelector('input[data-testid="searchPeople"]');
  if (!inp) return {ok:false, why:'no searchPeople'};
  inp.focus();
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(inp, __H__);
  inp.dispatchEvent(new Event('input', {bubbles:true}));
  return {ok:true};
})())""".replace("__H__", json.dumps(handle)))
    if not (isinstance(typed, dict) and typed.get("ok")):
        return "no-ui"
    await asyncio.sleep(3.5)
    pic = await ev(s, pid, r"""JSON.stringify((() => {
  const want = ('@' + __H__).toLowerCase();
  const rows = [...document.querySelectorAll('[data-testid="typeaheadResult"]')];
  for (const r of rows) {
    const tx = (r.innerText || '').toLowerCase();
    if (tx.includes(want)) {
      if (tx.includes("can't be tagged") || tx.includes("cannot be tagged")) return {status:'untaggable'};
      const btn = r.querySelector('[data-testid="TypeaheadUser"]') || r;
      btn.click();
      return {status:'clicked'};
    }
  }
  return {status:'notfound', n: rows.length};
})())""".replace("__H__", json.dumps(handle)))
    st = pic.get("status") if isinstance(pic, dict) else "failed"
    if st != "clicked":
        await ev(s, pid, r"""JSON.stringify((() => { const b=[...document.querySelectorAll('button, [role="button"], [role="link"]')].find(x=>/close/i.test(x.getAttribute('aria-label')||'')); if(b) b.click(); return {ok:true}; })())""")
        return st
    await asyncio.sleep(1.8)
    done = await ev(s, pid, r"""JSON.stringify((() => {
  const btns = [...document.querySelectorAll('button')].filter(b => b.offsetParent !== null && (b.innerText||'').trim() === 'Done');
  if (btns.length) { btns[btns.length-1].click(); return {ok:true}; }
  return {ok:false};
})())""")
    if not (isinstance(done, dict) and done.get("ok")):
        return "failed"
    await asyncio.sleep(2.0)
    ver = await ev(s, pid, r"""JSON.stringify((() => {
  const d = document.querySelector('[role="dialog"]') || document;
  return { has: (d.innerText || '').toLowerCase().includes(__H__) };
})())""".replace("__H__", json.dumps("@" + handle.lower())))
    return "tagged" if (isinstance(ver, dict) and ver.get("has")) else "tagged-unverified"


async def main():
    argv = sys.argv[1:]
    dry = "--dry" in argv
    no_permalink = "--no-permalink" in argv
    tag_handle = ""
    fallback_text = ""
    src_url = ""
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--dry", "--no-permalink"):
            i += 1
        elif a == "--tag" and i + 1 < len(argv):
            tag_handle = argv[i + 1].lstrip("@"); i += 2
        elif a == "--fallback-text" and i + 1 < len(argv):
            fallback_text = argv[i + 1]; i += 2
        elif a == "--src" and i + 1 < len(argv):
            src_url = argv[i + 1]; i += 2
        else:
            pos.append(a); i += 1
    if not pos:
        print("usage: aesthetic_publish.py <image_path> [\"<text>\"] [--tag @handle] [--fallback-text '<text>'] [--dry]")
        sys.exit(2)
    img_path = pos[0]
    text = pos[1] if len(pos) > 1 else ""
    tag_status = "none"
    if not os.path.exists(img_path):
        print("ERR: image not found", img_path)
        sys.exit(2)
    sz = os.path.getsize(img_path)
    print(f"image: {img_path} ({sz/1024:.0f} KB) | text: {text!r}")

    # --- NSFW HARD GATE (owner directive 2026-09-24; fail closed) ---
    EXPLICIT = {"FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED", "MALE_GENITALIA_EXPOSED",
                "BUTTOCKS_EXPOSED", "ANUS_EXPOSED", "FEMALE_BREAST_EXPOSED_THROUGH_CLOTHING"}
    try:
        global _DET
        if _DET is None:
            from nudenet import NudeDetector
            _DET = NudeDetector()
        sres = _DET.detect(img_path)
        if isinstance(sres, dict):
            sres = [sres]
        hits = [d for d in sres if d.get("class") in EXPLICIT and d.get("score", 0) > 0.30]
        if hits:
            print("SCREEN BLOCKED: NSFW detected", [(d["class"], round(d["score"], 2)) for d in hits])
            sys.exit(7)
        print("screen: clean")
    except SystemExit:
        raise
    except Exception as e:
        print("SCREEN ERROR (fail closed):", str(e)[:90])
        sys.exit(8)

    # --- VISION LABEL GATE (owner 2026-09-24: vision names + NSFW review) ---
    LABELS = "worker/image-labels.json"
    _label = None
    if os.path.exists(LABELS):
        try:
            _lb = json.load(open(LABELS))
            _label = _lb.get(os.path.basename(img_path))
        except Exception:
            _label = None
    if _label:
        if _label.get("nsfw"):
            print("SCREEN BLOCKED (vision):", (_label.get("reason") or "labeled NSFW")[:70])
            sys.exit(7)
        if not text and _label.get("title"):
            text = _label["title"]
            print("label title:", text)

    # --- DUPLICATE HARD GATE (owner: never post the same image twice, ever) ---
    import hashlib
    img_hash = hashlib.sha256(open(img_path, "rb").read()).hexdigest()
    REG = "worker/aesthetic-posted.jsonl"
    if os.path.exists(REG):
        try:
            for line in open(REG):
                if line.strip() and json.loads(line).get("sha256") == img_hash:
                    print("DUPLICATE BLOCKED: this image was already posted (hash match)")
                    sys.exit(9)
        except SystemExit:
            raise
        except Exception:
            pass

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

            if tag_handle:
                tag_status = await attach_tag(s, pid, tag_handle)
                print("tag:", tag_status)
                if tag_status in ("untaggable", "notfound", "no-ui", "failed") and fallback_text and not text:
                    text = fallback_text
                    t2 = await ev(s, pid, TYPE_JS.replace("__TEXT__", json.dumps(text)))
                    print("fallback text:", json.dumps(t2)[:90])
                    await asyncio.sleep(1.0)

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
            if outcome == "hit" and not no_permalink:
                try:
                    await call(s, "cloak_navigate", {"page_id": pid, "url": "https://x.com/your_handle"})
                    await asyncio.sleep(4)
                    await call(s, "cloak_navigate", {"page_id": pid, "url": "https://x.com/your_handle"})  # hard reload: profile is stale right after posting
                    await asyncio.sleep(7)
                    rows = await ev(s, pid, PROFILE_JS)
                    if isinstance(rows, list) and rows:
                        permalink = rows[0].get("url")
                except Exception as e:
                    print("permalink fail:", str(e)[:80])
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass

    if outcome == "hit":
        with open("worker/aesthetic-posted.jsonl", "a") as fh:
            fh.write(json.dumps({"sha256": img_hash, "file": img_path, "ts": time.strftime("%H:%M:%S"), "src": src_url}) + "\n")

    os.makedirs("logs", exist_ok=True)
    entry = {"ts": time.strftime("%H:%M:%S"), "date": time.strftime("%Y-%m-%d"), "type": "aesthetic",
             "image": img_path, "image_bytes": sz, "text": text, "outcome": outcome, "permalink": permalink,
             "tag": tag_handle, "tag_status": tag_status}
    with open("logs/aesthetic-%s.jsonl" % time.strftime("%Y%m%d"), "a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("OUTCOME:", outcome, "| permalink:", permalink)


if __name__ == "__main__":
    asyncio.run(main())
