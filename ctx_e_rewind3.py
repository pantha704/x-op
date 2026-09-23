#!/usr/bin/env python3
"""Round 8 (e-slice): Rewind 99 'KITTY' post + caseoh clip replies (full, verbose)."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

POST_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const a = arts[0];
  if (!a) return {err: 'none'};
  const h = a.querySelector('[data-testid="User-Name"]');
  const t = a.querySelector('[data-testid="tweetText"]');
  const time = a.querySelector('time');
  const imgs = [...a.querySelectorAll('img')].map(i => ({src: i.src.slice(0, 90), alt: i.getAttribute('alt')})).slice(0, 6);
  return {
    who: h ? h.innerText : '', time: time ? time.getAttribute('datetime') : '',
    txt: t ? t.innerText : '', full: a.innerText.slice(0, 900), imgs: imgs,
    replies: arts.slice(1, 12).map(x => {const tt = x.querySelector('[data-testid="tweetText"]'); const hh = x.querySelector('[data-testid="User-Name"]'); return {who: hh ? hh.innerText.split('\n')[0] : '', txt: tt ? tt.innerText.replace(/\n/g, ' / ') : ''};})
  };
})())"""

JOBS = [
    ("rewind_kitty", "https://x.com/Rewind99_Game/status/2024334407868219596", POST_JS),
    ("clip_post", "https://x.com/caseohOOC/status/2101902335828218236", POST_JS),
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
            for tag, u, js in JOBS:
                d = None
                for attempt in range(3):
                    await call(s, "cloak_navigate", {"page_id": page, "url": u})
                    await asyncio.sleep(6.5)
                    d = await ev(s, page, js)
                    if isinstance(d, dict) and d.get("who"):
                        break
                    await asyncio.sleep(2.0)
                out[tag] = d if isinstance(d, dict) else {"err": str(d)}
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e-rewind3-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print(json.dumps(d, ensure_ascii=False)[:3200])

asyncio.run(main())
