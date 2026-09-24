#!/usr/bin/env python3
"""Aesthetic image picker: find art / scenery / aesthetic posts with media on X.

Owner spec (2026-09-24): the aesthetic worker posts ONLY images, no text by
default; when there is something about the image it says it, short; and the
owner/artist gets credited - @handle when on X, else "Platform: username".

Output: JSON list of candidates on stdout:
  {tweet_url, author, img, likes, text, credit}
Filters: media images only (no videos), likes >= 250, skip repost-crediting posts,
skip NSFW-ish text. Download happens in the worker (curl the img url).

Usage: aesthetic_pick.py [--limit N] [--min-likes N]
"""
import asyncio
import json
import re
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

# queries in the account's universe: art, scenery, aesthetic - anime / games / general digital
QUERIES = [
    "anime art scenery",
    "(digital art OR concept art) landscape",
    "(pixel art OR retro art) city",
    "genshin art scenery",
    "cozy art illustration",
    "cyberpunk art cityscape",
    "my art painting landscape",
    "original illustration art scenery",
    "fantasy art environment",
]

READ_JS = r"""JSON.stringify((() => {
  const out = [];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
    const tx = a.querySelector('[data-testid="tweetText"]');
    const un = a.querySelector('[data-testid="User-Name"]');
    const grp = a.querySelector('[role="group"]');
    const imgs = [...a.querySelectorAll('img')].filter(i => {
      const s = i.src || '';
      return s.includes('pbs.twimg.com/media');
    }).map(i => i.src);
    let url = '';
    for (const l of a.querySelectorAll('a[href*="/status/"]')) {
      if (l.href && l.href.includes('/status/')) { url = l.href.split('?')[0]; break; }
    }
    const handle = un ? (un.innerText.match(/@([A-Za-z0-9_]+)/) || [])[1] || '' : '';
    const tm = a.querySelector('time');
    out.push({
      author: handle,
      who: un ? un.innerText.replace(/\n/g,' | ').slice(0,80) : '',
      text: tx ? tx.innerText.slice(0, 400) : '',
      stats: grp ? grp.getAttribute('aria-label') : '',
      img: imgs.length ? imgs[0] : '',
      nimg: imgs.length,
      dt: tm ? tm.getAttribute('datetime') : '',
      url: url
    });
  });
  return out;
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


def parse_likes(stats):
    m = re.search(r'([\d,\.]+[KkMm]?) (?:likes|Likes|LIKES)', stats or '')
    if not m:
        return 0
    v = m.group(1).replace(',', '')
    try:
        if v.lower().endswith('k'):
            return int(float(v[:-1]) * 1000)
        if v.lower().endswith('m'):
            return int(float(v[:-1]) * 1000000)
        return int(v)
    except Exception:
        return 0


BANNED_TEXT = re.compile(r'\bnsfw|18\+|onlyfans|porn|lewd\b', re.I)
REPOST_TEXT = re.compile(r'\b(not mine|repost|rt\b|via\s|credit[: ]|found this|unknown artist)', re.I)


async def main():
    argv = sys.argv[1:]
    lim = 4
    min_likes = 250
    if "--limit" in argv:
        lim = int(argv[argv.index("--limit") + 1])
    if "--min-likes" in argv:
        min_likes = int(argv[argv.index("--min-likes") + 1])
    out = []
    seen = set()
    async with streamable_http_client(URL) as ctx:
        async with ClientSession(ctx[0], ctx[1]) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/explore"}))
            pid = np.get("page_id") or np.get("id")
            await asyncio.sleep(3)
            for q in QUERIES:
                try:
                    url = "https://x.com/search?q=" + q.replace(' ', '%20').replace('(', '%28').replace(')', '%29').replace('"', '%22') + "&src=typed_query&f=top"
                    await call(s, "cloak_navigate", {"page_id": pid, "url": url})
                    await asyncio.sleep(4)
                    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": READ_JS})
                    rows = json.loads(json.loads(raw).get("result", "[]"))
                except Exception as e:
                    print("query fail:", q, str(e)[:60], file=sys.stderr)
                    continue
                for r in rows:
                    if not r.get("url") or not r.get("img") or not r.get("author"):
                        continue
                    if r["url"] in seen:
                        continue
                    likes = parse_likes(r.get("stats") or "")
                    if likes < min_likes:
                        continue
                    if BANNED_TEXT.search(r.get("text") or ""):
                        continue
                    if REPOST_TEXT.search(r.get("text") or ""):
                        continue
                    dt = r.get("dt") or ""
                    if dt:
                        try:
                            import datetime as _d
                            when = _d.datetime.fromisoformat(dt.replace('Z', '+00:00'))
                            age_days = (_d.datetime.now(_d.timezone.utc) - when).days
                            if age_days > 120:
                                continue
                        except Exception:
                            pass
                    seen.add(r["url"])
                    out.append({
                        "tweet_url": r["url"],
                        "author": r["author"],
                        "credit": "@" + r["author"],
                        "img": r["img"].split('&name=')[0] + "&name=large" if '?' in r["img"] else r["img"],
                        "likes": likes,
                        "text": (r.get("text") or "").strip(),
                    })
            # ---- additional pools: unsplash (free photography) + pinterest (aesthetic) ----
            STOCK = [
                ("unsplash", "https://unsplash.com/s/photos/serene-landscape"),
                ("unsplash", "https://unsplash.com/s/photos/cozy-forest-cabin"),
                ("unsplash", "https://unsplash.com/s/photos/cyberpunk-city-night"),
                ("pinterest", "https://www.pinterest.com/search/pins/?q=aesthetic%20scenery%20art"),
                ("pinterest", "https://www.pinterest.com/search/pins/?q=anime%20scenery%20art"),
                ("pinterest", "https://www.pinterest.com/search/pins/?q=cozy%20fantasy%20art"),
            ]
            STOCK_JS = r"""JSON.stringify((() => {
  const out = [];
  [...document.querySelectorAll('img')].forEach(i => {
    const s = i.src || '';
    if (s.includes('images.unsplash.com')) { if (i.width >= 150 && i.height >= 150) out.push({pool:'unsplash', img:s.split('?')[0] + '?fm=jpg&q=80&w=1600'}); }
    else if (s.includes('i.pinimg.com') && !s.includes('60x60') && !s.includes('75x75') && !s.includes('30x30')) out.push({pool:'pinterest', img:s.replace('/236x/','/736x/').replace('/474x/','/736x/').replace('/564x/','/736x/')});
  });
  return out;
})())"""
            for pool, url in STOCK:
                try:
                    await call(s, "cloak_navigate", {"page_id": pid, "url": url})
                    await asyncio.sleep(6)
                    if pool == "pinterest":  # lazy-load: scroll so real pins render
                        for y in (1400, 2800):
                            await call(s, "cloak_evaluate", {"page_id": pid,
                                "expression": "window.scrollTo(0,%d);1" % y})
                            await asyncio.sleep(1.6)
                    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": STOCK_JS})
                    rows = json.loads(json.loads(raw).get("result", "[]"))
                except Exception as e:
                    print("stock fail:", pool, str(e)[:60], file=sys.stderr)
                    continue
                for x in rows:
                    key = x["img"]
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"tweet_url": "", "author": "", "credit": "", "img": key,
                                "likes": 0, "text": "", "source": pool})
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass
    # X candidates ranked by likes; stock candidates fill the tail (worker may pick from either)
    for r in out:
        r.setdefault("source", "x")
    xr = [r for r in out if r.get("source") == "x"]
    sr = [r for r in out if r.get("source") != "x"]
    xr.sort(key=lambda v: -v["likes"])
    final = xr[:max(3, lim)] + sr[:6]
    print(json.dumps(final, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
