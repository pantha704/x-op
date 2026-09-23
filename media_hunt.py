#!/usr/bin/env python3
"""Media hunter for the post feed (owner directive 2026-09-21: photos from anywhere - Pinterest, Reddit, raw internet).

Sources:
  reddit   - public JSON (no login). search or subreddit top-of-day.
  pinterest- public search page scraped via the live rig (MCP :8932).

Usage:
  media_hunt.py reddit "<query>" [--sub anime] [--n 6] [--min-score 200]
  media_hunt.py pinterest "<query>" [--n 12]
Saves validated images to /home/ubuntu/x-op/media/posts/ and prints paths + source URLs.
"""
import asyncio, io, json, os, re, sys, urllib.parse, urllib.request

OUTDIR = "/home/ubuntu/x-op/media/posts"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def slugify(q):
    return re.sub(r'[^a-z0-9]+', '-', q.lower()).strip('-')[:40]


def save_image(url, slug, idx):
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=45).read()
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if min(im.size) < 400:
        return None, f"tiny {im.size}"
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)))
    os.makedirs(OUTDIR, exist_ok=True)
    p = os.path.join(OUTDIR, f"{slug}-{idx}.jpg")
    im.save(p, "JPEG", quality=88)
    return p, None


def reddit(query, sub=None, n=6, min_score=200):
    """Reddit via redlib mirror (safereddit) - the mirror proxies images so no IP block, no login."""
    import html as _html
    base = "https://safereddit.com"
    if sub:
        url = f"{base}/r/{sub}/top/?t=day"
    else:
        url = f"{base}/search?q=" + urllib.parse.quote(query) + "&sort=top&t=day"
    req = urllib.request.Request(url, headers=UA)
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    imgs = re.findall(r'<img[^>]*alt="Post image"[^>]*src="([^"]+)"', page)
    imgs += re.findall(r'<img[^>]*src="([^"]+)"[^>]*alt="Post image"', page)
    out = []
    seen = set()
    for i, src in enumerate(imgs):
        src = _html.unescape(src)
        if src.startswith("/"):
            src = base + src
        if src in seen:
            continue
        seen.add(src)
        try:
            path, err = save_image(src, slugify(query or sub), len(out) + 1)
        except Exception as ex:
            path, err = None, str(ex)[:60]
        if path:
            out.append({"path": path, "src": src})
            print(f"OK  {path}  {src[:90]}")
        else:
            print(f"x   {src[:80]} -> {err}")
        if len(out) >= n:
            break
    return out


async def pinterest(query, n=12):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    URL = "http://127.0.0.1:8932/mcp"
    JS = "JSON.stringify([...document.querySelectorAll('img')].map(i=>i.src).filter(s=>s&&s.includes('pinimg.com')&&!s.includes('75x75')).slice(0,40))"

    async def call(s, name, args=None):
        res = await s.call_tool(name, args or {})
        return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

    urls = []
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            lp = await call(s, "cloak_list_pages", {})
            pages = json.loads(lp).get("pages", [])
            try:
                np = json.loads(await call(s, "cloak_new_page", {"url": "about:blank"}))
                page = np.get("page_id") or np.get("id")
            except Exception:
                page = None
            if not page:
                page = pages[0]["page_id"] if pages else json.loads(await call(s, "cloak_launch", {"user_data_dir": "/home/ubuntu/.cloakbrowser/profiles/operator"})).get("page_id")
            nav = "https://www.pinterest.com/search/pins/?q=" + urllib.parse.quote(query)
            await call(s, "cloak_navigate", {"page_id": page, "url": nav})
            await asyncio.sleep(4)
            for _ in range(2):
                r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
                try:
                    urls += json.loads(json.loads(r3).get("result", "[]"))
                except Exception:
                    pass
                await call(s, "cloak_evaluate", {"page_id": page, "expression": "window.scrollBy(0, 1200)"})
                await asyncio.sleep(2)
    # upscale thumbs to originals when possible
    fixed = []
    for u in urls:
        u2 = re.sub(r"/(\d+x\d*|\d+x)/", "/originals/", u)
        fixed.append(u2)
    seen, out = set(), []
    for i, u in enumerate(fixed):
        if u in seen: continue
        seen.add(u)
        try:
            path, err = save_image(u, slugify(query) + "-pin", len(out) + 1)
        except Exception as ex:
            path, err = None, str(ex)[:50]
        if path:
            out.append({"path": path, "src": u})
            print(f"OK  {path}  {u[:90]}")
        if len(out) >= n:
            break
    return out


def main():
    mode = sys.argv[1]
    query = sys.argv[2]
    if mode == "reddit":
        sub = None; n = 6; min_score = 200
        if "--sub" in sys.argv: sub = sys.argv[sys.argv.index("--sub") + 1]
        if "--n" in sys.argv: n = int(sys.argv[sys.argv.index("--n") + 1])
        if "--min-score" in sys.argv: min_score = int(sys.argv[sys.argv.index("--min-score") + 1])
        res = reddit(query, sub, n, min_score)
    elif mode == "pinterest":
        n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 12
        res = asyncio.run(pinterest(query, n))
    else:
        print("mode must be reddit|pinterest"); sys.exit(2)
    json.dump(res, open("/tmp/media-hunt-last.json", "w"), indent=1)
    print(f"\n{len(res)} images saved -> {OUTDIR}")


if __name__ == "__main__":
    main()
