#!/usr/bin/env python3
"""Check X drafts: count items + media thumbnails. Read-only."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

CHECK = r"""JSON.stringify((() => {
  const items = [...document.querySelectorAll('[data-testid="unsentTweet"]')];
  return items.map(e => {
    const imgs = [...e.querySelectorAll('img')].filter(i => (i.src||'').includes('pbs.twimg.com/media'));
    const txt = (e.innerText||'').replace(/\n+/g,' | ').slice(0,60);
    return {t: txt, media: imgs.length};
  });
})())"""

async def main():
    async with streamable_http_client('http://127.0.0.1:8932/mcp') as ctx:
        async with ClientSession(ctx[0], ctx[1]) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/compose/post"}))
            pid = np.get("page_id") or np.get("id")
            await asyncio.sleep(5)
            await call(s, "cloak_evaluate", {"page_id": pid, "expression":
                r"""JSON.stringify((() => { const c=[...document.querySelectorAll('a,button,div[role="button"],span')].filter(e=>/^drafts$/i.test((e.innerText||'').trim())); if(c.length)c[0].click(); return 1; })())"""})
            await asyncio.sleep(3)
            raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": CHECK})
            try:
                data = json.loads(json.loads(raw).get("result", "[]"))
            except Exception:
                print("RAW:", raw[:300]); data = []
            withmedia = [d for d in data if d.get("media")]
            print(f"total drafts: {len(data)} | with media: {len(withmedia)}")
            for d in data:
                print(f"  [{d.get('media',0)}] {d.get('t','')}")
            await call(s, "cloak_close_page", {"page_id": pid})

asyncio.run(main())
