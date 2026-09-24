#!/usr/bin/env python3
"""art_pick_api.py — no-browser art sourcing: Safebooru (safe-only) + Wallhaven (sfw-only).

Pulls character art across the anime/game lanes, ranks by score, downloads the top
pieces per series, screens with nudenet, dedupes by hash + posted registry, and
writes worker/api-candidates.jsonl with tag-derived titles ("Ram | Re:Zero").

Usage: art_pick_api.py [--per-series 2] [--limit 16]
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
BANNED_TAGS = re.compile(r"comic|4koma|multiple_views|text|watermark|sketch_page|animated|video|gif|bikini|swimsuit|swimwear|onsen|hot_spring|hotspring|leotard|garter|lingerie|underwear|panties|lacie|cleavage|underboob|sideboob|see-through|see_through|wet_clothes|wet_shirt|implied_nudity|borderline|questionable|micro_bikini|fundoshi|towel|beach|poolside|gravure|pin-up|pinup", re.I)

SERIES = [
    ("re:zero_kara_hajimeru_isekai_seikatsu", "Re:Zero"),
    ("genshin_impact", "Genshin Impact"),
    ("kaguya-sama_wa_kokurasetai", "Love is War"),
    ("jujutsu_kaisen", "Jujutsu Kaisen"),
    ("kimetsu_no_yaiba", "Demon Slayer"),
    ("chainsaw_man", "Chainsaw Man"),
    ("sousou_no_frieren", "Frieren"),
    ("one_piece", "One Piece"),
    ("bleach", "Bleach"),
    ("spy_x_family", "Spy x Family"),
    ("berserk", "Berserk"),
    ("steins;gate", "Steins;Gate"),
    ("shingeki_no_kyojin", "Attack on Titan"),
    ("vinland_saga", "Vinland Saga"),
    ("elden_ring", "Elden Ring"),
    ("nier_(series)", "NieR"),
    ("persona_5", "Persona 5"),
    ("hollow_knight", "Hollow Knight"),
    ("hades_(game)", "Hades"),
    ("monster_(manga)", "Monster"),
    ("mushishi", "Mushishi"),
    ("serial_experiments_lain", "Serial Experiments Lain"),
    ("solo_leveling", "Solo Leveling"),
    ("dandadan", "Dandadan"),
    ("neon_genesis_evangelion", "Evangelion"),
    # widened: any anime/game, beautiful females (owner 2026-09-24)
    ("honkai:_star_rail", "Honkai: Star Rail"),
    ("genshin_impact", "Genshin Impact"),
    ("zenless_zone_zero", "Zenless Zone Zero"),
    ("wuthering_waves", "Wuthering Waves"),
    ("arknights", "Arknights"),
    ("stellar_blade", "Stellar Blade"),
    ("final_fantasy_vii", "Final Fantasy VII"),
    ("league_of_legends", "League of Legends"),
    ("overwatch", "Overwatch"),
    ("fire_emblem", "Fire Emblem"),
    ("xenoblade_chronicles", "Xenoblade"),
    ("violet_evergarden", "Violet Evergarden"),
    ("kimi_no_na_wa", "Your Name"),
    ("koe_no_katachi", "A Silent Voice"),
    ("oshi_no_ko", "Oshi no Ko"),
    ("bocchi_the_rock", "Bocchi the Rock"),
    ("komi-san_wa_komyushou_desu", "Komi Can't Communicate"),
    ("overlord", "Overlord"),
    ("konosuba", "Konosuba"),
    ("mushoku_tensei", "Mushoku Tensei"),
    ("tensei_shitara_slime_datta_ken", "Slime Isekai"),
    ("cyberpunk:_edgerunners", "Cyberpunk: Edgerunners"),
    ("naruto", "Naruto"),
    ("dragon_ball", "Dragon Ball"),
    ("boku_no_hero_academia", "My Hero Academia"),
    ("sailor_moon", "Sailor Moon"),
    ("cardcaptor_sakura", "Cardcaptor Sakura"),
    ("tokyo_ghoul", "Tokyo Ghoul"),
    ("kimi_ga_nozomu_eien", "Your Lie in April"),
    ("horimiya", "Horimiya"),
    ("k-on!", "K-On!"),
]

CHAR_MAP = [
    (r"ram\b", "Ram", "Re:Zero"), (r"\brem\b", "Rem", "Re:Zero"), (r"emilia", "Emilia", "Re:Zero"),
    (r"reinhard", "Reinhard", "Re:Zero"), (r"beatrice", "Beatrice", "Re:Zero"), (r"subaru", "Subaru", "Re:Zero"),
    (r"furina", "Furina", "Genshin Impact"), (r"mavuika", "Mavuika", "Genshin Impact"),
    (r"raiden", "Raiden Shogun", "Genshin Impact"), (r"nahida", "Nahida", "Genshin Impact"),
    (r"arlecchino", "Arlecchino", "Genshin Impact"), (r"columbina", "Columbina", "Genshin Impact"),
    (r"hu tao", "Hu Tao", "Genshin Impact"), (r"zhongli", "Zhongli", "Genshin Impact"),
    (r"ganyu", "Ganyu", "Genshin Impact"), (r"keqing", "Keqing", "Genshin Impact"),
    (r"kaguya", "Kaguya Shinomiya", "Love is War"), (r"chika", "Chika Fujiwara", "Love is War"),
    (r"gojou|gojo", "Gojo", "Jujutsu Kaisen"), (r"sukuna", "Sukuna", "Jujutsu Kaisen"),
    (r"megumi", "Megumi", "Jujutsu Kaisen"), (r"nobara", "Nobara", "Jujutsu Kaisen"),
    (r"nezuko", "Nezuko", "Demon Slayer"), (r"tanjirou|tanjiro", "Tanjiro", "Demon Slayer"),
    (r"shinobu", "Shinobu", "Demon Slayer"),
    (r"makima", "Makima", "Chainsaw Man"), (r"power\b", "Power", "Chainsaw Man"), (r"denji", "Denji", "Chainsaw Man"),
    (r"frieren", "Frieren", "Frieren"), (r"fern\b", "Fern", "Frieren"),
    (r"luffy", "Luffy", "One Piece"), (r"zoro", "Zoro", "One Piece"), (r"nami", "Nami", "One Piece"),
    (r"rukia", "Rukia", "Bleach"), (r"ichigo", "Ichigo", "Bleach"),
    (r"yor\b", "Yor Forger", "Spy x Family"), (r"anya", "Anya", "Spy x Family"),
    (r"guts", "Guts", "Berserk"), (r"griffith", "Griffith", "Berserk"),
    (r"kurisu", "Kurisu Makise", "Steins;Gate"), (r"mikasa", "Mikasa", "Attack on Titan"),
    (r"levi\b", "Levi", "Attack on Titan"), (r"eren", "Eren Yeager", "Attack on Titan"),
    (r"thorfinn", "Thorfinn", "Vinland Saga"), (r"melina", "Melina", "Elden Ring"),
    (r"malenia", "Malenia", "Elden Ring"), (r"ranni", "Ranni", "Elden Ring"),
    (r"2b\b", "2B", "NieR"), (r"nier", "2B", "NieR"),
    (r"makoto|queen\b", "Makoto Niijima", "Persona 5"), (r"joker\b", "Joker", "Persona 5"),
    (r"hornet", "Hornet", "Hollow Knight"), (r"zagreus", "Zagreus", "Hades"),
    (r"lain\b", "Lain", "Serial Experiments Lain"), (r"ging", "Ging", "Monster"),
    (r"sung jin", "Sung Jinwoo", "Solo Leveling"), (r"cha hae", "Cha Hae-In", "Solo Leveling"),
    (r"momo\b", "Momo", "Dandadan"), (r"okarun", "Okarun", "Dandadan"),
    (r"rei\b", "Rei Ayanami", "Evangelion"), (r"asuka", "Asuka", "Evangelion"),
]


def title_from_tags(tags):
    s = tags.replace("_", " ").lower()
    for pat, name, series in CHAR_MAP:
        if re.search(pat, s):
            return f"{name} | {series}" if series else name
    return ""


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def posted_hashes():
    h = set()
    reg = "worker/aesthetic-posted.jsonl"
    if os.path.exists(reg):
        for line in open(reg):
            try:
                if line.strip():
                    h.add(json.loads(line)["sha256"])
            except Exception:
                pass
    return h


def screen(data):
    """Fail-closed nudenet screen; returns True when the image is clean."""
    try:
        from nudenet import NudeDetector
        det = NudeDetector()
        open("/tmp/_screen.jpg", "wb").write(data)
        res = det.detect("/tmp/_screen.jpg")
        for r in res:
            cls = r.get("class", "")
            sc = float(r.get("score", 0))
            if sc < 0.30:
                continue
            if cls in ("FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED", "MALE_GENITALIA_EXPOSED",
                       "BUTTOCKS_EXPOSED", "ANUS_EXPOSED", "FEMALE_BREAST_EXPOSED_THROUGH_CLOTHING"):
                return False
    except Exception as e:
        print("screen err (fail closed):", str(e)[:60], file=sys.stderr)
        return False
    return True


def main():
    argv = sys.argv[1:]
    per_series = 2
    limit = 16
    if "--per-series" in argv:
        per_series = int(argv[argv.index("--per-series") + 1])
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    have = posted_hashes()
    import random as _r
    _r.shuffle(SERIES)  # spread pulls across all 56 lanes
    os.makedirs("images/aesthetic", exist_ok=True)
    out = []
    n = 0
    for tag, series in SERIES:
        if n >= limit:
            break
        posts = []
        for extra in (" 1girl solo", " 1girl", ""):
            try:
                url = ("https://safebooru.org/index.php?page=dapi&s=post&q=index" +
                       "&tags=" + urllib.parse.quote(tag + " rating:safe" + extra) + "&limit=80")
                xml = fetch(url)
                posts = ET.fromstring(xml).findall("post")
                if len(posts) >= 20:
                    break
            except Exception as e:
                print("skip", tag, extra, str(e)[:50], file=sys.stderr)
                continue
        if not posts:
            continue
        rows = []
        for p in posts:
            try:
                w = int(p.get("width") or 0)
                h = int(p.get("height") or 0)
                tg = p.get("tags") or ""
                if w < 800 or h < 600 or w > 6000:
                    continue
                if BANNED_TAGS.search(tg):
                    continue
                if "1boy" in tg and "1girl" not in tg:
                    continue  # female-forward
                if "cosplay" in tg or "photo" in tg or "realistic" in tg:
                    continue
                rows.append({"score": int(p.get("score") or 0), "url": p.get("file_url"), "tags": tg,
                             "w": w, "h": h, "id": p.get("id")})
            except Exception:
                continue
        rows.sort(key=lambda r: -r["score"])
        got = 0
        for r in rows:
            if got >= per_series or n >= limit:
                break
            try:
                data = fetch(r["url"], timeout=45)
                if len(data) < 40000:
                    continue
                hh = hashlib.sha256(data).hexdigest()
                if hh in have:
                    continue
                if not screen(data):
                    continue
                have.add(hh)
                fn = f"api-{tag[:18].replace(':', '').replace('_', '')}-{r['id']}.jpg"
                path = "images/aesthetic/" + fn
                open(path, "wb").write(data)
                title = title_from_tags(r["tags"])
                out.append({"image": path, "tag": "", "text": title, "source": "safebooru",
                            "author": "", "url": "https://safebooru.org/index.php?page=post&s=view&id=" + str(r["id"]),
                            "series": series, "score": r["score"], "title": title})
                got += 1
                n += 1
                time.sleep(1.2)
            except Exception as e:
                print("dl fail", str(e)[:60], file=sys.stderr)
                continue
        print(f"{series}: +{got} (queue {n})", flush=True)

    with open("worker/api-candidates.jsonl", "w") as fh:
        for e in out:
            fh.write(json.dumps(e) + "\n")
    print(f"DONE {len(out)} candidates -> worker/api-candidates.jsonl")


if __name__ == "__main__":
    main()
