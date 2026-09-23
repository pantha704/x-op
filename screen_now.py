#!/usr/bin/env python3
"""Print-only screen: read current likes on our live replies (no ledger writes).

Usage: screen_now.py [--min-age-h 0.5] [--max 40]
Reads vault ledger entries with your_handle reply URLs, opens each, prints likes.
For +1h perception reads. The +24h verdict stamping lives in measure_ledger.py.
"""
import asyncio, json, sys
from datetime import datetime, timezone
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
LEDGER = "/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json"

READ_JS = r"""JSON.stringify((() => {
  const ID = "__ID__";
  const a = [...document.querySelectorAll('article[data-testid="tweet"]')].find(x => x.querySelector('a[href*="/status/' + ID + '"]'));
  if (!a) return null;
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
  let likes = null, replies = null;
  for (const l of labels) {
    let m = l.match(/^([\d,]+)\s+likes?/i); if (m) likes = parseInt(m[1].replace(/,/g, ''));
    m = l.match(/^([\d,]+)\s+repl/i); if (m) replies = parseInt(m[1].replace(/,/g, ''));
  }
  return { likes, replies };
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


def age_h(e):
    ts = e.get("firedAt") or ""
    try:
        a = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if a.tzinfo is None:
            a = a.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - a).total_seconds() / 3600
    except Exception:
        return 999


async def main():
    args = sys.argv[1:]
    min_age = float(args[args.index("--min-age-h") + 1]) if "--min-age-h" in args else 0.5
    max_n = int(args[args.index("--max") + 1]) if "--max" in args else 40
    es = json.load(open(LEDGER))["entries"]
    todo = [e for e in es if "your_handle/status" in (e.get("url") or "") and age_h(e) >= min_age][-max_n:]
    print(f"screen: {len(todo)} live replies (age >= {min_age}h)")
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            page = json.loads(lp).get("pages", [])[0]["page_id"]
            for e in todo:
                try:
                    await call(s, "cloak_navigate", {"page_id": page, "url": e["url"]})
                    await asyncio.sleep(2.6)
                    r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS.replace("__ID__", e["url"].split("/")[-1])})
                    d = json.loads(json.loads(r3).get("result", "null") or "null")
                except Exception:
                    d = None
                lk = (d or {}).get("likes")
                rp = (d or {}).get("replies")
                flag = "ALIVE" if (lk or 0) >= 2 else ("hit" if (lk or 0) >= 1 else "flat")
                print(f"  {flag:5s} likes={lk} replies={rp}  ago={age_h(e):4.1f}h  | {e.get('text','')[:52]}")
                await asyncio.sleep(0.8)

asyncio.run(main())
