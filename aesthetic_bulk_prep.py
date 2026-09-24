#!/usr/bin/env python3
"""Bulk prep for the aesthetic batch: run picker passes until `target` unique
candidates are collected, dedupe (by image url + one-per-author), skip everything
already posted, download the images, emit the manifest for aesthetic_bulk_post.py.

Usage: aesthetic_bulk_prep.py [--target 100] [--passes 6] [--min-likes 120]
"""
import json
import os
import subprocess
import sys
import urllib.request

argv = sys.argv[1:]
def opt(name, default):
    return int(argv[argv.index(name) + 1]) if name in argv else default

target = opt("--target", 100)
max_passes = opt("--passes", 6)
min_likes = opt("--min-likes", 120)



import re

# Context line rule (owner 2026-09-24): a few words of context - JUST the name of
# the anime / game / character / quest. No sentences, nothing extra.
FRANCHISES = [
    (r'stories ?of ?frost ?snow', "Genshin: Stories of Frost and Snow"),
    (r'\bvesna\b', "Genshin: Vesna"),
    (r'\bmavuika\b', "Genshin: Mavuika"),
    (r'genshin', "Genshin Impact"),
    (r're:?\s?zero', "Re:Zero"),
    (r'kaguya|love ?is ?war', "Love is War"),
    (r'fullmetal ?alchemist|\bfma\b|\bfmab\b', "Fullmetal Alchemist"),
    (r'elfen ?lied', "Elfen Lied"),
    (r'attack ?on ?titan|shingeki', "Attack on Titan"),
    (r'vinland ?saga', "Vinland Saga"),
    (r'death ?note', "Death Note"),
    (r'nightreign', "Elden Ring: Nightreign"),
    (r'elden ?ring', "Elden Ring"),
    (r'red ?dead|rdr2', "Red Dead Redemption 2"),
    (r'resident evil', "Resident Evil"),
    (r'cyberpunk|edgerunners', "Cyberpunk"),
    (r'\bzelda\b', "Zelda"),
    (r'\bminecraft\b', "Minecraft"),
    (r'\bpersona\b', "Persona"),
    (r'\bfrieren\b', "Frieren"),
    (r'jujutsu ?kaisen|\bjjk\b', "Jujutsu Kaisen"),
    (r'one ?piece', "One Piece"),
    (r'demon ?slayer|kimetsu', "Demon Slayer"),
    (r'chainsaw ?man', "Chainsaw Man"),
    (r'solo ?leveling', "Solo Leveling"),
    (r'studio ghibli|ghibli', "Ghibli"),
]

CHARACTERS = [
    (r'kaguya shinomiya', "Kaguya Shinomiya", "Love is War"), (r'chika fujiwara', "Chika Fujiwara", "Love is War"),
    (r'\bram\b', "Ram", "Re:Zero"), (r'\brem\b', "Rem", "Re:Zero"), (r'\bemilia\b', "Emilia", "Re:Zero"),
    (r'\bsubaru\b', "Subaru Natsuki", "Re:Zero"), (r'\bbeatrice\b', "Beatrice", "Re:Zero"),
    (r'\bmelina\b', "Melina", "Elden Ring"), (r'\bmalenia\b', "Malenia", "Elden Ring"),
    (r'heolstor', "Heolstor", "Elden Ring: Nightreign"), (r'soul of cinder', "Soul of Cinder", "Dark Souls III"),
    (r'\bmiquella\b', "Miquella", "Elden Ring"), (r'\bradahn\b', "Radahn", "Elden Ring"),
    (r'\brebecca\b', "Rebecca", "Cyberpunk: Edgerunners"), (r'\bdavid\b', "David Martinez", "Cyberpunk: Edgerunners"),
    (r'\blucy\b', "Lucy", ""),
    (r'\bfurina\b', "Furina", "Genshin Impact"), (r'\bmavuika\b', "Mavuika", "Genshin Impact"),
    (r'raiden shogun', "Raiden Shogun", "Genshin Impact"), (r'\bnahida\b', "Nahida", "Genshin Impact"),
    (r'\barlecchino\b', "Arlecchino", "Genshin Impact"), (r'\bcolumbina\b', "Columbina", "Genshin Impact"),
    (r'\btsaritsa\b', "The Tsaritsa", "Genshin Impact"), (r'\bventi\b', "Venti", "Genshin Impact"),
    (r'\bzhongli\b', "Zhongli", "Genshin Impact"), (r'\bhu tao\b', "Hu Tao", "Genshin Impact"),
    (r'\bskirk\b', "Skirk", "Genshin Impact"),
    (r'\bmakima\b', "Makima", "Chainsaw Man"), (r'\bdenji\b', "Denji", "Chainsaw Man"),
    (r'\bgojo\b', "Gojo", "Jujutsu Kaisen"), (r'\bsukuna\b', "Sukuna", "Jujutsu Kaisen"),
    (r'\byuji\b', "Yuji Itadori", "Jujutsu Kaisen"),
    (r'\bthorfinn\b', "Thorfinn", "Vinland Saga"), (r'\baskeladd\b', "Askeladd", "Vinland Saga"),
    (r'\bcanute\b', "Canute", "Vinland Saga"),
    (r'\beren\b', "Eren Yeager", "Attack on Titan"), (r'\blevi\b', "Levi", "Attack on Titan"),
    (r'\bmikasa\b', "Mikasa", "Attack on Titan"),
    (r'\barthur morgan\b', "Arthur Morgan", "Red Dead Redemption 2"), (r'\bdutch\b', "Dutch van der Linde", "Red Dead Redemption 2"),
    (r'\bsylphiette\b', "Sylphiette", "Mushoku Tensei"), (r'\broxy\b', "Roxy", "Mushoku Tensei"),
    (r'\bfrieren\b', "Frieren", "Frieren"),
    (r'\bguts\b', "Guts", "Berserk"), (r'\bgriffith\b', "Griffith", "Berserk"),
]

