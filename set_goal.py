#!/usr/bin/env python3
"""set_goal.py <N> — arm a reply goal for the worker (owner directive 2026-09-24).

The worker is goal-driven now: it fires replies until `completed` reaches `target`,
then goal_watch pauses it. Nothing runs without an active goal.

Usage: set_goal.py <target_count>          (arm the goal; worker still needs resume)
       set_goal.py --status                (show current goal)
       set_goal.py --clear                 (deactivate)
"""
import json
import sys
import time

GOAL = "worker/goal.json"


def load():
    try:
        return json.load(open(GOAL))
    except Exception:
        return {"active": False, "target": 0, "started_ts": "", "completed": 0, "goal_type": "replies", "history": []}


def save(g):
    json.dump(g, open(GOAL, "w"), indent=1)


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    g = load()
    if argv[0] == "--status":
        print(json.dumps(g, indent=1))
        return
    if argv[0] == "--clear":
        g["active"] = False
        save(g)
        print("goal cleared")
        return
    n = int(argv[0])
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    hist = g.get("history", [])
    if g.get("target"):
        hist.append({"target": g["target"], "completed": g.get("completed", 0), "ended": now})
    g = {"active": True, "target": n, "started_ts": now, "completed": 0, "goal_type": "replies", "history": hist[-10:]}
    save(g)
    print(f"goal armed: {n} replies (active). Resume the worker to start: hermes cron resume fff4b48b1810")


if __name__ == "__main__":
    main()
