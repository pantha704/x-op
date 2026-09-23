#!/usr/bin/env python3
"""Fire a batch of X replies via the local cloakbrowsermcp server (:8932).

Usage:
    /home/ubuntu/x-op/venv/bin/python fire_driver.py targets.json [--max 6] [--gap-min 20] [--gap-max 45]

targets.json: [{"url": "...", "text": "...", "lang": "en", "tags": ["take"]}, ...]

Per target: navigate -> jittered wait -> in-page JS (like + type + reply + verify).
Outcomes: hit / THROTTLED / uncertain / no-article / no-box / no-btn / error.
On THROTTLED: stop immediately (throttle protocol: caller cools down).
Logs one JSONL line per attempt to ~/x-op/logs/fire-<ts>.jsonl, prints a summary.

Bible rules baked in: like-before-reply, no dashes in text, verify-composer-cleared.
"""
import asyncio
import json
import os
import random
import sys
import time
import traceback

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"
OUT = os.path.expanduser("~/x-op")
PROFILE = "/home/ubuntu/.cloakbrowser/profiles/operator"

RESTRICTED_FILE = os.path.expanduser("~/x-op/targets/restricted-urls.json")


def split_outcome(raw):
    """('no-box', diag) for 'no-box|<json>'; (raw, None) otherwise."""
    if isinstance(raw, str) and raw.startswith("no-box|"):
        try:
            return "no-box", json.loads(raw[len("no-box|"):])
        except Exception:
            return "no-box", {"raw": raw[:160]}
    return raw, None


def note_restricted(url, diag):
    """Persist restricted URLs so harvests/filters can drop them."""
    try:
        cur = json.load(open(RESTRICTED_FILE)) if os.path.exists(RESTRICTED_FILE) else {}
    except Exception:
        cur = {}
    cur[url] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "diag": diag}
    tmp = RESTRICTED_FILE + ".tmp"
    json.dump(cur, open(tmp, "w"), indent=1, ensure_ascii=False)
    os.replace(tmp, RESTRICTED_FILE)

JS_TEMPLATE = r"""(async () => {
  const sleep = ms => new Promise(res => setTimeout(res, ms));
  const a = document.querySelector('article[data-testid="tweet"]');
  if (!a) return 'no-article';

  // X mounts composers as [data-testid^="tweetTextarea_"]; prefer the modal one, else the last mounted.
  const findBox = () => {
    const all = [...document.querySelectorAll('[data-testid^="tweetTextarea_"]')];
    if (!all.length) return null;
    const dlg = all.filter(b => b.closest('[role="dialog"]'));
    return dlg.length ? dlg[dlg.length - 1] : all[all.length - 1];
  };
  const waitBox = async (ms, step = 400) => {
    for (let t = 0; t < ms; t += step) { const b = findBox(); if (b) return b; await sleep(step); }
    return findBox();
  };
  const clickReply = () => { const rb = a.querySelector('[data-testid="reply"]'); if (rb) { rb.click(); return true; } return false; };

  let likedNow = false;
  if (!a.querySelector('[data-testid="unlike"]')) { const l = a.querySelector('[data-testid="like"]'); if (l) { l.click(); likedNow = true; } }
  await sleep(400);

  let box = await waitBox(2500);                        // replyable detail pages mount the composer unclicked
  let clicked = false;
  if (!box) {
    clicked = clickReply();
    box = await waitBox(8000);                          // was: a single 1200ms probe
    if (!box && clicked) { clickReply(); box = await waitBox(4000); }   // one retry: hydration can swallow the click
  }

  if (!box) {
    const txt = document.body.innerText || '';
    const probes = [
      /who can (?:reply|respond)[^\n]{0,120}/i,
      /people @[A-Za-z0-9_]+ follows?[^\n]{0,80}/i,
      /only (?:accounts?|people|verified)[^\n]{0,80}/i,
      /verified accounts[^\n]{0,80}/i,
      /accounts? (?:they|you) (?:follow|mentioned)[^\n]{0,80}/i,
      /not allowed to reply[^\n]{0,80}/i,
      /repl(?:y|ies) (?:are )?(?:limited|restricted|turned off|disabled)[^\n]{0,80}/i
    ];
    const evidence = [];
    for (const re of probes) { const m = txt.match(re); if (m) evidence.push(m[0].trim().slice(0, 120)); }
    const rb = a.querySelector('[data-testid="reply"]');
    const diag = {
      evidence,                                         // empty => probably slow render, not a lock
      replyBtnPresent: !!rb,
      replyBtnAriaDisabled: rb ? (rb.getAttribute('aria-disabled') || rb.disabled || false) : null,
      replyClicks: clicked ? 1 : 0,
      composerNodes: document.querySelectorAll('[data-testid^="tweetTextarea_"]').length,
      dialogOpen: !!document.querySelector('[role="dialog"]'),
      articleChars: a.innerText.length
    };
    // optional (see 6.3): revert our like if we cannot reply
    if (likedNow) { const u = a.querySelector('[data-testid="unlike"]'); if (u) u.click(); }
    return 'no-box|' + JSON.stringify(diag);
  }

  box.focus();
  document.execCommand('insertText', false, __TEXT__);
  await sleep(450);
  const btns = [...document.querySelectorAll('button')].filter(b => (b.innerText||'').trim() === 'Reply' && !b.disabled);
  const btn = btns[btns.length - 1];
  if (!btn) return 'no-btn';
  btn.click();
  await sleep(3000);
  const errToast = /Something went wrong/i.test(document.body.textContent||'');
  const boxNow = findBox();
  const cleared = !boxNow || !boxNow.textContent.trim();
  if (errToast) return 'THROTTLED';
  return cleared ? 'hit' : 'uncertain';
})()"""


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    parts = [getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])]
    return "\n".join(parts)


