#!/usr/bin/env python3
"""Games radar - games / PC games / Genshin signals from OUTSIDE X (owner directive 2026-09-21).

Sources:
  - Steam charts (most played + top sellers)  : what PC players actually play right now
  - Steam news RSS + PC Gamer / Dexerto / PS Blog / Nintendo Life feeds
  - HoYoLAB (Genshin community API)           : Genshin/HoYo community posts (public endpoints)
  - TikTok Creative Center (via rig)          : gaming hashtags trending
  - Pinterest (via rig)                       : genshin/gaming pins (what people save)
  - Twitch directory (via rig, optional)      : top live categories

Output: targets/games-ideas.json
Usage: games_radar.py [--rig]
"""
import asyncio, json, re, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

import feedparser

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
OUT = "/home/ubuntu/x-op/targets/games-ideas.json"

FEEDS = {
    "steam_news": "https://store.steampowered.com/feeds/news.xml",
    "pcgamer": "https://www.pcgamer.com/rss/",
    "dexerto": "https://www.dexerto.com/feed/",
    "psblog": "https://blog.playstation.com/feed/",
    "nintendolife": "https://www.nintendolife.com/feeds/latest",
}
GAME_WORDS = r"\b(game|gaming|steam|pc|playstation|xbox|nintendo|switch|genshin|hoyoverse|hoyo|zelda|mario|pokemon|final fantasy|elden|baldur|fortnite|minecraft|valorant|league|dota|cs2|counter-strike|overwatch|destiny|bungie|starfield|cyberpunk)\b"


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()


def steam_charts():
    out = {}
    for name, url in (("mostplayed", "https://store.steampowered.com/charts/mostplayed"),
                      ("topselling", "https://store.steampowered.com/charts/topselling/global")):
        try:
            html = fetch(url).decode("utf-8", "replace")
        except Exception as ex:
            out[name] = f"ERR {str(ex)[:50]}"
            continue
        rows = re.findall(r'class="[^"]*_1n_4-zvf0n4aqGEksbgW9N[^"]*"[^>]*>([^<]{2,60})<', html)
        if not rows:
            rows = re.findall(r'<div class="[^"]*_2n_4[^"]*"[^>]*>([^<]{2,60})<', html)
        out[name] = rows[:25]
    return out


def feeds():
    items = []
    for src, url in FEEDS.items():
        try:
            d = feedparser.parse(fetch(url))
        except Exception:
            continue
        for e in d.entries[:40]:
            t = (getattr(e, "title", "") or "").strip()
            if t and re.search(GAME_WORDS, t, re.I):
                items.append({"source": src, "title": t[:170], "url": getattr(e, "link", "")})
    return items


def hoyolab():
    """Genshin community posts - public HoYoLAB endpoints (no auth)."""
    out = []
    for forum in (("genshin", 26), ("hkrpg", 52)):
        url = ("https://bbs-api-os.hoyolab.com/community/post/wapi/getForumPostList?"
               f"forum_id={forum[1]}&gids=2&is_good=false&is_hot=true&page_size=15&sort_type=2")
        try:
            d = json.loads(fetch(url))
            for p in (d.get("data", {}).get("list") or [])[:15]:
                post = p.get("post", {})
                out.append({
                    "forum": forum[0],
                    "title": (post.get("subject") or "")[:170],
                    "likes": (post.get("stat") or {}).get("like_num"),
                    "url": f"https://www.hoyolab.com/article/{post.get('post_id')}",
                })
        except Exception as ex:
            out.append({"forum": forum[0], "error": str(ex)[:60]})
    return out


async def rig_call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def rig_sources():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    out = {"tiktok": [], "pinterest": [], "twitch": []}
    async with streamable_http_client("http://127.0.0.1:8932/mcp") as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await rig_call(s, "cloak_new_page", {"url": "about:blank"}))
            page = np.get("page_id") or np.get("id")
            # TikTok trending hashtags (gaming filter)
            await rig_call(s, "cloak_navigate", {"page_id": page, "url": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"})
            await asyncio.sleep(9)
            r1 = await rig_call(s, "cloak_evaluate", {"page_id": page, "expression": "document.body.innerText.slice(0,6000)"})
            try:
                txt = json.loads(r1).get("result", "")
            except Exception:
                txt = r1
            tags = re.findall(r"#([A-Za-z0-9_]{3,40})", txt)
            out["tiktok"] = [t for t in dict.fromkeys(tags)][:40]
            # Pinterest gaming pins
            pins = []
            for q in ("genshin impact wallpaper", "pc gaming setup", "genshin fanart"):
                await rig_call(s, "cloak_navigate", {"page_id": page, "url": "https://www.pinterest.com/search/pins/?q=" + urllib.parse.quote(q)})
                await asyncio.sleep(7)
                r2 = await rig_call(s, "cloak_evaluate", {"page_id": page, "expression": "JSON.stringify([...document.querySelectorAll('img')].map(i=>i.src).filter(s=>s.includes('pinimg')).slice(0,10))"})
                try:
                    urls = json.loads(json.loads(r2).get("result", "[]"))
                except Exception:
                    urls = []
                pins.append({"query": q, "pins": urls})
            out["pinterest"] = pins
            # Twitch top categories
            await rig_call(s, "cloak_navigate", {"page_id": page, "url": "https://www.twitch.tv/directory"})
            await asyncio.sleep(8)
            r3 = await rig_call(s, "cloak_evaluate", {"page_id": page, "expression": "JSON.stringify([...document.querySelectorAll('a[href^=\"/directory/game/\"]')].map(a=>a.innerText.replace(/\\n/g,' ').slice(0,60)).slice(0,20))"})
            try:
                out["twitch"] = json.loads(json.loads(r3).get("result", "[]"))
            except Exception:
                out["twitch"] = []
            await rig_call(s, "cloak_close_page", {"page_id": page})
    return out


def main():
    do_rig = "--rig" in sys.argv
    res = {"built": datetime.now(tz=timezone.utc).isoformat()}
    for name, fn in (("steam", steam_charts), ("feeds", feeds), ("hoyolab", hoyolab)):
        try:
            res[name] = fn()
            print(name, "ok:", len(res[name]) if isinstance(res[name], (list, dict)) else res[name])
        except Exception as ex:
            res[name] = []
            print(name, "FAILED:", str(ex)[:70])
    if do_rig:
        plat = asyncio.run(rig_sources())
        res.update(plat)
        print("tiktok:", len(res.get("tiktok", [])), "pinterest q:", len(res.get("pinterest", [])), "twitch:", len(res.get("twitch", [])))
    json.dump(res, open(OUT, "w"), indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
