#!/usr/bin/env python3
"""Measure our thighs reply + caseoh context (one browser pass)."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

LIST_JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 25).map(a => {
  const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
  const tx = a.querySelector('[data-testid="tweetText"]');
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
  let likes = null, reps = null;
  for (const l of labels) {
    let m = l.match(/^([\d,]+)\s+likes?/i); if (m) likes = parseInt(m[1].replace(/,/g, ''));
    m = l.match(/^([\d,]+)\s+repl/i); if (m) reps = parseInt(m[1].replace(/,/g, ''));
  }
  return {url: tl ? tl.href.split('?')[0] : null, text: tx ? tx.innerText.replace(/\n/g, ' ') : '', likes, reps};
}).filter(x => x.url))"""

JOBS = [
    ("quotes", "https://x.com/caseohOOC/status/2101902335828218236/quotes", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, items: arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), t: (t ? t.innerText.slice(0, 320) : '')};
  })};
})())"""),
    ("search_rewind", "https://x.com/search?q=%22rewind%2099%22&src=typed_query&f=live", r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return {n: arts.length, items: arts.slice(0, 12).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), t: (t ? t.innerText.slice(0, 320) : '')};
  })};
})())"""),
]


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, page, js):
    r = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
    try:
        return json.loads(json.loads(r).get("result", "null") or "null")
    except Exception:
        return {"raw": r[:300]}


async def main():
    out = {}
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            # 1) measure our thighs reply
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/your_handle/with_replies"})
            await asyncio.sleep(5.0)
            rows = await ev(s, page, LIST_JS)
            out["with_replies"] = rows
            # 2) caseoh context
            for tag, u, js in JOBS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(6.0)
                out[tag] = await ev(s, page, js)
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/measure-thighs-e4.json", "w"), ensure_ascii=False, indent=1)
    print("== OUR RECENT REPLIES (with_replies) ==")
    n = 0
    for row in (out.get("with_replies") or []):
        n += 1
        print(f'  likes={row.get("likes")} reps={row.get("reps")} | {row.get("text","")[:90]}')
        if n >= 12:
            break
    for tag in ("quotes", "search_rewind"):
        print("=" * 70)
        print("##", tag)
        print(json.dumps(out.get(tag), ensure_ascii=False)[:2200])

asyncio.run(main())
