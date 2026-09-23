#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

PAGES = [
    ("gacha_quotes", "https://x.com/TheGachaAniGuy/status/2101908495956418753/quotes"),
    ("comfy_quotes", "https://x.com/comfypill/status/2101898496831881579/quotes"),
    ("yy_profile", "https://x.com/yy624022"),
]

READ_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  return arts.slice(0, 6).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    const imgs = [...a.querySelectorAll('img')].filter(i => i.src.includes('media')).length;
    return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.slice(0,400) : '', hasMedia: imgs};
  });
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    out = {}
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for tag, u in PAGES:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(4.5)
                r1 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                try:
                    d = json.loads(json.loads(r1).get("result", "null") or "null")
                except Exception:
                    d = {"raw": r1[:300]}
                out[tag] = d
                print("=" * 70)
                print("PAGE:", tag)
                print(json.dumps(d, indent=1)[:2500])
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-c-quotes.json", "w"), indent=1)

asyncio.run(main())
