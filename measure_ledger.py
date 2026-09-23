#!/usr/bin/env python3
"""Measure ledger entries at +24h: fill likes / repliesBack / verdict.

Modes:
  default    permalink measurement for entries whose url points at our reply
  --resolve  search-based recovery for entries whose url is the parent:
             searches `from:your_handle <keywords>`, matches text locally,
             recovers our reply URL + metrics.
Common: --min-age-h (default 20), --max N, --dry, --no-push
"""
import asyncio, json, os, re, subprocess, sys, time, urllib.parse
from datetime import datetime, timezone
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"
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
  const tx = a.querySelector('[data-testid="tweetText"]');
  return { likes, replies, text: tx ? tx.innerText.slice(0, 60) : '' };
})())"""

LIST_JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].slice(0, 15).map(a => {
  const t = a.querySelector('time'); const tl = t ? t.closest('a') : null;
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label') || '');
  let likes = null, replies = null;
  for (const l of labels) {
    let m = l.match(/^([\d,]+)\s+likes?/i); if (m) likes = parseInt(m[1].replace(/,/g, ''));
    m = l.match(/^([\d,]+)\s+repl/i); if (m) replies = parseInt(m[1].replace(/,/g, ''));
  }
  const tx = a.querySelector('[data-testid="tweetText"]');
  return { url: tl ? tl.href.split('?')[0] : null, likes, replies, text: tx ? tx.innerText.replace(/\n/g, ' ') : '' };
}).filter(x => x.url))"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


def age_h(entry):
    ts = entry.get("firedAt") or ""
    try:
        a = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if a.tzinfo is None:
            a = a.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - a).total_seconds() / 3600
    except Exception:
        return 999


def kws(text, n=6):
    return " ".join(re.findall(r"[A-Za-z0-9'\u2019\u3040-\u30ff\u4e00-\u9fff]+", text or "")[:n])


async def pick_page(s):
    """Own dedicated tab (never pages[0]): measurement runs while waves may be live."""
    np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
    page = np.get("page_id") or np.get("id")
    if page:
        await asyncio.sleep(2)
        return page
    return json.loads(await call(s, "cloak_launch", {"user_data_dir": PROFILE})).get("page_id")


def stamp(e, likes, replies, via):
    e["likes"] = likes
    e["repliesBack"] = replies
    e["verdict"] = ("winner" if (likes or 0) >= 10 else "mid" if (likes or 0) >= 1 else "dead") if likes is not None else None
    e["measuredAt"] = datetime.now(timezone.utc).isoformat()
    e["resolvedVia"] = via


async def main():
    args = sys.argv[1:]
    min_age = float(args[args.index("--min-age-h") + 1]) if "--min-age-h" in args else 20.0
    max_n = int(args[args.index("--max") + 1]) if "--max" in args else 200
    dry = "--dry" in args
    resolve_mode = "--resolve" in args

    led = json.load(open(LEDGER))
    entries = led["entries"]
    if resolve_mode:
        todo = [e for e in entries if e.get("likes") is None
                and "your_handle/status" not in (e.get("url") or "") and age_h(e) >= min_age][:max_n]
        print(f"resolve mode | lookup candidates: {len(todo)}")
    else:
        todo = [e for e in entries if e.get("likes") is None
                and "your_handle/status" in (e.get("url") or "") and age_h(e) >= min_age][:max_n]
        print(f"permalink mode | measurable: {len(todo)}")

    done = 0
    found = 0
    if todo and not dry:
        async with streamable_http_client(URL) as ctx:
            r, w = ctx[0], ctx[1]
            async with ClientSession(r, w) as s:
                await s.initialize()
                page = await pick_page(s)
                for e in todo:
                    if resolve_mode:
                        q = "from:your_handle " + kws(e.get("text"), 6)
                        url = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=top"
                        try:
                            await call(s, "cloak_navigate", {"page_id": page, "url": url})
                            await asyncio.sleep(3.2)
                            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": LIST_JS})
                            rows = json.loads(json.loads(r3).get("result", "[]"))
                        except Exception:
                            rows = []
                        probe = kws(e.get("text"), 4).lower()[:32]
                        hit = None
                        for row in rows:
                            if probe and probe in (row.get("text") or "").lower():
                                hit = row
                                break
                        if hit:
                            e["url"] = hit["url"]
                            stamp(e, hit.get("likes"), hit.get("replies"), "search")
                            found += 1
                            print(f"  + {hit['url'].split('/')[-1]}  likes={hit.get('likes')}  | {e.get('text','')[:44]}")
                        else:
                            print(f"  x not found | {e.get('text','')[:44]}")
                        done += 1
                        await asyncio.sleep(1.0)
                    else:
                        try:
                            await call(s, "cloak_navigate", {"page_id": page, "url": e["url"]})
                            await asyncio.sleep(3.2)
                            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": READ_JS.replace("__ID__", e["url"].split("/")[-1])})
                            data = json.loads(json.loads(r3).get("result", "null") or "null")
                        except Exception:
                            data = None
                        if data:
                            stamp(e, data.get("likes"), data.get("replies"), "permalink")
                            done += 1
                            print(f"  {e['url'].split('/')[-1]}  likes={e['likes']}  -> {e['verdict']}")
                        await asyncio.sleep(1.0)
                # close our dedicated tab so tabs never pile up
                try:
                    await call(s, "cloak_close_page", {"page_id": page})
                except Exception:
                    pass

    json.dump(led, open(LEDGER, "w"), indent=2, ensure_ascii=False)
    open(LEDGER, "a").write("\n")
    if not dry and ("--no-push" not in args):
        subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "add", "PARA/3. Resources/Operator - Reply Ledger.json"])
        subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "commit", "-m", f"Operator op: +24h verdicts ({done} resolved, {found} via search)"])
        subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "pull", "--rebase", "origin", "master"])
        subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "push", "origin", "master"])
    w_ = sum(1 for e in entries if e.get("verdict") == "winner")
    m_ = sum(1 for e in entries if e.get("verdict") == "mid")
    d_ = sum(1 for e in entries if e.get("verdict") == "dead")
    print(f"processed {done} | found {found} | totals: winner={w_} mid={m_} dead={d_}")

asyncio.run(main())
