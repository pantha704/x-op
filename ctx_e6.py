#!/usr/bin/env python3
"""Measure our own recent replies (likes) from with_replies, carefully."""
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
  const who = a.querySelector('[data-testid="User-Name"]');
  return {url: tl ? tl.href.split('?')[0] : null, who: who ? who.innerText.split('\n')[0] : '', text: tx ? tx.innerText.replace(/\n/g, ' ') : '', likes, reps};
}).filter(x => x.url))"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, page, js):
    r = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
    try:
        return json.loads(json.loads(r).get("result", "null") or "null")
    except Exception:
        return {"raw": r[:200]}


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/your_handle/with_replies"})
            await asyncio.sleep(9.0)
            url_now = await ev(s, page, "location.href")
            print("PAGE:", url_now)
            rows = await ev(s, page, LIST_JS)
            json.dump(rows, open("/home/ubuntu/x-op/targets/measure-own-replies.json", "w"), ensure_ascii=False, indent=1)
            for row in (rows or [])[:14]:
                print(f'  likes={row.get("likes")} reps={row.get("reps")} | {row.get("who","")[:20]} | {row.get("text","")[:100]}')

asyncio.run(main())
