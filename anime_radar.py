#!/usr/bin/env python3
"""Anime radar - anime content signals from OUTSIDE X (owner directive 2026-09-21).

Sources:
  - AniList GraphQL   : trending now + all-time popular + top rated (fanbase size signal)
  - Jikan (MyAnimeList): top by members + current season
  - TikTok Creative Center (via rig): trending hashtags -> anime-related ones
  - Pinterest (via rig) : search pins for anime keywords (what people actually save)
  - Google Trends RSS   : anime-related search trends
  - Anime news RSS (ANN/Dexerto): what's being written about

Owner's angle: not just "what's latest" - evergreen titles with BIG fanbases but LOW current post
volume are the opportunity (engagement without competition).

Output: targets/anime-ideas.json
Usage: anime_radar.py [--tiktok] [--pinterest]   (rig passes are optional/slow)
"""
import asyncio, json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

import feedparser

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}
OUT = "/home/ubuntu/x-op/targets/anime-ideas.json"

ANILIST_Q = """
{ trending: Page(perPage: 15) { media(sort: TRENDING_DESC, type: ANIME) { title { romaji english } popularity trending genres } }
  popular: Page(perPage: 30) { media(sort: POPULARITY_DESC, type: ANIME) { title { romaji english } popularity trending genres } }
  rated: Page(perPage: 20) { media(sort: SCORE_DESC, type: ANIME) { title { romaji english } popularity averageScore genres } } }
"""


def http_json(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=25).read())


def anilist():
    d = http_json("https://graphql.anilist.co", json.dumps({"query": ANILIST_Q}).encode())
    out = {}
    for k in ("trending", "popular", "rated"):
        rows = []
        for m in d["data"][k]["media"]:
            t = m["title"]
            rows.append({
                "title": t.get("english") or t.get("romaji"),
                "popularity": m.get("popularity"),
                "trending": m.get("trending"),
                "score": m.get("averageScore"),
                "genres": m.get("genres"),
            })
        out[k] = rows
    return out


def jikan():
    top = http_json("https://api.jikan.moe/v4/top/anime?limit=25")["data"]
    season = http_json("https://api.jikan.moe/v4/seasons/now?limit=20")["data"]
    return {
        "top": [{"title": a["title"], "members": a.get("members"), "score": a.get("score")} for a in top],
        "season": [{"title": a["title"], "members": a.get("members"), "score": a.get("score")} for a in season],
    }


def google_trends_anime():
    try:
        d = feedparser.parse(urllib.request.urlopen(urllib.request.Request(
            "https://trends.google.com/trending/rss?geo=US", headers=UA), timeout=20).read())
    except Exception:
        return []
    out = []
    for e in d.entries[:40]:
        t = getattr(e, "title", "")
        if re.search(r"\b(anime|manga|otaku|cosplay|waifu|shonen|jojo|naruto|one piece|dragon ball|pokemon|genshin)\b", t, re.I):
            out.append({"title": t, "url": getattr(e, "link", "")})
    return out


def anime_news():
    out = []
    for src, url in (("ann", "https://www.animenewsnetwork.com/all/rss.xml"),
                     ("dexerto", "https://www.dexerto.com/feed/")):
        try:
            d = feedparser.parse(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read())
        except Exception:
            continue
        for e in d.entries[:40]:
            t = getattr(e, "title", "")
            if re.search(r"\b(anime|manga|season|film|studio|episode|dub|sub|opening|ending)\b", t, re.I):
                out.append({"source": src, "title": t[:170], "url": getattr(e, "link", "")})
    return out


async def rig_call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def tiktok_pinterest(do_tiktok, do_pinterest):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    out = {"tiktok": [], "pinterest": []}
    async with streamable_http_client("http://127.0.0.1:8932/mcp") as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await rig_call(s, "cloak_new_page", {"url": "about:blank"}))
            page = np.get("page_id") or np.get("id")
            if do_tiktok:
                await rig_call(s, "cloak_navigate", {"page_id": page, "url": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"})
                await asyncio.sleep(9)
                r1 = await rig_call(s, "cloak_evaluate", {"page_id": page, "expression": "document.body.innerText.slice(0,4000)"})
                try:
                    txt = json.loads(r1).get("result", "")
                except Exception:
                    txt = r1
                rows = re.findall(r"#([A-Za-z0-9_]{3,40})", txt)
                out["tiktok"] = [{"hashtag": h} for h in dict.fromkeys(rows)][:40]
            if do_pinterest:
                pins = []
                for q in ("anime aesthetic", "anime quotes", "anime fanart"):
                    await rig_call(s, "cloak_navigate", {"page_id": page, "url": "https://www.pinterest.com/search/pins/?q=" + urllib.parse.quote(q)})
                    await asyncio.sleep(7)
                    r2 = await rig_call(s, "cloak_evaluate", {"page_id": page, "expression": "JSON.stringify([...document.querySelectorAll('img')].map(i=>i.src).filter(s=>s.includes('pinimg')).slice(0,12))"})
                    try:
                        urls = json.loads(json.loads(r2).get("result", "[]"))
                    except Exception:
                        urls = []
                    pins.append({"query": q, "pins": urls})
                out["pinterest"] = pins
            await rig_call(s, "cloak_close_page", {"page_id": page})
    return out


def main():
    do_tt = "--tiktok" in sys.argv
    do_pin = "--pinterest" in sys.argv
    res = {"built": datetime.now(tz=timezone.utc).isoformat()}
    for name, fn in (("anilist", anilist), ("mal", jikan), ("google_trends", google_trends_anime), ("news", anime_news)):
        try:
            res[name] = fn()
            n = len(res[name]) if isinstance(res[name], list) else {k: len(v) for k, v in res[name].items()}
            print(name, "->", n)
        except Exception as ex:
            res[name] = []
            print(name, "FAILED:", str(ex)[:70])
    if do_tt or do_pin:
        plat = asyncio.run(tiktok_pinterest(do_tt, do_pin))
        res.update(plat)
        print("tiktok:", len(res.get("tiktok", [])), "| pinterest queries:", len(res.get("pinterest", [])))
    json.dump(res, open(OUT, "w"), indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
