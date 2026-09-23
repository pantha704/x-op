#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
TARGETS = [
    ("yy624022", "https://x.com/yy624022/status/2101925932193939910"),
    ("TheGachaAniGuy", "https://x.com/TheGachaAniGuy/status/2101908495956418753"),
    ("USA37107692", "https://x.com/USA37107692/status/2101907624744599995"),
    ("comfypill", "https://x.com/comfypill/status/2101898496831881579"),
]

READ_JS = r"""JSON.stringify((() => {
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return {err: 'no article'};
  const tx = a.querySelector('[data-testid="tweetText"]');
  const un = a.querySelector('[data-testid="User-Name"]');
  const imgs = [...a.querySelectorAll('img')].map(i => ({src: (i.src||'').slice(0,200), alt: (i.alt||'').slice(0,150)})).filter(i => i.src.includes('media') || i.src.includes('thumb') || i.src.includes('profile_images') === false);
  const vids = [...a.querySelectorAll('video')].map(v => (v.poster||'').slice(0,200));
  return {
    who: un ? un.innerText.replace(/\n/g,' | ').slice(0,80) : '',
    text: tx ? tx.innerText : '',
    truncated: !!a.querySelector('[data-testid="tweet-text-show-more-link"]'),
    imgs: imgs,
    vids: vids,
    articleText: a.innerText.slice(0, 1600)
  };
})())"""

SHOWMORE_JS = r"""JSON.stringify((() => {
  const l = document.querySelector('[data-testid="tweet-text-show-more-link"]');
  if (l) { l.click(); return 'clicked'; }
  return 'none';
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
            for tag, u in TARGETS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(4.5)
                r1 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                try:
                    d = json.loads(json.loads(r1).get("result", "null") or "null")
                except Exception:
                    d = {"err": "parse", "raw": r1[:400]}
                if d and d.get("truncated"):
                    await call(s, "cloak_evaluate", {"page_id": page, "expression": SHOWMORE_JS})
                    await asyncio.sleep(1.5)
                    r2 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                    try:
                        d2 = json.loads(json.loads(r2).get("result", "null") or "null")
                        if d2:
                            d = d2
                    except Exception:
                        pass
                try:
                    shot = await call(s, "cloak_screenshot", {"page_id": page})
                    d["screenshot"] = shot[:300]
                except Exception as e:
                    d["screenshot"] = "ERR " + str(e)[:120]
                out[tag] = d
                print("=" * 70)
                print("HANDLE:", tag, "URL:", u)
                print(json.dumps(d, indent=1)[:2500])
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-c-media.json", "w"), indent=1)

asyncio.run(main())
