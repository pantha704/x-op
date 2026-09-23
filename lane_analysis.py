#!/usr/bin/env python3
"""Rank reply lanes by measured performance (our replies' likes).

Joins logs/measures-*.jsonl (our replies' like counts, scraped 3x/day) with the
reply ledger (parent URLs) and classifies each parent into a lane. Writes
research/reply-lane-analysis.md. Read-only.
"""
import glob
import json
import os
import re
from collections import defaultdict

X = "/home/ubuntu/x-op"
LEDGER = "/home/ubuntu/obsidian/PARA/3. Resources/Operator - Reply Ledger.json"
OUT = os.path.join(X, "research", "reply-lane-analysis.md")

SPORTS = ("nba", "nfl", "f1", "fc", "football", "cric", "barca", "liverpool", "arsenal", "chelsea",
          "goal", "sport", "espn", "wnba", "ufc", "box", "wwe", "wrestl", "soccer", "hoops",
          "clutch", "transfer", "fcb", "realmadrid", "mufc", "lfc", "afc", "mlb", "nhl", "tennis",
          "atp", "wta", "formula", "madrid", "eurofoot", "barstool", "kohli", "bumrah", "bcci",
          "nflmemes", "thekhel")
ANIME = ("anime", "genshin", "honkai", "starrail", "zzz", "jjk", "jujutsu", "onepiece", "one_piece",
         "bleach", "naruto", "manga", "shonen", "waifu", "otaku", "hololive", "vtuber", "pokemon",
         "nintendo", "ghibli", "dandadan", "frieren", "sololeveling", "sakamoto", "kaiju")
GAMING = ("gaming", "game", "xbox", "playstation", "ps5", "steam", "valorant", "league", "lol",
          "cs2", "roblox", "minecraft", "fortnite", "cod", "callofduty", "halo", "zelda", "mario",
          "sonic", "tekken", "streetfighter", "capcom", "fromsoft", "elden", "souls", "gta",
          "rivals", "overwatch", "apex", "pubg", "silksong", "hollowknight", "indie", "sajam",
          "ign", "gameinformer", "devolver")
TECH = ("ai", "openai", "anthropic", "claude", "chatgpt", "grok", "llm", "gpt", "nvidia", "apple",
        "iphone", "android", "pixel", "tesla", "spacex", "starlink", "microsoft", "google",
        "meta", "tech", "coding", "dev", "github", "linux", "sama", "kimmonismus", "rowan",
        "polymarket", "markgurman")
MOVIES = ("netflix", "hbo", "movie", "film", "cinema", "trailer", "boxoffice", "marvel", "dc",
          "starwars", "horror", "conjuring", "saw", "hulu", "disney", "amazonprime", "primevideo")
MUSIC = ("music", "spotify", "billboard", "taylor", "drake", "bts", "kpop", "straykids", "aespa",
         "newjeans", "seventeen", "nmixx", "jo1", "shinee", "album", "song", "grammy")


def handle_of(u):
    m = re.search(r"(?:x|twitter)\.com/([^/]+)/", u or "")
    return (m.group(1) if m else "").lower()


def lane_of(h):
    if not h:
        return "unknown"
    for k, lane in ((SPORTS, "sports"), (ANIME, "anime/fandom"), (GAMING, "gaming"),
                    (TECH, "tech/AI"), (MOVIES, "movies/TV"), (MUSIC, "music")):
        if any(t in h for t in k):
            return lane
    return "other"


def load_measures():
    rows = []
    for path in glob.glob(os.path.join(X, "logs", "measures-*.jsonl")):
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def likes_num(s):
    m = re.match(r"([\d,]+)", str(s or "").replace("Like", "").strip())
    return int(m.group(1).replace(",", "")) if m else 0


def main():
    led = json.load(open(LEDGER))
    entries = led if isinstance(led, list) else led.get("entries", [])
    by_url = {}
    by_text = {}
    for e in entries:
        u = e.get("url") or ""
        m = re.search(r"/status/(\d+)", u)
        if m:
            by_url[m.group(1)] = e
        t = (e.get("text") or "").strip()
        if t:
            by_text[t[:60]] = e

    measures = load_measures()
    lanes = defaultdict(list)
    joined = 0
    top = []
    for r in measures:
        link = r.get("link") or ""
        m = re.search(r"/status/(\d+)", link)
        e = by_url.get(m.group(1)) if m else None
        if not e:
            e = by_text.get((r.get("text") or "").strip()[:60])
        parent = (e or {}).get("parent") or ""
        h = handle_of(parent)
        lane = lane_of(h)
        lk = likes_num(r.get("likes"))
        lanes[lane].append((lk, r.get("text", "")[:70], h))
        if e:
            joined += 1
        top.append((lk, lane, h, r.get("text", "")[:70]))

    lines = ["# Reply lane performance (measured)", "",
             f"Source: logs/measures-*.jsonl ({len(measures)} measured replies, scraped 3x/day) "
             f"joined to the ledger by reply URL/text. Likes on OUR replies = how well the reply landed.",
             ""]
    lines.append("| lane | replies measured | avg likes | median | best | share >=5 likes |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for lane, rows in sorted(lanes.items(), key=lambda kv: -(sum(r[0] for r in kv[1]) / max(1, len(kv[1])))):
        lks = sorted(r[0] for r in rows)
        avg = sum(lks) / len(lks)
        med = lks[len(lks) // 2]
        best = lks[-1]
        share5 = 100 * sum(1 for x in lks if x >= 5) / len(lks)
        lines.append("| %s | %d | %.1f | %d | %d | %.0f%% |" % (lane, len(rows), avg, med, best, share5))
    lines.append("")
    lines.append("## Top measured replies")
    lines.append("")
    for lk, lane, h, t in sorted(top, reverse=True)[:12]:
        lines.append(f"- {lk} likes [{lane}] @{h or '?'} — {t}")
    lines.append("")
    lines.append(f"({joined}/{len(measures)} measures joined to ledger entries)")
    text = "\n".join(lines) + "\n"
    open(OUT, "w").write(text)
    print(text)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
