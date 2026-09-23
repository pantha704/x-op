#!/usr/bin/env python3
"""Conversation farm: find replies-back on our recent replies, for the worker to answer.

For our reply permalinks (ledger: known repliesBack>0 first, then newest 12h), opens
its own tab and extracts the first 1-2 reply items after the focal tweet
(handle, text, permalink). Writes worker/conversations.json.

- Skips replyUrls already in worker/conversations_handled.json.
- Read-only except the output file. Own tab - safe beside live waves.
- Caps: scan at most 22 threads, stop at 8 found.
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
X = "/home/ubuntu/x-op"
LEDGER = "/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json"
OUT = os.path.join(X, "worker", "conversations.json")
HANDLED = os.path.join(X, "worker", "conversations_handled.json")
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"
MAX_SCAN = 22
MAX_FOUND = 8

REPLIES_JS = r"""JSON.stringify((() => {
  const ID = "__ID__";
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  let fi = arts.findIndex(x => x.querySelector('a[href*="/status/' + ID + '"]'));
  if (fi < 0) return [];
  const out = [];
  for (let i = fi + 1; i < arts.length && out.length < 2; i++) {
    const a = arts[i];
    const t = a.querySelector('time');
    if (!t) continue;
    const link = t.closest('a');
    const url = link ? link.href.split('?')[0] : null;
    if (!url || url.includes('/' + ID)) continue;
    const h = [...a.querySelectorAll('a[href^="/"]')]
      .map(x => x.getAttribute('href'))
      .find(x => /^\/[A-Za-z0-9_]{2,20}$/.test(x));
    const handle = h ? h.slice(1) : '';
    if (handle.toLowerCase() === 'your_handle') continue;
    const tx = a.querySelector('[data-testid="tweetText"]');
    const text = tx ? tx.innerText.replace(/\n/g, ' ').slice(0, 280) : '';
    if (!text) continue;
    out.push({ handle, url, text });
  }
  return out;
})())"""

PROFILE_JS = r"""JSON.stringify((() => {
  return [...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 14).map(a => {
    const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
    const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
    let replies = null;
    for (const l of labels) { const m = l.match(/^([\d,]+)\s+repl/i); if (m) replies = parseInt(m[1].replace(/,/g, '')); }
    const tx = a.querySelector('[data-testid="tweetText"]');
    return { url: tl ? tl.href.split('?')[0] : null, replies, text: tx ? tx.innerText.replace(/\n/g, ' ').slice(0, 90) : '' };
  }).filter(x => x.url && x.url.includes('/your_handle/status/'));
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


def load_candidates():
    led = json.load(open(LEDGER))
    entries = led if isinstance(led, list) else led.get("entries", [])
    handled = set()
    if os.path.exists(HANDLED):
        try:
            handled = set(json.load(open(HANDLED)))
        except Exception:
            handled = set()
    now = datetime.now(timezone.utc)
    known, recent = [], []
    for e in entries:
        u = e.get("url") or ""
        if "/your_handle/status/" not in u:
            continue
        if u in handled:
            continue
        ts = e.get("firedAt") or ""
        try:
            a = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if a.tzinfo is None:
                a = a.replace(tzinfo=timezone.utc)
            age_h = (now - a).total_seconds() / 3600
        except Exception:
            age_h = 999
        if (e.get("repliesBack") or 0) > 0:
            known.append((age_h, u, e.get("text") or "", "reply"))
        elif age_h <= 12:
            recent.append((age_h, u, e.get("text") or "", "reply"))
    known.sort(key=lambda x: x[0])
    recent.sort(key=lambda x: x[0])
    return known + recent


async def main():
    ledger_cands = load_candidates()
    items = []
    scanned = 0
    post_cands = []
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as session:
            await session.initialize()
            np = json.loads(await call(session, "cloak_new_page", {"url": "https://x.com/home"}))
            page = np.get("page_id") or np.get("id")
            await asyncio.sleep(2)
            # 1) OUR ORIGINAL POSTS with comments (engagement loop on posts)
            try:
                await call(session, "cloak_navigate", {"page_id": page, "url": "https://x.com/your_handle"})
                await asyncio.sleep(4.0)
                raw = await call(session, "cloak_evaluate", {"page_id": page, "expression": PROFILE_JS})
                posts = json.loads(json.loads(raw).get("result", "[]")) if raw.strip().startswith("{") else []
            except Exception as ex:
                posts = []
                print("profile scan error:", str(ex)[:80])
            handled = set()
            if os.path.exists(HANDLED):
                try:
                    handled = set(json.load(open(HANDLED)))
                except Exception:
                    handled = set()
            for p in posts:
                if (p.get("replies") or 0) >= 1 and p.get("url") not in handled:
                    post_cands.append((0.5, p["url"], p.get("text") or "", "post"))
            print(f"profile posts with comments: {len(post_cands)}")
            # 2) scan: posts first, then reply candidates
            cands = (post_cands + ledger_cands)[:MAX_SCAN]
            print(f"candidates to scan: {len(cands)}")
            for age_h, u, ourtext, kind in cands:
                scanned += 1
                sid = u.rstrip("/").split("/")[-1]
                try:
                    await call(session, "cloak_navigate", {"page_id": page, "url": u})
                    await asyncio.sleep(3.2)
                    raw = await call(session, "cloak_evaluate", {"page_id": page, "expression": REPLIES_JS.replace("__ID__", sid)})
                    found = json.loads(json.loads(raw).get("result", "[]")) if raw.strip().startswith("{") else []
                except Exception as ex:
                    found = []
                    print(f"  {sid} scan error: {str(ex)[:80]}")
                for f in found:
                    if f.get("url") and f.get("text"):
                        items.append({"kind": kind, "ourReply": u, "ourText": ourtext[:120], "ageH": round(age_h, 1),
                                      "replyUrl": f["url"], "handle": f.get("handle", ""), "text": f["text"]})
                if found:
                    print(f"  {sid} ({kind}) -> {len(found)} reply(ies)")
                if len(items) >= MAX_FOUND:
                    break
            try:
                await call(session, "cloak_close_page", {"page_id": page})
            except Exception:
                pass
    out = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "scanned": scanned, "items": items}
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"scanned {scanned} threads | found {len(items)} replies-back -> {OUT}")
    for it in items:
        print(f"  @{it['handle']} -> {it['text'][:80]}")


if __name__ == "__main__":
    asyncio.run(main())
