#!/usr/bin/env python3
"""Genre growth study: scrape account histories across genres to answer
"which genre should we pick, and did these accounts grow fast or slow?"

Per account (own page, never touches the worker's fire page):
  1. profile      -> followers, joined date, bio, name
  2. top posts    -> from:<h> min_faves:3000, f=top   (what boomed + when)
  3. recent feed  -> from:<h> f=live                  (current baseline)

Output: research/genre-study/raw/<handle>.json
Usage: genre_study.py [--only a,b,c]
"""
import asyncio, json, os, random, sys, urllib.parse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
OUTDIR = "/home/ubuntu/x-op/research/genre-study/raw"
os.makedirs(OUTDIR, exist_ok=True)

ACCOUNTS = {
    "anime": ["sugoiLITE", "MangaMoguraRE", "AIR_News01", "AniNews", "AnimexTwts",
              "AnimetrendsLA", "WSJ_manga", "AniTrendz", "animecorner_ac"],
    "gaming": ["Okami13_", "Genki_JPN", "HazzadorGamin", "Wario64", "eXtas1s",
               "Dexerto", "VideoArtGame", "Nezzzooo", "Kizessuu"],
    "tech": ["TheTuringPost", "minchoi", "rowancheung", "tomashibadaisen", "cdlnxxuy",
             "OllieDreamer", "baralover3003", "AdamDunneOffic"],
}

PROFILE_JS = r"""JSON.stringify((() => {
  const q = s => document.querySelector(s);
  const fol = q('a[href$="/verified_followers"], a[href$="/followers"]');
  const bio = q('[data-testid="UserDescription"]');
  const items = q('[data-testid="UserProfileHeader_Items"]');
  const name = q('[data-testid="UserName"]');
  return {
    followers: fol ? fol.innerText.replace(/\n/g,' ') : '',
    bio: bio ? bio.innerText.slice(0,220) : '',
    items: items ? items.innerText.replace(/\n/g,' | ') : '',
    name: name ? name.innerText.replace(/\n/g,' ') : '',
  };
})())"""

POSTS_JS = r"""JSON.stringify([...document.querySelectorAll('article[data-testid="tweet"]')].map(a => {
  const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
  const un = a.querySelector('[data-testid="User-Name"]');
  const tx = a.querySelector('[data-testid="tweetText"]');
  const labels = [...a.querySelectorAll('[role="group"] [aria-label]')].map(b => b.getAttribute('aria-label')||'');
  let likes=null, rts=null, replies=null;
  for (const l of labels) {
    let m=l.match(/^([\d,]+)\s+likes?/i); if(m && likes===null) likes=parseInt(m[1].replace(/,/g,''));
    m=l.match(/^([\d,]+)\s+repl/i); if(m && replies===null) replies=parseInt(m[1].replace(/,/g,''));
    m=l.match(/^([\d,]+)\s+repost/i); if(m && rts===null) rts=parseInt(m[1].replace(/,/g,''));
  }
  const media = a.querySelectorAll('[data-testid="tweetPhoto"], video, [data-testid="card.wrapper"]').length;
  return { url: link ? link.href.split('?')[0] : null, handle: un ? (un.innerText.match(/@[A-Za-z0-9_]+/)||[''])[0] : '',
           likes: likes===null?-1:likes, rts: rts===null?-1:rts, replies: replies===null?-1:replies, media,
           text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,200) : '', age: t ? t.getAttribute('datetime') : '' };
}).filter(p => p.url))"""

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def grab(s, pid, url, js, wait):
    await call(s, "cloak_navigate", {"page_id": pid, "url": url})
    await asyncio.sleep(wait)
    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": js})
    try:
        return json.loads(json.loads(raw).get("result", "null"))
    except Exception:
        return None

async def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    todo = [(g, h) for g, hs in ACCOUNTS.items() for h in hs if not only or h in only]
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            pg = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            pid = pg.get("page_id") or pg.get("id")
            print("page:", pid, "| accounts:", len(todo))
            await asyncio.sleep(3)
            for genre, h in todo:
                path = os.path.join(OUTDIR, h + ".json")
                if os.path.exists(path) and "--redo" not in sys.argv:
                    print("skip (have):", h); continue
                rec = {"handle": h, "genre": genre}
                try:
                    rec["profile"] = await grab(s, pid, "https://x.com/" + h, PROFILE_JS, random.uniform(4, 6))
                    await asyncio.sleep(random.uniform(2, 3.5))
                    rec["top"] = await grab(s, pid, "https://x.com/search?q=" + urllib.parse.quote("from:" + h + " min_faves:3000") + "&f=top", POSTS_JS, random.uniform(4, 6))
                    await asyncio.sleep(random.uniform(2, 3.5))
                    rec["recent"] = await grab(s, pid, "https://x.com/search?q=" + urllib.parse.quote("from:" + h) + "&f=live", POSTS_JS, random.uniform(4, 6))
                    prof = rec.get("profile") or {}
                    print("%-18s [%s] fol=%-8s joined=%s | top=%s recent=%s" % (
                        h, genre, (prof.get("followers") or "?")[:8],
                        ((prof.get("items") or "").split("|")[0].strip())[:18],
                        len(rec.get("top") or []), len(rec.get("recent") or [])))
                except Exception as e:
                    print("FAIL", h, str(e)[:90])
                json.dump(rec, open(path, "w"), indent=1)
                await asyncio.sleep(random.uniform(3, 5))
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass
    print("done")

asyncio.run(main())
