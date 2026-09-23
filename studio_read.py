#!/usr/bin/env python3
"""Read analytics + program page + recent original posts (own tab, :8933)."""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8933/mcp"

POSTS_JS = r"""JSON.stringify((() => {
  return [...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 10).map(a => {
    const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
    const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
    let likes = null, replies = null, rts = null, views = null;
    for (const l of labels) {
      let m = l.match(/^([\d,]+)\s+likes?/i); if (m) likes = parseInt(m[1].replace(/,/g, ''));
      m = l.match(/^([\d,]+)\s+repl/i); if (m) replies = parseInt(m[1].replace(/,/g, ''));
      m = l.match(/^([\d,]+)\s+repost/i); if (m) rts = parseInt(m[1].replace(/,/g, ''));
      m = l.match(/^([\d,]+)\s+views?/i); if (m) views = parseInt(m[1].replace(/,/g, ''));
    }
    const tx = a.querySelector('[data-testid="tweetText"]');
    return { url: tl ? tl.href.split('?')[0] : null, likes, replies, rts, views, text: tx ? tx.innerText.replace(/\n/g, ' ').slice(0, 90) : '' };
  }).filter(x => x.url);
})())"""

TEXT_JS = r"""JSON.stringify((() => { const m = document.querySelector('main'); return { text: (m ? m.innerText : document.body.innerText).slice(0, 2500) }; })())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def evaljs(s, page, js):
    raw = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
    try:
        parsed = json.loads(raw)
        inner = parsed.get("result", raw) if isinstance(parsed, dict) else raw
        return json.loads(inner) if isinstance(inner, str) else inner
    except Exception:
        return raw


async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = json.loads(await call(s, "cloak_list_pages", {}))
            page = None
            if lp.get("pages"):
                page = lp["pages"][0].get("page_id") or lp["pages"][0].get("id")
            if not page:
                try:
                    np_ = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
                    page = np_.get("page_id")
                except Exception:
                    page = None
            if not page:
                lr = json.loads(await call(s, "cloak_launch", {"user_data_dir": "/home/ubuntu/.cloakbrowser/profiles/operator2"}))
                page = lr.get("page_id")
                if not page:
                    np_ = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
                    page = np_.get("page_id")
            print("page:", page)
            await asyncio.sleep(3)

            for tag, u, js in [
                ("analytics", "https://x.com/i/account_analytics", TEXT_JS),
                ("program-retry", "https://x.com/i/jf/creators/original", TEXT_JS),
                ("posts", "https://x.com/your_handle", POSTS_JS),
            ]:
                try:
                    await call(s, "cloak_navigate", {"page_id": page, "url": u})
                    await asyncio.sleep(5)
                    out = await evaljs(s, page, js)
                    print(f"===== {tag} =====")
                    if isinstance(out, list):
                        for x in out:
                            print(f"  {x.get('likes')}L {x.get('replies')}R {x.get('rts')}RT {x.get('views')}V | {x.get('text')}")
                            print(f"    {x.get('url')}")
                    else:
                        txt = out.get("text", "") if isinstance(out, dict) else str(out)
                        print(txt[:1800])
                    print()
                except Exception as e:
                    print(f"{tag} error: {str(e)[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
