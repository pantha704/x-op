#!/usr/bin/env python3
"""Post-pattern research harvester: for a list of accounts, pull their top and recent posts
with engagement, so we can compare what worked vs what flopped.

Per account, 3 passes:
  top-all     : from:<user> min_faves:1000        (f=top)   -> all-time bangers
  top-recent  : from:<user> since:<date> min_faves:30 (f=top) -> recent winners
  baseline    : from:<user> -filter:replies       (f=live)  -> the ordinary feed (flops included)

Output: research/post-patterns/raw/<user>.json
Usage: post_research_harvest.py [--users a,b,c] [--since 2026-08-15]
"""
import asyncio, json, os, random, sys, time, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"
OUTDIR = "/home/ubuntu/x-op/research/post-patterns/raw"

EXTRACT = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].map(a => {
  const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
  const un = a.querySelector('[data-testid="User-Name"]');
  const tx = a.querySelector('[data-testid="tweetText"]');
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label')||'');
  let likes=null, replies=null, rts=null;
  const num = s => { const m = (s||'').replace(/,/g,'').match(/([\d.]+)\s*([KM])?/i); if(!m) return null; let v=parseFloat(m[1]); if(m[2]&&m[2].toUpperCase()==='K') v*=1000; if(m[2]&&m[2].toUpperCase()==='M') v*=1000000; return Math.round(v); };
  const likeBtn = a.querySelector('[data-testid="like"] span[data-testid="app-text-transition-container"], [data-testid="like"] span');
  if (likeBtn) likes = num(likeBtn.innerText);
  const rtBtn = a.querySelector('[data-testid="retweet"] span[data-testid="app-text-transition-container"], [data-testid="retweet"] span');
  if (rtBtn) rts = num(rtBtn.innerText);
  const repBtn = a.querySelector('[data-testid="reply"] span[data-testid="app-text-transition-container"], [data-testid="reply"] span');
  if (repBtn) replies = num(repBtn.innerText);
  for (const l of labels) { let m=l.match(/^([\d,]+)\s+likes?/i); if(m && likes===null) likes=parseInt(m[1].replace(/,/g,'')); m=l.match(/^([\d,]+)\s+repl/i); if(m && replies===null) replies=parseInt(m[1].replace(/,/g,'')); m=l.match(/^([\d,]+)\s+repost/i); if(m && rts===null) rts=parseInt(m[1].replace(/,/g,'')); }
  const media = a.querySelectorAll('[data-testid="tweetPhoto"], video, [data-testid="card.wrapper"]').length;
  const hasImg = a.querySelectorAll('[data-testid="tweetPhoto"] img').length;
  return { url: link ? link.href.split('?')[0] : null, handle: un ? (un.innerText.match(/@[A-Za-z0-9_]+/)||[''])[0] : '',
           likes: likes===null?-1:likes, replies: replies===null?-1:replies, rts: rts===null?-1:rts, media, imgs: hasImg, text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,220) : '',
           hasText: !!tx, age: t ? t.getAttribute('datetime') : '' };
}).filter(p => p.url))"""

USERS = [
    "sugoiLITE", "MangaMoguraRE", "AniNews", "animecorner_ac", "AIR_News01", "WSJ_manga",
    "Okami13_", "Genki_JPN", "HazzadorGamin", "Wario64", "eXtas1s", "GenshinUpdate",
    "TheTuringPost", "minchoi", "rowancheung", "dril", "nihilist_arbys", "historyinmemes",
]

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def scrape(s, page, query, tag, passes=3, min_likes=0):
    url = "https://x.com/search?q=" + urllib.parse.quote(query) + "&f=top"
    await call(s, "cloak_navigate", {"page_id": page, "url": url})
    await asyncio.sleep(random.uniform(3.5, 5.0))
    # guard: make sure we're really on the search results page (not home/feed), else retry once
    chk = await call(s, "cloak_evaluate", {"page_id": page, "expression": "JSON.stringify({u: location.href.slice(0,40), n: document.querySelectorAll('article[data-testid=\"tweet\"]').length})"})
    try:
        st = json.loads(json.loads(chk).get("result", "{}"))
    except Exception:
        st = {}
    if not str(st.get("u", "")).startswith("https://x.com/search") or st.get("n", 0) == 0:
        await call(s, "cloak_navigate", {"page_id": page, "url": url})
        await asyncio.sleep(random.uniform(5, 7))
    out = []
    for _ in range(passes):
        r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": EXTRACT})
        try:
            rows = json.loads(json.loads(r3).get("result", "[]"))
        except Exception:
            rows = []
        for row in rows:
            if row["likes"] >= min_likes:
                row["pass"] = tag
                out.append(row)
        await call(s, "cloak_evaluate", {"page_id": page, "expression": "window.scrollBy(0, 1600); 'ok'"})
        await asyncio.sleep(random.uniform(1.3, 2.0))
    return out

async def main():
    users = USERS
    if "--users" in sys.argv:
        users = sys.argv[sys.argv.index("--users") + 1].split(",")
    since = "2026-08-15"
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]
    os.makedirs(OUTDIR, exist_ok=True)
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            pages = json.loads(lp).get("pages", [])
            page = pages[0]["page_id"] if pages else json.loads(await call(s, "cloak_launch", {"user_data_dir": PROFILE})).get("page_id")
            for u in users:
                path = f"{OUTDIR}/{u}.json"
                if os.path.exists(path) and "--force" not in sys.argv:
                    print(f"skip {u} (exists)")
                    continue
                rows = []
                rows += await scrape(s, page, f"from:{u} min_faves:1000 -filter:replies", "top-all", passes=3)
                rows += await scrape(s, page, f"from:{u} since:{since} min_faves:30 -filter:replies", "top-recent", passes=2)
                rows += await scrape(s, page, f"from:{u} -filter:replies", "baseline", passes=3)
                # dedupe by url, keep max likes seen
                byurl = {}
                for row in rows:
                    k = row["url"]
                    if k not in byurl or row["likes"] > byurl[k]["likes"]:
                        byurl[k] = row
                data = list(byurl.values())
                if not data and os.path.exists(path):
                    print(f"{u}: empty result, keeping existing file")
                    continue
                json.dump(data, open(path, "w"), indent=1)
                print(f"{u}: {len(data)} posts -> {path}")
                await asyncio.sleep(random.uniform(20, 35))

asyncio.run(main())
