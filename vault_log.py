#!/usr/bin/env python3
"""Append a finished fire batch to the vault ledger + growth log, commit + push.
Usage: vault_log.py <fire-log.jsonl> <targets.json> [urlmap.json]
  urlmap.json: {"<reply text>": "<our reply url>"} from verify pass (optional).
"""
import json, subprocess, sys, time

VAULT = "/home/ubuntu/obsidian/PARA/3. Resources"
LEDGER = VAULT + "/Operator - Reply Ledger.json"
GLOG = VAULT + "/Operator - X Growth Log.md"

def main():
    fire_log, tfile = sys.argv[1], sys.argv[2]
    urls = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    rows = [json.loads(l) for l in open(fire_log) if l.strip()]
    targets = {t["url"]: t for t in json.load(open(tfile))}
    led = json.load(open(LEDGER))
    have = {(e.get("parent"), e.get("text")) for e in led["entries"]}
    day = time.strftime("%Y-%m-%d")
    added = 0
    for r in rows:
        if not str(r.get("outcome", "")).startswith("hit"):
            print("skip non-post:", r.get("outcome"), r["url"])
            continue
        key = (r["url"], r["text"])
        if key in have:
            print("skip dup:", r["url"])
            continue
        t = targets.get(r["url"], {})
        e = {
            "url": urls.get(r["text"]) or r["url"],
            "firedAt": "%sT%s+00:00" % (day, r["ts"]),
            "text": r["text"],
            "tag": (t.get("tags") or ["take"])[0],
            "lang": r.get("lang") or "en",
            "parent": r["url"],
            "parentLikes": t.get("parent_likes"),
            "parentReplies": t.get("parent_replies"),
        }
        led["entries"].append(e)
        added += 1
    json.dump(led, open(LEDGER, "w"), indent=2, ensure_ascii=False)
    open(LEDGER, "a").write("\n")
    n = len(led["entries"])
    hits = sum(1 for r in rows if r["outcome"] == "hit")
    now = time.strftime("%Y-%m-%d %H:%M")
    gl = ("\n### Worker batch (%s UTC)\n"
          "- %d replies fired, %d posted, %d total ledger entries.\n"
          "- Next: +1h screen, then +24h verdicts.\n") % (now, added, hits, n)
    open(GLOG, "a").write(gl)
    subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "add",
                    "PARA/3. Resources/Operator - Reply Ledger.json",
                    "PARA/3. Resources/Operator - X Growth Log.md"])
    subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "commit", "-m",
                    "Operator op: worker batch (+%d ledger entries)" % added])
    subprocess.run(["git", "-C", "/home/ubuntu/obsidian", "push", "origin", "master"])
    print("ledger entries now: %d (+%d) | committed + pushed" % (n, added))

if __name__ == "__main__":
    main()
