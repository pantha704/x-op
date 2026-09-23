#!/usr/bin/env python3
"""Push queue drafts onto X as saved drafts (owner directive: review/post from his app).

Usage: draft_posts_x.py [--limit N] [--gap-min 18] [--gap-max 40]
Reads targets/posts-queue.json, drafts every post with status=draft & approved!=False is NOT required here
(these are drafts, not publishes) - but we only push posts flagged push_to_x != False.
Updates the queue with draft_pushed: true.
"""
import json, random, subprocess, sys, time

Q = "/home/ubuntu/x-op/targets/posts-queue.json"
PY = "/home/ubuntu/x-op/venv/bin/python"


def main():
    limit = 99
    gmin, gmax = 18, 40
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--gap-min" in sys.argv:
        gmin = int(sys.argv[sys.argv.index("--gap-min") + 1])
    if "--gap-max" in sys.argv:
        gmax = int(sys.argv[sys.argv.index("--gap-max") + 1])
    q = json.load(open(Q))
    done = 0
    for p in q["posts"]:
        if done >= limit:
            break
        if p.get("draft_pushed"):
            continue
        print(f"== drafting {p['id']} ({p['lane']}): {p['text'][:60]}")
        r = subprocess.run([PY, "/home/ubuntu/x-op/post_draft.py", p["text"]],
                           capture_output=True, text=True, timeout=180)
        tail = (r.stdout or "").strip().splitlines()[-3:]
        print("   ", " | ".join(tail))
        if "OK draft saved" in (r.stdout or ""):
            p["draft_pushed"] = True
            done += 1
            json.dump(q, open(Q, "w"), indent=1)
        else:
            print("    !! not confirmed, leaving for retry")
        time.sleep(random.randint(gmin, gmax))
    print(f"\npushed {done} drafts to X")


if __name__ == "__main__":
    main()
