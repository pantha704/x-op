#!/usr/bin/env python3
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

PAGES = [
    ("yy_profile_top", "https://x.com/yy624022"),
]

READ_JS = r"""JSON.stringify((() => {
  // profile header area
  const bio = document.querySelector('[data-testid="UserDescription"]');
  const name = document.querySelector('[data-testid="UserName"]');
  const stats = document.querySelector('[data-testid="UserName"]') ? '' : '';
  // pinned or first post detail
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const posts = arts.slice(0, 8).map(a => {
    const t = a.querySelector('[data-testid="tweetText"]');
    const vids = [...a.querySelectorAll('video')].length;
    const imgs = [...a.querySelectorAll('img')].filter(i => i.src.includes('media')).length;
    const time = a.querySelector('time') ? a.querySelector('time').getAttribute('datetime') : '';
    const social = a.innerText.split('\n').slice(-3).join(' ');
    return {txt: t ? t.innerText.slice(0,200) : '', vids, imgs, time, social: social.slice(0,120)};
  });
  return {
    name: name ? name.innerText.replace(/\n/g,' | ') : '',
    bio: bio ? bio.innerText : '',
    posts
  };
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for tag, u in PAGES:
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(5.0)
                r1 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                try:
                    d = json.loads(json.loads(r1).get("result", "null") or "null")
                except Exception:
                    d = {"raw": r1[:400]}
                print("=" * 70)
                print("PAGE:", tag)
                print(json.dumps(d, indent=1)[:3000])

asyncio.run(main())
