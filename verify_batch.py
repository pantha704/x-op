#!/usr/bin/env python3
"""Capture our recent replies from profile/with_replies (URL capture + spot check)."""
import asyncio, json, time
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"

JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 20).map(a => {
  const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
  const tx = a.querySelector('[data-testid="tweetText"]');
  const replyTo = a.innerText.match(/Replying to\s+(@\w+)/);
  return { url: tl ? tl.href.split('?')[0] : null, text: tx ? tx.innerText.replace(/\n/g, ' ') : '', replyTo: replyTo ? replyTo[1] : null };
}).filter(x => x.url))"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            pages = json.loads(lp).get("pages", [])
            page = pages[0]["page_id"] if pages else json.loads(await call(s, "cloak_launch", {"user_data_dir": PROFILE})).get("page_id")
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/your_handle/with_replies"})
            await asyncio.sleep(4)
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
            try:
                rows = json.loads(json.loads(r3).get("result", "[]"))
            except Exception:
                rows = []
            # friction sentinel: scan the page for challenge / verification markers
            fs = await call(s, "cloak_evaluate", {"page_id": page, "expression":
                "(() => { const t = (document.body.innerText || '').toLowerCase();"
                " const marks = ['verify your identity','unusual activity','suspicious','we need to confirm','enter your password','challenge_required','verify it\'s you','locked','temporarily limited'];"
                " const hits = marks.filter(m => t.includes(m)); return JSON.stringify({friction: hits}); })()"})
            try:
                fr = json.loads(json.loads(fs).get("result", "{}"))
            except Exception:
                fr = {}
            if fr.get("friction"):
                print("!! FRICTION MARKERS:", fr["friction"])
            print("our recent replies visible:", len(rows))
            for x in rows[:14]:
                print(" -", x["url"].split("/")[-1], "|", (x["replyTo"] or "-"), "|", x["text"][:80])
            fn = "/home/ubuntu/x-op/logs/verify-%s.json" % time.strftime("%H%M")
            json.dump(rows, open(fn, "w"), indent=1, ensure_ascii=False)
            print("saved:", fn)


asyncio.run(main())
