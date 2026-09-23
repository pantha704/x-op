#!/usr/bin/env python3
"""Wave F (midnight register): context fetch for the picked candidate set."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
HARVEST = "/home/ubuntu/x-op/targets/harvest-20260921-0915.json"

WANT = ["@snuffffles", "@devilmaycra1", "@imagesaicouldnt", "@dimbreath", "@4k_taylorr", "@Dottyyidi"]

data = json.load(open(HARVEST))
jobs = [(r["handle"].lstrip("@"), r["url"]) for r in data if r.get("handle") in WANT]
print("jobs:", jobs)

READ_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const main = arts[0];
  if (!main) return {err: 'no article'};
  const mt = main.querySelector('[data-testid="tweetText"]');
  const who = main.querySelector('[data-testid="User-Name"]');
  const imgs = [...main.querySelectorAll('img')].map(i => ({src: i.src.slice(0, 100), alt: i.getAttribute('alt')})).slice(0, 6);
  const vids = [...main.querySelectorAll('video')].map(v => v.poster).slice(0, 2);
  return {
    author: who ? who.innerText.split('\n')[0] : '',
    mainText: mt ? mt.innerText : '',
    inner: main.innerText.slice(0, 700),
    imgs: imgs, vids: vids, n: arts.length,
    replies: arts.slice(1, 8).map(a => {const t = a.querySelector('[data-testid="tweetText"]'); const h = a.querySelector('[data-testid="User-Name"]'); return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.replace(/\n/g, ' ').slice(0, 220) : ''};})
  };
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, page, js):
    r = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
    try:
        return json.loads(json.loads(r).get("result", "null") or "null")
    except Exception:
        return {"raw": r[:250]}


async def main():
    out = {}
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for tag, u in jobs:
                d = None
                for attempt in range(3):
                    await call(s, "cloak_navigate", {"page_id": page, "url": u})
                    await asyncio.sleep(5.5)
                    d = await ev(s, page, READ_JS)
                    if isinstance(d, dict) and d.get("author"):
                        break
                    await asyncio.sleep(2.0)
                out[tag] = d if isinstance(d, dict) else {"err": str(d)[:150]}
                await asyncio.sleep(0.8)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-wavef-out.json", "w"), ensure_ascii=False, indent=1)
    for tag, d in out.items():
        print("=" * 66)
        print("##", tag, "|", (d.get("author") or d.get("err") or ""))
        print("TXT:", (d.get("mainText") or "").replace("\n", " / ")[:400])
        print("INNER:", (d.get("inner") or "").replace("\n", " / ")[:350])
        print("IMGS:", json.dumps(d.get("imgs") or [])[:260])
        print("VIDS:", json.dumps(d.get("vids") or [])[:150])
        for x in (d.get("replies") or [])[:5]:
            print("  R:", x.get("who", "")[:30], "|", (x.get("txt") or "")[:150])

asyncio.run(main())
