#!/usr/bin/env python3
"""Quote wave driver: fire a targets.json batch as QUOTE posts (card + comment).

Same pacing + logging discipline as fire_driver.py. Owner directive 2026-09-23:
the reply arm switches to quotes - quote posts count toward verified Home
Timeline impressions, replies never do.

Usage: quote_driver.py <targets.json> [--max N] [--gap-min S] [--gap-max S]

Targets schema: [{"url": <target permalink>, "text": <our line>, "tags": [...]}]
Log: logs/fire-YYYYMMDD-HHMMSS.jsonl - one entry per target, same fields as the
reply driver plus {"type": "quote", "quote_url": <our new post permalink>}.

Outcomes: hit (posted + toast verified) / no-article (target never rendered) /
no-box-restricted (retweet button missing - protected or restricted post) /
unverified (post click happened but no toast; check the profile).
"""
import asyncio
import json
import os
import random
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"


async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])


async def ev(s, pid, js):
    raw = await call(s, "cloak_evaluate", {"page_id": pid, "expression": js})
    try:
        return json.loads(json.loads(raw).get("result", "null"))
    except Exception:
        return {"raw": raw[:200]}


OPEN_QUOTE_JS = r"""JSON.stringify((() => {
  const b = document.querySelector('[data-testid="retweet"]');
  if (!b) return {ok:false, why:'no retweet button'};
  b.click(); return {ok:true};
})())"""

MENU_JS = r"""JSON.stringify((() => {
  const items = [...document.querySelectorAll('[role="menuitem"]')];
  const q = items.find(x => /quote/i.test(x.innerText || ''));
  if (q) { q.click(); return {ok:true, via:'menuitem'}; }
  const link = [...document.querySelectorAll('a[href*="/compose/post"]')].find(a => /quote/i.test(a.innerText||''));
  if (link) { link.click(); return {ok:true, via:'link'}; }
  return {ok:false, items: items.map(x => (x.innerText||'').slice(0,24))};
})())"""

TYPE_JS = r"""JSON.stringify((() => {
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  if (!ed) return {ok:false, why:'no editor'};
  ed.focus();
  if ((ed.innerText || '').length > 0) {
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    ed.focus();
  }
  document.execCommand('insertText', false, %s);
  return {ok:true, len: (ed.innerText || '').length, text: (ed.innerText || '').slice(0, 80)};
})())"""

CARD_JS = r"""JSON.stringify((() => {
  const d = document.querySelector('[role="dialog"]') || document;
  const byAvatar = !!d.querySelector('[data-testid="UserAvatar-Container-__HANDLE__"]');
  const byText = (d.innerText || '').includes('__HANDLE__');
  const hasAttach = !!d.querySelector('[data-testid="attachments"]');
  return {ok: byAvatar || byText, byAvatar, byText, hasAttach};
})())"""

POST_JS = r"""JSON.stringify((() => {
  const b = document.querySelector('[data-testid="tweetButton"]') || document.querySelector('[data-testid="tweetButtonInline"]');
  if (!b) return {ok:false, why:'no button'};
  if (b.getAttribute('aria-disabled') === 'true') return {ok:false, why:'disabled'};
  b.click(); return {ok:true};
})())"""

TOAST_JS = r"""JSON.stringify((() => {
  const toast = document.querySelector('[data-testid="toast"]');
  const ed = document.querySelector('[data-testid="tweetTextarea_0"]');
  return { toast: toast ? toast.innerText.slice(0,60) : null, editor: !!ed };
})())"""

PROFILE_JS = r"""JSON.stringify((() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  const out = [];
  for (const a of arts.slice(0, 24)) {
    const t = a.querySelector('time'); const link = t ? t.closest('a') : null;
    const tx = a.querySelector('[data-testid="tweetText"]');
    out.push({url: link ? link.href.split('?')[0] : null, text: tx ? tx.innerText.replace(/\n/g,' ').slice(0,110) : ''});
  }
  return out;
})())"""


