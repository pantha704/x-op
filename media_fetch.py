#!/usr/bin/env python3
"""Fetch + normalize a post image (owner directive 2026-09-21: photos from anywhere - his Pinterest or raw internet).

Usage: media_fetch.py <image-url> <slug>
Saves /home/ubuntu/x-op/media/posts/<slug>.jpg (normalized: jpeg, max width 1600, quality 88).
Validates: real image, min 400px on the short side, no tiny thumbnails.
Prints the saved path on success; exits 1 otherwise.
"""
import io, os, sys, urllib.request

OUTDIR = "/home/ubuntu/x-op/media/posts"

def main():
    url, slug = sys.argv[1], sys.argv[2]
    os.makedirs(OUTDIR, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"})
    data = urllib.request.urlopen(req, timeout=45).read()
    try:
        from PIL import Image
    except Exception:
        p = os.path.join(OUTDIR, slug + ".jpg")
        open(p, "wb").write(data)
        print(p)
        return
    im = Image.open(io.BytesIO(data))
    if min(im.size) < 400:
        print(f"REJECT tiny image {im.size}"); sys.exit(1)
    im = im.convert("RGB")
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)))
    p = os.path.join(OUTDIR, slug + ".jpg")
    im.save(p, "JPEG", quality=88)
    print(p)

if __name__ == "__main__":
    main()
