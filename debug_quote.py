#!/usr/bin/env python3
"""Debug: open quote composer and dump its state."""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
TARGET = "https://x.com/theapplehub/status/2102423178442379709"


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, pid, js):
    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": js})
    try:
        return json.loads(json.loads(raw).get("result", "null"))
    except Exception:
        return {"raw": raw[:300]}


DUMP_JS = r"""JSON.stringify((() => {
  const d = document.querySelector('[role="dialog"]');
  const scope = d || document;
  return {
    href: location.href,
    dialog: !!d,
    editor: !!scope.querySelector('[data-testid="tweetTextarea_0"]'),
    text: (scope.innerText || '').slice(0, 300),
    statusLinks: [...scope.querySelectorAll('a')].map(a => a.getAttribute('href')).filter(h => h && h.includes('status')).slice(0, 6),
    imgs: scope.querySelectorAll('img').length,
    blobs: [...scope.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:')).length,
    testids: [...scope.querySelectorAll('[data-testid]')].map(x => x.getAttribute('data-testid')).slice(0, 30),
  };
})())"""


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": TARGET}))
            pid = np.get("page_id") or np.get("id")
            await asyncio.sleep(5)
            print("before:", json.dumps(await ev(s, pid, r"""JSON.stringify({href: location.href, dialog: !!document.querySelector('[role="dialog"]')})""")))
            await ev(s, pid, r"""JSON.stringify((() => { const b = document.querySelector('[data-testid="retweet"]'); b && b.click(); return {ok: !!b}; })())""")
            await asyncio.sleep(1.8)
            mq = await ev(s, pid, r"""JSON.stringify((() => {
              const items = [...document.querySelectorAll('[role="menuitem"]')];
              const q = items.find(x => /quote/i.test(x.innerText || ''));
              if (q) { q.click(); return {ok:true}; }
              return {ok:false, items: items.map(x => (x.innerText||'').slice(0,24))};
            })())""")
            print("menu:", mq)
            await asyncio.sleep(3.5)
            d1 = await ev(s, pid, DUMP_JS)
            print("after-quote:", json.dumps(d1, indent=1)[:1400])
            # type something then re-dump
            await ev(s, pid, r"""JSON.stringify((() => {
              const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
              if (!ed) return {ok:false};
              ed.focus(); document.execCommand('insertText', false, 'debug quote text');
              return {ok:true};
            })())""")
            await asyncio.sleep(2)
            d2 = await ev(s, pid, DUMP_JS)
            print("after-type:", json.dumps(d2, indent=1)[:1400])
            # cancel + close
            await ev(s, pid, r"""JSON.stringify((() => { const c = document.querySelector('[data-testid="app-bar-close"]'); c && c.click(); return {ok: !!c}; })())""")
            await asyncio.sleep(1)
            await call(s, "cloak_close_page", {"page_id": pid})


if __name__ == "__main__":
    asyncio.run(main())
