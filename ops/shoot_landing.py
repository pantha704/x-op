#!/usr/bin/env python3
"""Clean landing-page screenshot for a utility post (no annotations).
Usage: shoot_landing.py <name> <url>
Saves /home/ubuntu/x-op/media/util-shots/<name>.jpg (1440x900 viewport, JPEG q85).
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
from PIL import Image

OUT = '/home/ubuntu/x-op/media/util-shots'
CHROME = "/home/ubuntu/.cloakbrowser/chromium-146.0.7680.177.5/chrome"

CONSENT_JS = r"""(() => {
  const btns = [...document.querySelectorAll('button, [role="button"], a')];
  const hit = btns.find(b => /^(accept|accept all|agree|got it|ok|allow all|i agree)/i.test((b.innerText||'').trim()));
  if (hit) { hit.click(); return 'clicked'; }
  return 'none';
})()"""

async def main():
    name, url = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME, headless=True,
                                          args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            locale="en-US")
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3.5)
        try:
            await page.evaluate(CONSENT_JS)
            await asyncio.sleep(1.2)
        except Exception:
            pass
        raw = f"{OUT}/{name}.png"
        await page.screenshot(path=raw)
        im = Image.open(raw).convert("RGB")
        im.save(f"{OUT}/{name}.jpg", "JPEG", quality=85)
        os.remove(raw)
        await browser.close()
        print(f"saved {OUT}/{name}.jpg {im.size}")

asyncio.run(main())