def context_name(text, author=""):
    """Title rule (owner 2026-09-24): "Character | Series" when a character is known,
    else the specific title, else the series alone."""
    src = (text or "").lower()
    for pat, name, series in CHARACTERS:
        if re.search(pat, src):
            return f"{name} | {series}" if series else name
    for pat, name in FRANCHISES:
        if re.search(pat, src):
            return name
    return ""

ROOM_TEXT = re.compile(r'\b(my little room|my room|bedroom|kitchen|living room|interior|desk setup|room tour|apartment)\b', re.I)

def run_picker():
    r = subprocess.run(["./venv/bin/python", "aesthetic_pick.py", "--limit", "70", "--min-likes", str(min_likes)],
                       capture_output=True, text=True, timeout=1200)
    try:
        return json.loads(r.stdout)
    except Exception:
        print("picker parse fail; stderr tail:", (r.stderr or "")[-300:], flush=True)
        return []


def posted_sets():
    imgs, authors = set(), set()
    if os.path.isdir("logs"):
        for fn in os.listdir("logs"):
            if fn.startswith("aesthetic-") and fn.endswith(".jsonl"):
                for line in open("logs/" + fn):
                    try:
                        e = json.loads(line)
                    except Exception:
                        continue
                    if e.get("image"):
                        imgs.add(os.path.basename(e["image"]))
                    if e.get("tag"):
                        authors.add(e["tag"].lstrip("@").lower())
    return imgs, authors


def main():
    seen_imgs = set()
    picked = []
    seen_authors, posted_authors = posted_sets()
    for p in range(max_passes):
        rows = run_picker()
        added = 0
        for r in rows:
            img = r.get("img") or ""
            a = (r.get("author") or "").lower()
            if not img or img in seen_imgs:
                continue
            if a and (a in seen_authors or a in posted_authors):
                continue
            if ROOM_TEXT.search(r.get("text") or ""):
                continue
            seen_imgs.add(img)
            if a:
                seen_authors.add(a)
            picked.append(r)
            added += 1
        print(f"pass {p+1}: +{added} (unique so far {len(picked)})", flush=True)
        if len(picked) >= target:
            break

    picked = picked[:target]
    os.makedirs("images/aesthetic", exist_ok=True)
    manifest = []
    for i, r in enumerate(picked):
        dest = f"images/aesthetic/bulk-{i:03d}.jpg"
        try:
            req = urllib.request.Request(r["img"], headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=30).read()
            if len(data) < 15000:
                raise Exception(f"too small: {len(data)}")
            import hashlib as _h
            _hh = _h.sha256(data).hexdigest()
            if os.path.exists("worker/aesthetic-posted.jsonl"):
                _dup = False
                for _l in open("worker/aesthetic-posted.jsonl"):
                    try:
                        if _l.strip() and json.loads(_l).get("sha256") == _hh:
                            _dup = True
                            break
                    except Exception:
                        pass
                if _dup:
                    print("skip dup (already posted):", r["img"][:70], flush=True)
                    continue
            open(dest, "wb").write(data)
        except Exception as e:
            print("dl fail:", r["img"][:70], str(e)[:70], flush=True)
            continue
        manifest.append({
            "image": dest,
            "tag": ("@" + r["author"]) if r.get("author") else "",
            "text": context_name(r.get("text") or "", r.get("author") or ""),
            "source": r.get("source", "x"),
            "author": r.get("author", ""),
            "url": r.get("tweet_url", ""),
            "likes": r.get("likes", 0),
        })
    with open("worker/aesthetic-bulk-manifest.jsonl", "w") as fh:
        for m in manifest:
            fh.write(json.dumps(m) + "\n")
    print(f"MANIFEST {len(manifest)} entries -> worker/aesthetic-bulk-manifest.jsonl", flush=True)


if __name__ == "__main__":
    main()