async def fire_one(s, pid, target):
    """Run the quote flow on one target. Returns (outcome, warn_list, quote_text_ok)."""
    await call(s, "cloak_navigate", {"page_id": pid, "url": target["url"]})
    await asyncio.sleep(random.uniform(4.0, 5.2))
    oq = await ev(s, pid, OPEN_QUOTE_JS)
    if not (isinstance(oq, dict) and oq.get("ok")):
        # no retweet button: page may not have rendered; retry once with a longer wait
        await asyncio.sleep(3.5)
        oq = await ev(s, pid, OPEN_QUOTE_JS)
        if not (isinstance(oq, dict) and oq.get("ok")):
            return "no-article", [], False
    await asyncio.sleep(random.uniform(1.4, 1.9))
    mq = await ev(s, pid, MENU_JS)
    if not (isinstance(mq, dict) and mq.get("ok")):
        return "no-box-restricted", ["no quote menu"], False
    await asyncio.sleep(random.uniform(2.0, 2.6))
    tp = await ev(s, pid, TYPE_JS % json.dumps(target["text"]))
    if not (isinstance(tp, dict) and tp.get("ok")):
        return "no-article", ["no editor"], False
    if tp.get("len") != len(target["text"]):
        await asyncio.sleep(0.8)
        tp = await ev(s, pid, TYPE_JS % json.dumps(target["text"]))
    warn = []
    if tp.get("len") != len(target["text"]):
        warn.append(f"text len {tp.get('len')} != {len(target['text'])}")
    await asyncio.sleep(random.uniform(1.0, 1.4))
    handle = target["url"].split("/")[3] if "/status/" in target["url"] else ""
    card = await ev(s, pid, CARD_JS.replace("__HANDLE__", handle))
    if not (isinstance(card, dict) and card.get("ok")):
        warn.append("card unconfirmed")
    posted = False
    for _ in range(3):
        po = await ev(s, pid, POST_JS)
        if isinstance(po, dict) and po.get("ok"):
            posted = True
            break
        await asyncio.sleep(2)
    if not posted:
        return "unverified", warn + ["post button stuck"], False
    for _ in range(20):
        st = await ev(s, pid, TOAST_JS)
        if isinstance(st, dict) and (st.get("toast") or not st.get("editor")):
            return "hit", warn, True
        await asyncio.sleep(1.5)
    return "unverified", warn + ["no toast"], True


async def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = {k: v for k, v in zip(sys.argv[1::2], sys.argv[2::2]) if k.startswith("--")} if False else {}
    argv = sys.argv[1:]
    def opt(name, default):
        if name in argv:
            i = argv.index(name)
            try:
                return int(argv[i + 1])
            except Exception:
                return default
        return default
    targets_file = args[0]
    max_n = opt("--max", 20)
    gap_min = opt("--gap-min", 15)
    gap_max = opt("--gap-max", 35)

    data = json.load(open(targets_file))
    targets = data if isinstance(data, list) else data.get("targets", [])
    targets = targets[:max_n]
    print(f"quote wave: {len(targets)} targets from {targets_file} | gaps {gap_min}-{gap_max}s")

    fired = []
    logname = "logs/fire-%s.jsonl" % time.strftime("%Y%m%d-%H%M%S")
    os.makedirs("logs", exist_ok=True)

    async with streamable_http_client(URL) as ctx:
        async with ClientSession(ctx[0], ctx[1]) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "https://x.com/home"}))
            pid = np.get("page_id") or np.get("id")
            await asyncio.sleep(3)
            for idx, t in enumerate(targets):
                t0 = time.time()
                try:
                    outcome, warn, posted = await fire_one(s, pid, t)
                except Exception as e:
                    outcome, warn, posted = "error", [str(e)[:80]], False
                entry = {
                    "ts": time.strftime("%H:%M:%S"),
                    "url": t["url"],
                    "text": t["text"],
                    "lang": "",
                    "tags": t.get("tags") or [],
                    "outcome": outcome,
                    "warn": warn,
                    "secs": round(time.time() - t0, 1),
                    "type": "quote",
                }
                if posted:
                    fired.append({"text": t["text"], "target": t["url"]})
                with open(logname, "a") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[{idx+1}/{len(targets)}] {outcome} {t['url'][-30:]} ({entry['secs']}s)")
                if outcome == "hit" and idx < len(targets) - 1:
                    await asyncio.sleep(random.uniform(gap_min, gap_max))

            # capture permalinks of what we just posted (one profile visit)
            if fired:
                try:
                    await call(s, "cloak_navigate", {"page_id": pid, "url": "https://x.com/your_handle"})
                    await asyncio.sleep(5)
                    rows = await ev(s, pid, PROFILE_JS)
                    if isinstance(rows, list):
                        used = set()
                        # newest-first; match by text prefix (our line is the start of the post text)
                        for f in fired:
                            key = f["text"][:48]
                            for r in rows:
                                if r["url"] and r["url"] not in used and r["text"].startswith(key[:40]):
                                    f["quote_url"] = r["url"]
                                    used.add(r["url"])
                                    break
                except Exception as e:
                    print("permalink capture failed:", str(e)[:100])
                # rewrite log with quote_urls
                lines = [json.loads(l) for l in open(logname) if l.strip()]
                for e in lines:
                    for f in fired:
                        if f["target"] == e["url"] and f.get("quote_url"):
                            e["quote_url"] = f["quote_url"]
                with open(logname, "w") as fh:
                    for e in lines:
                        fh.write(json.dumps(e, ensure_ascii=False) + "\n")
                print("permalinks:", sum(1 for f in fired if f.get("quote_url")), "/", len(fired))
            try:
                await call(s, "cloak_close_page", {"page_id": pid})
            except Exception:
                pass
    hits = sum(1 for l in open(logname) if '"outcome": "hit"' in l)
    print(f"DONE {hits}/{len(targets)} hit | log={logname}")


if __name__ == "__main__":
    asyncio.run(main())
