#!/usr/bin/env python3
"""Research-rig X search helper (port 8933). Opens its own tab, searches X, extracts
article text + author + engagement, closes the tab. Read-only research."""
import asyncio, json, sys, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8933/mcp"

READ_JS = r"""JSON.stringify((() => {
  const out = [];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
    const tx = a.querySelector('[data-testid="tweetText"]');
    const un = a.querySelector('[data-testid="User-Name"]');
    const soc = a.querySelector('[data-testid="socialContext"]');
    const grp = a.querySelector('[role="group"]');
    const st = a.querySelectorAll('a[href*="/status/"]');
    let url = '';
    for (const l of st) { if (l.href && l.href.includes('/status/')) { url = l.href.split('?')[0]; break; } }
    out.push({
      who: un ? un.innerText.replace(/\n/g,' | ').slice(0,90) : '',
      soc: soc ? soc.innerText.slice(0,60) : '',
      text: tx ? tx.innerText.slice(0, 2200) : '',
      stats: grp ? grp.getAttribute('aria-label') : '',
      url: url
    });
  });
  return out;
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def main():
    queries = json.load(open(sys.argv[1]))
    mode = sys.argv[2] if len(sys.argv) > 2 else "top"
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = await call(s, "cloak_new_page", {})
            try:
                page = json.loads(np).get("page_id")
            except Exception:
                page = None
            if not page:
                try:
                    lp = await call(s, "cloak_list_pages", {})
                    page = json.loads(lp).get("pages", [])[0]["page_id"]
                except Exception:
                    page = None
            if not page:
                lr = await call(s, "cloak_launch", {"user_data_dir": "/home/ubuntu/.cloakbrowser/profiles/operator2"})
                try:
                    page = json.loads(lr).get("page_id")
                except Exception:
                    page = None
                if not page:
                    np2 = await call(s, "cloak_new_page", {})
                    page = json.loads(np2).get("page_id")
            print("PAGE:", page, file=sys.stderr)
            for q in queries:
                u = "https://x.com/search?q=" + urllib.parse.quote(q) + "&src=typed_query&f=" + mode
                await call(s, "cloak_navigate", {"page_id": page, "url": u})
                await asyncio.sleep(7)
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS})
                try:
                    items = json.loads(json.loads(r3).get("result", "[]") or "[]")
                except Exception as e:
                    items = []
                    print("PARSE ERR", e, r3[:200], file=sys.stderr)
                print("=" * 70)
                print("QUERY:", q, "| mode:", mode, "| n=", len(items))
                for it in items:
                    print("-" * 60)
                    print("WHO:", it.get("who"))
                    print("URL:", it.get("url"))
                    print("STATS:", (it.get("stats") or "").replace("\n", " "))
                    print("TXT:", (it.get("text") or "").replace("\n", " ")[:1200])
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass

asyncio.run(main())
