#!/usr/bin/env python3
"""Ctx fetch for compose-e slice (6 candidates). Reads via op MCP (logged-in browser)."""
import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

TARGETS = [
    ("shinobi602", "https://x.com/shinobi602/status/2101931539558711688", True),
    ("JonnyBlox", "https://x.com/JonnyBlox/status/2101930246190633396", True),
    ("hroptatyrdaily", "https://x.com/hroptatyrdaily/status/2101912178882396614", True),
    ("LittleRedhoodd", "https://x.com/LittleRedhoodd/status/2101929876160917670", True),
    ("roshidere", "https://x.com/roshidere/status/2101945284804882635", True),
    ("caseohOOC", "https://x.com/caseohOOC/status/2101902335828218236", True),
]

READ_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const main = arts[0];
  if (!main) return {err: 'no article', body: document.body.innerText.slice(0, 400)};
  const mt = main.querySelector('[data-testid="tweetText"]');
  const who = main.querySelector('[data-testid="User-Name"]');
  const imgs = [...main.querySelectorAll('img')].map(i => i.src).filter(s => s.includes('pbs.twimg.com/media') || s.includes('video_thumb'));
  const vids = [...main.querySelectorAll('video')].map(v => ({src: v.src, poster: v.poster}));
  const plays = main.querySelector('[data-testid="playButton"]') ? 1 : 0;
  const replies = arts.slice(1, 9).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: (h ? h.innerText.split('\n')[0] : ''), txt: (t ? t.innerText.slice(0, 400) : '')};
  });
  return {
    url: location.href,
    mainText: mt ? mt.innerText : '',
    mainInner: main.innerText.slice(0, 1400),
    who: who ? who.innerText.slice(0, 80) : '',
    imgs: imgs, vids: vids, plays: plays,
    nArticles: arts.length,
    replies: replies
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
        return {"raw": r[:400]}


async def main():
    out = {}
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            tl = await s.list_tools()
            names = [t.name for t in tl.tools]
            print("TOOLS:", names)
            shot = [n for n in names if "screenshot" in n.lower()]
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for tag, u, want_shot in TARGETS:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(5.0)
                d = await ev(s, page, READ_JS)
                d = d if isinstance(d, dict) else {"err": str(d)[:200]}
                if want_shot and shot:
                    try:
                        res = await call(s, shot[0], {"page_id": page})
                        d["shot"] = res[:400]
                    except Exception as e:
                        d["shot_err"] = str(e)[:200]
                out[tag] = d
                await asyncio.sleep(1.0)
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-e-out.json", "w"), ensure_ascii=False, indent=1)
    # compact print
    for tag, d in out.items():
        print("=" * 70)
        print("##", tag)
        print("WHO:", (d.get("who") or "").replace("\n", " | ")[:90])
        print("TXT:", (d.get("mainText") or d.get("err") or "").replace("\n", " / ")[:700])
        print("NART:", d.get("nArticles"), "PLAYS:", d.get("plays"))
        print("IMGS:", json.dumps(d.get("imgs") or [])[:300])
        print("VIDS:", json.dumps(d.get("vids") or [])[:300])
        print("SHOT:", (d.get("shot") or d.get("shot_err") or "")[:220])
        for rep in (d.get("replies") or [])[:8]:
            print("  R:", rep.get("who", "")[:40], "|", (rep.get("txt") or "").replace("\n", " / ")[:200])

asyncio.run(main())
