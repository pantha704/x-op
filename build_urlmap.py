#!/usr/bin/env python3
"""Build a text->url map from a verify file against a targets file.
Usage: build_urlmap.py <verify.json> <targets.json> <out.json>
"""
import json
import sys

v = json.load(open(sys.argv[1]))
targets = json.load(open(sys.argv[2]))
m = {}
for t in targets:
    for item in v:
        if (item.get("text") or "").strip() == t["text"].strip():
            m[t["text"]] = item["url"]
json.dump(m, open(sys.argv[3], "w"), indent=1, ensure_ascii=False)
print(f"mapped {len(m)} of {len(targets)}")
