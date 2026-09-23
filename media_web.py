#!/usr/bin/env python3
"""Web image hunt via Bing Images (through the rig) + direct download.

Usage: media_web.py "<query>" [--n 3] [--slug custom-slug]
Searches Bing Images, extracts original media URLs (murl), downloads top N that pass
validation (real image, min 500px short side, max 4MB), saves to media/posts/<slug>-<i>.jpg.
Prints saved paths.
"""
import asyncio, io, json, os, re, sys, urllib.parse, urllib.request
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

OUTDIR = "/home/ubuntu/x-op/media/posts"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

JS = r"""JSON.stringify((()=>{
  const html = document.documentElement.innerHTML;
  const murls = [...html.matchAll(/murl&quot;:&quot;(.*?)&quot;/g)].map(m=>m[1]);
  const seen=[...new Set(murls)];
  return seen.slice(0,30);
})())"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


def slugify(q):
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:40]


def download(url, slug, idx):
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=40).read()
    if len(data) > 4_000_000:
        return None, "too big"
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if min(im.size) < 500:
        return None, f"small {im.size}"
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)))
    os.makedirs(OUTDIR, exist_ok=True)
    p = os.path.join(OUTDIR, f"{slug}-{idx}.jpg")
    im.save(p, "JPEG", quality=88)
    return p, None


async def hunt(query, n=3, slug=None):
    slug = slug or slugify(query)
    async with streamable_http_client("http://127.0.0.1:8932/mcp") as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "about:blank"}))
            page = np.get("page_id") or np.get("id")
            nav = "https://www.bing.com/images/search?q=" + urllib.parse.quote(query)
            await call(s, "cloak_navigate", {"page_id": page, "url": nav})
            await asyncio.sleep(4.5)
            r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS})
            try:
                urls = json.loads(json.loads(r3).get("result", "[]"))
            except Exception:
                urls = []
            await call(s, "cloak_close_page", {"page_id": page})
    print(f"bing: {len(urls)} candidates for {query!r}")
    out = []
    for u in urls:
        if len(out) >= n:
            break
        try:
            p, err = download(u, slug, len(out) + 1)
        except Exception as ex:
            p, err = None, str(ex)[:50]
        if p:
            out.append({"path": p, "src": u})
            print(f"OK  {p}  <- {u[:100]}")
        else:
            print(f"x   {u[:80]} -> {err}")
    return out


def main():
    query = sys.argv[1]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 3
    slug = sys.argv[sys.argv.index("--slug") + 1] if "--slug" in sys.argv else None
    res = asyncio.run(hunt(query, n, slug))
    json.dump(res, open("/tmp/media-web-last.json", "w"), indent=1)
    print(f"\n{len(res)} images saved")


if __name__ == "__main__":
    main()
