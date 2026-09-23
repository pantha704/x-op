#!/usr/bin/env python3
"""Attach media to EXISTING X drafts over CDP (Chrome :9222), then re-save.
Why: the rig MCP has no file-upload tool, and X's composer no longer exposes
[data-testid="attachments"]. Playwright's set_input_files is the reliable route.

Usage: post_attach_media.py <pairs.json>
pairs.json: [{"snippet": "start of draft text", "media": "/abs/path.jpg"}, ...]
Prints per-item: OK / FAIL reason. Never posts anything (saves drafts only).
"""
import asyncio, json, sys
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"

async def open_drafts(page):
    await page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    link = page.locator("text=/^Drafts$/i").first
    if await link.count():
        await link.click()
        await page.wait_for_timeout(2500)
    return await page.locator('[data-testid="unsentTweet"]').count()

async def main():
    pairs = json.load(open(sys.argv[1]))
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        page = await ctx.new_page()          # our own tab - never touch the worker's pages
        try:
            n = await open_drafts(page)
            print("drafts visible:", n)
            for it in pairs:
                snip, media = it["snippet"], it["media"]
                try:
                    item = page.locator('[data-testid="unsentTweet"]', has_text=snip).first
                    if not await item.count():
                        print("FAIL open:", snip[:40], "(not found)"); continue
                    await item.click()
                    await page.wait_for_timeout(2500)
                    # composer open with content?
                    ed = page.locator('[data-testid="tweetTextarea_0"]')
                    if not await ed.count():
                        print("FAIL composer:", snip[:40]); continue
                    inputs = page.locator('input[type="file"]')
                    cnt = await inputs.count()
                    attached = False
                    for i in range(cnt):
                        try:
                            await inputs.nth(i).set_input_files(media)
                            await page.wait_for_timeout(1500)
                            # media preview present?
                            for _ in range(20):
                                prevs = await page.locator('[data-testid="tweetPhoto"], [data-testid="attachments"], img[src^="blob:"]').count()
                                if prevs > 0:
                                    attached = True; break
                                await page.wait_for_timeout(1000)
                            if attached: break
                        except Exception as e:
                            err = str(e)[:80]
                    if not attached:
                        print("FAIL attach:", snip[:40]); continue
                    # wait for processing bar to clear
                    for _ in range(20):
                        bar = await page.locator('[role="progressbar"]').count()
                        if bar == 0: break
                        await page.wait_for_timeout(1000)
                    await page.wait_for_timeout(1500)
                    # close -> save
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(1200)
                    conf = page.locator('[data-testid="confirmationSheetConfirm"]')
                    if await conf.count():
                        await conf.first.click()
                    else:
                        sal = page.locator('[role="button"]:has-text("Save"), button:has-text("Save")')
                        if await sal.count():
                            await sal.first.click()
                    await page.wait_for_timeout(2000)
                    print("OK updated:", snip[:45])
                    # back to drafts list for the next one
                    try:
                        await open_drafts(page)
                    except Exception:
                        pass
                except Exception as e:
                    print("FAIL item:", snip[:40], str(e)[:110])
            # final verify
            await open_drafts(page)
            items = await page.locator('[data-testid="unsentTweet"]').all()
            print("=== final drafts check (media counts):")
            for el in items[:8]:
                try:
                    txt = (await el.inner_text()).replace("\n", " ")[:58]
                    m = await el.locator('img[src*="pbs.twimg.com/media"], img[src^="blob:"]').count()
                    print("  media=%d | %s" % (m, txt))
                except Exception:
                    break
        finally:
            await page.close()

asyncio.run(main())
