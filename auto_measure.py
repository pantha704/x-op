#!/usr/bin/env python3
"""Screen our replies timeline, record like counts -> logs/measures-YYYY-MM-DD.jsonl
Runs via cron 3x/day + once for +24h approvals. Read-only."""
import asyncio, json, time, os, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

READ = """(() => {
  const out = [];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
    const handle = a.querySelector('[data-testid="User-Name"]')?.innerText || '';
    const text = (a.querySelector('[data-testid="tweetText"]')?.innerText || '').slice(0, 140);
    const group = a.querySelector('[role="group"]');
    const likes = group ? (Array.from(group.querySelectorAll('[aria-label]')).map(x=>x.getAttribute('aria-label')).find(l=>/like/i.test(l)) || '') : '';
    const t = a.querySelector('time')?.getAttribute('datetime') || '';
    const link = Array.from(a.querySelectorAll('a[href*="/status/"]')).map(x=>x.getAttribute('href')).find(h=>h && h.includes('your_handle'));
    out.push({handle, text, likes, time: t, link});
  });
  return JSON.stringify(out);
})()"""

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def main():
    async with streamable_http_client("http://127.0.0.1:8932/mcp") as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/your_handle/with_replies"}))
            page = np.get("page_id") or np.get("id")
            await asyncio.sleep(3)
            await asyncio.sleep(4)
            rows = []
            for _ in range(3):
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ})
                try: rows += json.loads(json.loads(r3).get("result", "[]"))
                except Exception: pass
                await call(s, "cloak_evaluate", {"page_id": page, "expression": "window.scrollBy(0, 1800); 'ok'"})
                await asyncio.sleep(1.2)
            day = time.strftime("%Y-%m-%d")
            fn = f"/home/ubuntu/x-op/logs/measures-{day}.jsonl"
            with open(fn, "a") as f:
                for row in rows:
                    if row.get("link"):
                        row["measuredAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"appended {len(rows)} rows -> {fn}")
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass

asyncio.run(main())
