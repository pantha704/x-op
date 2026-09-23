#!/usr/bin/env python3
"""Stats pass: our recent replies with live like/view counts + profile counters."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const rows = arts.slice(0, 20).map(a => {
    const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
    const tx = a.querySelector('[data-testid="tweetText"]');
    const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
    let likes = null, views = null, reps = null;
    for (const l of labels) {
      let m = l.match(/^([\d,]+)\s+likes?/i); if (m) likes = parseInt(m[1].replace(/,/g, ''));
      m = l.match(/^([\d,]+)\s+repl/i); if (m) reps = parseInt(m[1].replace(/,/g, ''));
    }
    const vt = (a.innerText.match(/([\d.,]+[KM]?)\s+Views/i) || [])[1] || null;
    return {url: tl ? tl.href.split('?')[0] : null, text: tx ? tx.innerText.replace(/\n/g, ' ').slice(0, 90) : '', likes, reps, views: vt};
  }).filter(x => x.url);
  const stats = [...document.querySelectorAll('a[href*="/followers"], a[href*="/following"]')].map(x => x.getAttribute('href') + ' :: ' + (x.innerText || '').replace(/\n/g,' '));
  return {rows, stats};
})())"""


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
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/search?q=from%3Ayour_handle%20filter%3Areplies&f=live"})
            await asyncio.sleep(8.0)
            d = await ev(s, page, JS)
            print(json.dumps(d, ensure_ascii=False)[:3500])
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/your_handle"})
            await asyncio.sleep(6.5)
            h = await ev(s, page, r"""JSON.stringify([...document.querySelectorAll('a[href*="followers"], a[href*="following"]')].map(x => x.getAttribute('href') + ' :: ' + (x.innerText||'').replace(/\n/g,' ')))""")
            print('PROFILE:', json.dumps(h, ensure_ascii=False)[:500])

asyncio.run(main())
