#!/usr/bin/env python3
"""Analyze harvested post data v2: cleaner baselines + contamination check.

- baseline = median likes of the account's own "baseline" pass (their live feed); needs >=5 posts to count
- accounts without a reliable baseline fall back to median of all their harvested posts (marked approx)
- contamination check: share of posts whose @handle matches the account
"""
import json, os, re, statistics as st

RAW = "/home/ubuntu/x-op/research/post-patterns/raw"
OUT = "/home/ubuntu/x-op/research/post-patterns/analysis.json"

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
NEWS = re.compile(r"\b(announced|announces|reveals?|revealed|trailer|teaser|first look|leak|leaked|delayed|release date|launches|coming to|available now|update|patch|reportedly)\b", re.I)
OPINION = re.compile(r"\b(i think|honestly|imo|my take|wild|insane|crazy|unhinged|should|needs to|never|always|worst|best|actually|wtf|why does|why is)\b", re.I)
HYPE = re.compile(r"\b(lets go|let's go|we are so back|so back|peak|goat|cinema|masterpiece|cooked|we won|lfg|broke the internet|out of hand)\b", re.I)
QUESTION = re.compile(r"\?")
NUM = re.compile(r"\d")
HASH = re.compile(r"#\w+")
MENTION = re.compile(r"@\w+")
LINK = re.compile(r"https?://")
REACTION = re.compile(r"^(i|we|my|me)\b|\b(i think|i never|i can't|i cant|i love|i hate|never understood|can't stop|cant stop)\b", re.I)


def feats(p):
    t = p.get("text") or ""
    words = len(t.split())
    return {
        "has_media": p.get("imgs", 0) > 0 or p.get("media", 0) > 0,
        "short_text": words <= 12,
        "long_text": words >= 25,
        "has_emoji": bool(EMOJI.search(t)),
        "news_shape": bool(NEWS.search(t)),
        "opinion_shape": bool(OPINION.search(t)),
        "hype_shape": bool(HYPE.search(t)),
        "first_person_reaction": bool(REACTION.search(t)),
        "question": bool(QUESTION.search(t)),
        "has_number": bool(NUM.search(t)),
        "has_hashtag": bool(HASH.search(t)),
        "has_mention": bool(MENTION.search(t)),
        "has_link": bool(LINK.search(t)),
        "lowercase_start": bool(t[:1].islower()),
    }


def median(xs):
    return st.median(xs) if xs else 0


def main():
    files = sorted(f for f in os.listdir(RAW) if f.endswith(".json"))
    accounts, all_posts = {}, []
    for f in files:
        user = f[:-5]
        posts = json.load(open(f"{RAW}/{f}"))
        if not posts:
            continue
        base = [p["likes"] for p in posts if p.get("pass") == "baseline" and p.get("likes", -1) >= 0]
        approx = len(base) < 5
        med = median(base) if not approx else median([p["likes"] for p in posts if p.get("likes", -1) >= 0])
        if med <= 0:
            continue
        match = sum(1 for p in posts if (p.get("handle") or "").lower() == "@" + user.lower())
        for p in posts:
            p["user"] = user
            p["lift"] = round(p["likes"] / med, 2)
            p["feats"] = feats(p)
            all_posts.append(p)
        top = sorted([p for p in posts if p.get("pass") in ("top-all", "top-recent")], key=lambda x: -x["likes"])[:5]
        accounts[user] = {
            "posts": len(posts),
            "baseline_median_likes": int(med),
            "baseline_reliable": not approx,
            "handle_match_pct": round(100 * match / len(posts)),
            "top": [{"likes": p["likes"], "lift": p["lift"], "text": p["text"][:130], "imgs": p["imgs"]} for p in top],
        }
    # feature lift on reliable-baseline posts only
    rel = [p for p in all_posts if accounts[p["user"]]["baseline_reliable"]]
    fkeys = list(feats({"text": "", "imgs": 0}).keys())
    flift = {}
    for k in fkeys:
        with_ = [p["lift"] for p in rel if p["feats"].get(k)]
        without = [p["lift"] for p in rel if not p["feats"].get(k)]
        if len(with_) >= 8 and len(without) >= 8:
            flift[k] = {"n": len(with_), "median_lift_with": round(median(with_), 2),
                        "median_lift_without": round(median(without), 2),
                        "delta": round(median(with_) - median(without), 2)}
    flift = dict(sorted(flift.items(), key=lambda kv: -kv[1]["delta"]))
    json.dump({"accounts": accounts, "feature_lift": flift, "total_posts": len(all_posts),
               "reliable_posts": len(rel)}, open(OUT, "w"), indent=1)
    print(f"{len(accounts)} accounts, {len(all_posts)} posts ({len(rel)} with reliable baseline)\n")
    print("FEATURE LIFT (reliable-baseline accounts):")
    for k, v in flift.items():
        print(f"  {k:<22} with={v['median_lift_with']:<5} without={v['median_lift_without']:<5} delta={v['delta']:+.2f} (n={v['n']})")
    print("\nACCOUNTS:")
    for u, a in accounts.items():
        flag = "" if a["baseline_reliable"] else " (approx base)"
        sus = "" if a["handle_match_pct"] >= 80 else f" SUSPECT handle_match={a['handle_match_pct']}%"
        print(f"  {u:<18} base={a['baseline_median_likes']:<7}{flag}{sus}")


if __name__ == "__main__":
    main()
