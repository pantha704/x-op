#!/usr/bin/env python3
"""Hype radar - trends and hype from OUTSIDE X (owner question 2026-09-21: "are you actually pulling
the trendy hype or booming posts from other sites?").

Sources (all no-login, no-block):
  - Google Trends daily RSS (US)          -> what the general internet is searching RIGHT NOW
  - Anime News Network RSS                -> anime news/hype (announcements, trailers, films)
  - Dexerto RSS                           -> gaming/anime/streaming news
  - PlayStation Blog RSS / Nintendo Life  -> first-party game announcements
  - Reddit: IP-blocked from this VPS (direct + phone proxy) -> recorded as blocked, not faked

Output: targets/hype-ideas.json - [{source, title, url, ts, lane, hype}] sorted by hype.
Lanes: anime | games | tech | other. Cross-source duplicates get a hype bonus (same story on 2+ sites).
Usage: hype_radar.py [--hours 36]
"""
import json, re, sys, time
from datetime import datetime, timezone
import urllib.request

import feedparser

FEEDS = {
    "google_trends": "https://trends.google.com/trending/rss?geo=US",
    "ann": "https://www.animenewsnetwork.com/all/rss.xml",
    "dexerto": "https://www.dexerto.com/feed/",
    "psblog": "https://blog.playstation.com/feed/",
    "nintendolife": "https://www.nintendolife.com/feeds/latest",
    "pcgamer": "https://www.pcgamer.com/rss/",
}

LANE_WORDS = {
    "anime": r"\b(anime|manga|seiyuu|shonen|shoujo|isekai|episode|season|studio|otaku|waifu|cosplay)\b",
    "games": r"\b(game|gaming|playstation|xbox|nintendo|switch|steam|bungie|destiny|fortnite|zelda|mario|pokemon|elden|capcom|square enix)\b",
    "tech": r"\b(ai|llm|model|openai|anthropic|google|apple|chip|gpu|nvidia|amd|intel|robot|silicon)\b",
}
HYPE_WORDS = r"\b(announced|reveals?|trailer|teaser|first look|leak|delayed|release date|coming|launch|surprise|record|breaks|milestone)\b"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"})
    return urllib.request.urlopen(req, timeout=25).read()


def lane_of(text):
    t = text.lower()
    for lane, pat in LANE_WORDS.items():
        if re.search(pat, t):
            return lane
    return "other"


def main():
    hours = 36
    if "--hours" in sys.argv:
        hours = int(sys.argv[sys.argv.index("--hours") + 1])
    cutoff = time.time() - hours * 3600
    items = []
    for src, url in FEEDS.items():
        try:
            d = feedparser.parse(fetch(url))
        except Exception as ex:
            print(f"x {src}: {str(ex)[:60]}")
            continue
        n = 0
        for e in d.entries[:60]:
            ts = None
            for k in ("published_parsed", "updated_parsed"):
                if getattr(e, k, None):
                    ts = time.mktime(getattr(e, k)) - time.timezone
                    break
            if ts and ts < cutoff:
                continue
            title = (getattr(e, "title", "") or "").strip()
            if not title:
                continue
            hype = 0
            if re.search(HYPE_WORDS, title, re.I): hype += 3
            if src == "google_trends": hype += 2  # already a search trend
            items.append({
                "source": src,
                "title": title[:180],
                "url": getattr(e, "link", ""),
                "ts": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None,
                "lane": lane_of(title + " " + getattr(e, "summary", "")[:200]),
                "hype": hype,
            })
            n += 1
        print(f"{src}: {n} items")
    # cross-source duplicates: same story on 2+ sites -> bonus
    key = lambda t: " ".join(sorted(set(re.findall(r"[a-z0-9]{5,}", t.lower())))[:4])
    seen = {}
    for it in items:
        k = key(it["title"])
        seen.setdefault(k, []).append(it)
    for k, group in seen.items():
        if len({g["source"] for g in group}) >= 2:
            for g in group:
                g["hype"] += 4
                g["cross_site"] = len({x["source"] for x in group})
    items.sort(key=lambda x: (-x["hype"], x["lane"]))
    json.dump(items, open("/home/ubuntu/x-op/targets/hype-ideas.json", "w"), indent=1)
    for it in items[:18]:
        cs = f" x{it['cross_site']}" if it.get("cross_site") else ""
        print(f"h{it['hype']}{cs}  [{it['lane']:<6}] {it['source']:<14} {it['title'][:80]}")
    print(f"\n{len(items)} hype items -> targets/hype-ideas.json")


if __name__ == "__main__":
    main()
