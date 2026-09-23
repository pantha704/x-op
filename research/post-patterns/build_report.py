#!/usr/bin/env python3
"""Build the post-patterns research report (Markdown + PDF).

Inputs: research/post-patterns/raw/*.json  +  research/post-patterns/analysis.json
Output: research/post-patterns/REPORT.md and REPORT.pdf
"""
import json, os, statistics as st
import markdown
from weasyprint import HTML

BASE = "/home/ubuntu/x-op/research/post-patterns"
RAW = f"{BASE}/raw"

NARRATIVE = {
    "exec": """Two things decide whether a post lands: **media** and **a human voice**. Across every
account studied, posts carrying an image or clip outperform text-only posts, and the best-performing
lines are first-person reactions, not announcements. The worst performers are flat observations,
score roundups, and news relayed without a take. This is the same failure mode flagged on our own
drafts (reporter tone), now confirmed with other accounts' numbers.""",
}

def load():
    a = json.load(open(f"{BASE}/analysis.json"))
    return a


def fmt_top(rows, n=5):
    out = []
    for t in rows[:n]:
        img = "img" if t.get("imgs") else "no-img"
        out.append(f"| {t['likes']:,} | x{t['lift']} | {img} | {t['text'][:110]} |")
    return "\n".join(out)


def main():
    a = load()
    md = []
    md.append("# What works on posts (and what doesn't)\n")
    md.append("*Research across 18 accounts, harvested 2026-09-21. Sources: X search — each account's all-time top posts "
              "(min_faves:1000), recent winners (min_faves:30, last 5 weeks), and their ordinary feed as baseline.*\n")
    md.append("## Executive summary\n")
    md.append(NARRATIVE["exec"] + "\n")
    md.append("## Cross-account signal\n")
    md.append("Median lift = (post likes) ÷ (that account's baseline median). Feature rows show posts WITH the feature vs WITHOUT.\n")
    md.append("| feature | median lift with | without | delta | n |")
    md.append("|---|---|---|---|---|")
    for k, v in a["feature_lift"].items():
        md.append(f"| {k} | {v['median_lift_with']} | {v['median_lift_without']} | {v['delta']:+.2f} | {v['n']} |")
    md.append("\n## Case studies\n")
    for u, acc in a["accounts"].items():
        md.append(f"### @{u}\n")
        md.append(f"Baseline median: **{acc['baseline_median_likes']:,} likes**. Posts harvested: {acc['posts']}.\n")
        md.append("| likes | lift | media | post |")
        md.append("|---|---|---|---|")
        md.append(fmt_top(acc["top"], 5))
        md.append("")
    md.append("## What this means for @your_handle\n")
    md.append("(filled by the operator — see REPORT_NOTES.md)\n")
    text = "\n".join(md)
    open(f"{BASE}/REPORT.md", "w").write(text)
    html = markdown.markdown(text, extensions=["tables"])
    html = "<html><head><meta charset='utf-8'><style>body{font-family:Georgia,serif;max-width:820px;margin:40px auto;line-height:1.5;color:#111}h1,h2,h3{font-family:Helvetica,Arial,sans-serif}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border:1px solid #ccc;padding:4px 6px;text-align:left}</style></head><body>" + html + "</body></html>"
    HTML(string=html).write_pdf(f"{BASE}/REPORT.pdf")
    print("wrote REPORT.md + REPORT.pdf")
    print(text[:1500])


if __name__ == "__main__":
    main()
