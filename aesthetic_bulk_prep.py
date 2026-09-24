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
    (r'kaguya shinomiya', "Kaguya Shinomiya"), (r'chika fujiwara', "Chika Fujiwara"),
    (r'\bmelina\b', "Melina"), (r'\bmalenia\b', "Malenia"), (r'heolstor', "Heolstor"),
    (r'soul of cinder', "Soul of Cinder"), (r'\bmiquella\b', "Miquella"), (r'\bradahn\b', "Radahn"),
    (r'\bfurina\b', "Furina"), (r'\bmavuika\b', "Mavuika"), (r'raiden shogun', "Raiden Shogun"),
    (r'\bnahida\b', "Nahida"), (r'\barlecchino\b', "Arlecchino"), (r'\bcolumbina\b', "Columbina"),
    (r'\btsaritsa\b', "The Tsaritsa"), (r'\bventi\b', "Venti"), (r'\bzhongli\b', "Zhongli"),
    (r'\bhu tao\b', "Hu Tao"), (r'\bfurina\b', "Furina"), (r'\bkazuha\b', "Kazuha"),
    (r'\bsubaru\b', "Subaru Natsuki"), (r'\brem\b', "Rem"), (r'\bemilia\b', "Emilia"),
    (r'\brebecca\b', "Rebecca"), (r'\blucy\b', "Lucy"), (r'\bdavid\b', "David Martinez"),
    (r'\bmakima\b', "Makima"), (r'\bpower\b', "Power"), (r'\bdenji\b', "Denji"),
    (r'\bgojo\b', "Gojo"), (r'\bsukuna\b', "Sukuna"), (r'\byuji\b', "Yuji Itadori"),
    (r'\bthorfinn\b', "Thorfinn"), (r'\baskeladd\b', "Askeladd"), (r'\bcanute\b', "Canute"),
    (r'\beren\b', "Eren Yeager"), (r'\blevi\b', "Levi"), (r'\bmikasa\b', "Mikasa"),
    (r'\blight yagami\b|\bkira\b', "Light Yagami"), (r'\blelouch\b', "Lelouch"),
    (r'\barthur morgan\b', "Arthur Morgan"), (r'\bdutch\b', "Dutch van der Linde"),
    (r'\bsylphiette\b', "Sylphiette"), (r'\broxy\b', "Roxy"),
    (r'\bfrieren\b', "Frieren"), (r'\bfemto\b', "Femto"),
]

def context_name(text, author=""):
    """A few-word name-only context: character first, then specific title, then series."""
    src = (text or "").lower()
    for pat, name in CHARACTERS:
        if re.search(pat, src):
            return name
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
