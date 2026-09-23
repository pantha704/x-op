#!/usr/bin/env python3
"""Consistent stale-file cleanup for the x-op rig.

The selection scripts exclude every URL found in targets/*.json ("queued") - so stale wave/pool/
batch files pin candidates forever and the reply pool runs dry. This script ages out everything
that is no longer live, on a schedule, so the exclusion set self-heals.

Default = DRY RUN. Pass --apply to execute. Archives (moves), never hard-deletes, except media
uploads (already uploaded to X) and ctx-urls scratch files.

Rules:
  targets/*.json       -> targets/archive/<YYYY-MM>/ if older than --targets-days (48h)
                          KEEP: posts-queue.json, restricted-urls.json, *-ideas.json, targets.json
  logs/fire-*.jsonl    -> gzip into logs/archive/ if older than --logs-days (14d)
  worker/*.json|txt    -> worker/archive/ if older than --worker-days (72h)   KEEP: state.json
  .playwright-mcp/media -> delete if older than --uploads-days (14d)
  x-op/media/**        -> delete if older than --media-days (30d)
"""
import argparse, glob, gzip, json, os, shutil, sys, time

X = "/home/ubuntu/x-op"
KEEP_TARGETS = {"posts-queue.json", "restricted-urls.json", "trend-ideas.json",
                "anime-ideas.json", "games-ideas.json", "targets.json"}
KEEP_WORKER = {"state.json"}


def url_count(path):
    try:
        d = json.load(open(path))
    except Exception:
        return 0

    def cnt(o):
        c = 0
        if isinstance(o, dict):
            if isinstance(o.get("url"), str):
                c += 1
            for v in o.values():
                c += cnt(v)
        elif isinstance(o, list):
            for v in o:
                c += cnt(v)
        return c
    return cnt(d)


def move(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--targets-days", type=float, default=2)
    ap.add_argument("--logs-days", type=float, default=14)
    ap.add_argument("--worker-days", type=float, default=3)
    ap.add_argument("--uploads-days", type=float, default=14)
    ap.add_argument("--media-days", type=float, default=30)
    ap.add_argument("--scripts-days", type=float, default=7)
    a = ap.parse_args()
    now = time.time()
    report = {"targets": [], "logs": [], "worker": [], "worker_scripts": [], "uploads": [], "media": [], "urls_freed": 0}

    # 1) targets/*.json
    for f in sorted(glob.glob(f"{X}/targets/*.json")):
        name = os.path.basename(f)
        if name in KEEP_TARGETS:
            continue
        age = (now - os.stat(f).st_mtime) / 86400
        if age >= a.targets_days:
            report["targets"].append(name)
            report["urls_freed"] += url_count(f)
            if a.apply:
                move(f, f"{X}/targets/archive/{time.strftime('%Y-%m')}/{name}")

    # 2) logs/fire-*.jsonl
    for f in sorted(glob.glob(f"{X}/logs/fire-*.jsonl")):
        age = (now - os.stat(f).st_mtime) / 86400
        if age >= a.logs_days:
            report["logs"].append(os.path.basename(f))
            if a.apply:
                dst = f"{X}/logs/archive/{os.path.basename(f)}.gz"
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(f, "rb") as src, gzip.open(dst, "wb") as out:
                    shutil.copyfileobj(src, out)
                os.remove(f)

    # 3) worker/*.json + *.txt scratch
    for f in sorted(glob.glob(f"{X}/worker/*.json") + glob.glob(f"{X}/worker/*.txt")):
        name = os.path.basename(f)
        if name in KEEP_WORKER or name == "replied-today.txt":
            continue
        age = (now - os.stat(f).st_mtime) / 86400
        if age >= a.worker_days:
            report["worker"].append(name)
            if a.apply:
                move(f, f"{X}/worker/archive/{time.strftime('%Y-%m')}/{name}")

    # 3b) one-off worker build scripts (conservative patterns only: build_*/amend_*/tmp_*)
    for pat in ("build_*.py", "amend_*.py", "tmp_*.py", "test_*.py"):
        for f in sorted(glob.glob(f"{X}/worker/{pat}")):
            name = os.path.basename(f)
            age = (now - os.stat(f).st_mtime) / 86400
            if age >= a.scripts_days:
                report["worker_scripts"].append(name)
                if a.apply:
                    move(f, f"{X}/worker/archive/{time.strftime('%Y-%m')}/scripts/{name}")

    # 4) upload staging media
    up = "/home/ubuntu/.hermes/profiles/bounty/.playwright-mcp/media"
    for f in sorted(glob.glob(f"{up}/*")):
        if not os.path.isfile(f):
            continue
        age = (now - os.stat(f).st_mtime) / 86400
        if age >= a.uploads_days:
            report["uploads"].append(os.path.basename(f))
            if a.apply:
                os.remove(f)

    # 5) x-op media (local copies; uploaded media lives on X)
    for f in sorted(glob.glob(f"{X}/media/**/*", recursive=True)):
        if not os.path.isfile(f):
            continue
        age = (now - os.stat(f).st_mtime) / 86400
        if age >= a.media_days:
            report["media"].append(os.path.relpath(f, X))
            if a.apply:
                os.remove(f)

    mode = "APPLIED" if a.apply else "DRY RUN"
    print(f"=== cleanup_stale [{mode}] ===")
    print(f"targets archived : {len(report['targets'])} files  (~{report['urls_freed']} url fields freed)")
    print(f"logs gzipped     : {len(report['logs'])}")
    print(f"worker archived  : {len(report['worker'])}")
    print(f"build scripts    : {len(report['worker_scripts'])}")
    print(f"uploads deleted  : {len(report['uploads'])}")
    print(f"media deleted    : {len(report['media'])}")
    if not a.apply:
        print("\n-- targets to archive:")
        for n in report["targets"][:40]:
            print("   ", n)
        if len(report["targets"]) > 40:
            print(f"    ... +{len(report['targets']) - 40} more")
    out = f"{X}/logs/cleanup-{time.strftime('%Y%m%d-%H%M')}.json"
    json.dump(report, open(out, "w"), indent=1)
    print("report:", out)


if __name__ == "__main__":
    main()