async def pick_page(s):
    r = await call(s, "cloak_list_pages", {})
    try:
        pages = json.loads(r).get("pages", [])
    except Exception:
        pages = []
    if pages:
        return pages[0]["page_id"]
    r = await call(s, "cloak_launch", {"user_data_dir": PROFILE})
    try:
        return json.loads(r).get("page_id")
    except Exception:
        return None


async def check_posted(s, page, text):
    """False-positive guard: confirm whether a reply actually landed after a THROTTLED signal."""
    await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/your_handle/with_replies"})
    await asyncio.sleep(4)
    js = ("JSON.stringify([...document.querySelectorAll('article[data-testid=\"tweet\"]')].slice(0, 12)"
          ".map(a => { const tx = a.querySelector('[data-testid=\"tweetText\"]'); return tx ? tx.innerText : ''; }))")
    r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
    try:
        arr = json.loads(json.loads(r3).get("result", "[]"))
    except Exception:
        arr = []
    return any(text.strip() in x for x in arr)


def lint_text(t):
    warn = []
    if "\u2014" in t or "\u2013" in t:
        warn.append("dash!")
    if len(t) > 275:
        warn.append("too-long!")
    return warn


async def main():
    args = sys.argv[1:]
    if not args:
        print("usage: fire_driver.py targets.json [--max N] [--gap-min S] [--gap-max S]")
        return 2
    tf = args[0]
    max_n = 6
    gap_min, gap_max = 20, 45
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])
    if "--gap-min" in args:
        gap_min = float(args[args.index("--gap-min") + 1])
    if "--gap-max" in args:
        gap_max = float(args[args.index("--gap-max") + 1])

    targets = json.load(open(tf))[:max_n]
    os.makedirs(f"{OUT}/logs", exist_ok=True)
    run_id = time.strftime("%Y%m%d_%H%M%S")
    logf = open(f"{OUT}/logs/fire-{run_id}.jsonl", "w")

    results = []
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            page = await pick_page(s)
            if not page:
                print("NO PAGE — abort")
                return 1
            print(f"page: {page} | targets: {len(targets)} | gap {gap_min}-{gap_max}s")
            for i, t in enumerate(targets):
                url, text = t["url"], t["text"]
                warn = lint_text(text)
                t0 = time.time()
                outcome = "error"
                try:
                    await call(s, "cloak_navigate", {"page_id": page, "url": url})
                    await asyncio.sleep(random.uniform(3.5, 5.5))
                    js = JS_TEMPLATE.replace("__TEXT__", json.dumps(text))
                    r3 = await call(s, "cloak_evaluate", {"page_id": page, "expression": js})
                    try:
                        outcome, diag = split_outcome(json.loads(r3).get("result", "error"))
                    except Exception:
                        outcome, diag = f"parse:{r3[:60]}", None
                    if outcome == "no-box":
                        restricted = bool((diag or {}).get("evidence"))
                        outcome = "no-box-restricted" if restricted else "no-box-timeout"
                        if restricted:
                            note_restricted(url, diag)
                        if diag:
                            print(f"   diag: {json.dumps(diag, ensure_ascii=False)[:220]}")
                except Exception as e:
                    outcome = f"error:{type(e).__name__}"
                    traceback.print_exc()
                if outcome == "THROTTLED":
                    # false-alarm guard: indexing lag can hide the reply on the first look;
                    # retry up to 3x before declaring a real throttle (costly batch stop).
                    for _chk in range(3):
                        await asyncio.sleep(2 if _chk == 0 else 8)
                        try:
                            if await check_posted(s, page, text):
                                outcome = "hit(post-verified)"
                                print("   (throttle was a false alarm - reply is live)")
                                break
                        except Exception:
                            pass
                dt = round(time.time() - t0, 1)
                line = {"ts": time.strftime("%H:%M:%S"), "url": url, "text": text,
                        "lang": t.get("lang", ""), "tags": t.get("tags", []),
                        "outcome": outcome, "warn": warn, "secs": dt}
                if diag:
                    line["diag"] = diag
                results.append(line)
                logf.write(json.dumps(line, ensure_ascii=False) + "\n")
                logf.flush()
                print(f"[{i+1}/{len(targets)}] {outcome:11s} {url.split('/')[-1]} ({dt}s)" + (f" warn={warn}" if warn else ""))
                if outcome == "THROTTLED":
                    print(">> THROTTLE SIGNAL — stopping batch (cooldown protocol)")
                    break
                if i < len(targets) - 1:
                    gap = random.uniform(gap_min, gap_max)
                    if (i + 1) % 5 == 0:
                        gap += random.uniform(30, 60)
                        print(f"   (micro-pause {gap:.0f}s)")
                    await asyncio.sleep(gap)

    logf.close()
    hits = sum(1 for x in results if x["outcome"] == "hit")
    print(f"SUMMARY: {hits} hit / {len(results)} attempted | log: {OUT}/logs/fire-{run_id}.jsonl")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
