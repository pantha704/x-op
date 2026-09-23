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
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const main = arts[0];
  if (!main) return {err: 'no article'};
  const mainText = main.querySelector('[data-testid="tweetText"]');
  const replies = arts.slice(1, 8).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const h = a.querySelector('[data-testid="User-Name"]');
    return {who: h ? h.innerText.split('\n')[0] : '', txt: t ? t.innerText.slice(0,300) : ''};
  });
  return {
    mainText: mainText ? mainText.innerText : '',
    mainFull: main.innerText.slice(0, 900),
    replyCount: arts.length,
    replies: replies
  };
})())"""

REPLY_GATE_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const main = arts[0];
  if (!main) return {err: 'no article'};
  const btn = main.querySelector('[data-testid="reply"]');
  const info = {hasBtn: !!btn};
  if (btn) { btn.click(); info.clicked = true; }
  return info;
})())"""

GATE_CHECK_JS = r"""JSON.stringify((() => {
  // composer in a modal?
  const dlg = document.querySelector('[role="dialog"] [data-testid="tweetTextarea_0"]');
  const toast = [...document.querySelectorAll('[role="alert"], [data-testid="toast"]')].map(e => e.innerText).join(' | ');
  const dialogText = (document.querySelector('[role="dialog"]') || {innerText:''}).innerText.slice(0,300);
  return {composerOpen: !!dlg, toast: toast, dialogText: dialogText};
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

                # reply-gate test first (before scrolling, so main article is intact)
                g = await ev(s, page, REPLY_GATE_JS)
                await asyncio.sleep(2.0)
                gc = await ev(s, page, GATE_CHECK_JS)
                await call(s, "cloak_press_key", {"page_id": page, "key": "Escape"})
                await asyncio.sleep(1.0)

                await call(s, "cloak_scroll", {"page_id": page, "direction": "down"})
                await asyncio.sleep(2.5)
                d = await ev(s, page, READ_JS)

                d["gate"] = {"click": g, "after": gc}
                out[tag] = d
                print("=" * 70)
                print("HANDLE:", tag)
                print(json.dumps(d, indent=1)[:3000])
    json.dump(out, open("/home/ubuntu/x-op/targets/ctx-c-threads.json", "w"), indent=1)

asyncio.run(main())
