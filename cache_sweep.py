#!/usr/bin/env python3
"""Clear stale BROWSER CACHES across every Chromium profile on the system.

SAFE BY CONSTRUCTION: only removes regenerable cache directories. Never touches
cookies, logins, local storage, history, sessions, or extensions - all creds
and logins survive intact. Chromium rebuilds caches on next launch (cost: one
slower page load per site).

Live profiles (browsers currently running) are SKIPPED by default - their
caches are locked and clearing them mid-run is unsafe. Use --restart-rigs to
bounce the two x-op rigs (:8932/:8933) in the dark window and clear theirs too.

Usage:
  cache_sweep.py                 # report only (dry run)
  cache_sweep.py --apply         # clear caches on idle profiles
  cache_sweep.py --apply --restart-rigs   # also bounce rigs and clear theirs
"""
import argparse
import os
import subprocess
import time

HOME = "/home/ubuntu"
# (label, profile root, cache dir names relative to profile root)
PROFILES = [
    ("x-op operator (:8932)", f"{HOME}/.cloakbrowser/profiles/operator",
     ["Default/Cache", "Default/Code Cache", "Default/GPUCache",
      "Default/DawnWebGPUCache", "Default/DawnGraphiteCache",
      "Default/Service Worker/CacheStorage", "Default/Service Worker/ScriptCache",
      "GrShaderCache", "ShaderCache", "GraphiteDawnCache"]),
    ("x-op operator2 (:8933)", f"{HOME}/.cloakbrowser/profiles/operator2",
     ["Default/Cache", "Default/Code Cache", "Default/GPUCache",
      "Default/DawnWebGPUCache", "Default/DawnGraphiteCache",
      "Default/Service Worker/CacheStorage", "Default/Service Worker/ScriptCache",
      "GrShaderCache", "ShaderCache", "GraphiteDawnCache"]),
    ("cybersec bc-profile", f"{HOME}/cybersec/profiles/bc-profile",
     ["Default/Cache", "Default/Code Cache", "Default/GPUCache",
      "component_crx_cache", "optimization_guide_model_store", "WasmTtsEngine",
      "Safe Browsing", "OnDeviceHeadSuggestModel", "CertificateRevocation",
      "BrowserMetrics-spare.pma"]),
]
for name in ("profile", "profile-b", "profile-bb", "profile-c"):
    PROFILES.append((f"gitprotect {name}",
                     f"{HOME}/cybersec/recon/gitprotect/{name}",
                     ["Default/Cache", "Default/Code Cache", "Default/GPUCache",
                      "Default/DawnWebGPUCache", "Default/DawnGraphiteCache",
                      "Default/Service Worker/CacheStorage",
                      "GrShaderCache", "ShaderCache", "GraphiteDawnCache",
                      "BrowserMetrics-spare.pma"]))

# never, ever delete these - the creds and session state
PROTECTED = ("cookies", "login data", "local storage", "session storage",
             "indexeddb", "history", "sessions", "extensions", "web data")


def du(path):
    if not os.path.exists(path):
        return 0
    out = subprocess.run(["du", "-sb", path], capture_output=True, text=True).stdout
    return int(out.split()[0]) if out.strip() else 0


def live_profile_roots():
    """profile dirs whose browser is currently running (skip these)."""
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    live = set()
    for line in out.splitlines():
        if "user-data-dir=" in line:
            for tok in line.split():
                if "user-data-dir=" in tok:
                    live.add(tok.split("user-data-dir=", 1)[1].rstrip("/"))
    return live


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    ap.add_argument("--restart-rigs", action="store_true",
                    help="bounce :8932/:8933 rigs (dark window only) so their caches clear too")
    args = ap.parse_args()

    live = live_profile_roots()
    total_free = 0
    print("=== cache sweep %s ===" % time.strftime("%FT%TZ", time.gmtime()))
    print("live profiles (locked):", ", ".join(sorted(live)) or "none")

    for label, root, caches in PROFILES:
        if not os.path.isdir(root):
            continue
        locked = root.rstrip("/") in live
        size = sum(du(os.path.join(root, c)) for c in caches)
        if size < 1024 * 1024:
            continue
        action = "SKIP (live)" if locked and not args.restart_rigs else ("CLEAR" if args.apply else "would clear")
        print("  %-28s %6.0f MB  %s" % (label, size / 1048576, action))
        if args.apply and (not locked or args.restart_rigs):
            for c in caches:
                p = os.path.join(root, c)
                # hard guard: refuse anything touching protected names
                if any(prot in c.lower() for prot in PROTECTED):
                    print("    REFUSED (protected):", c)
                    continue
                if os.path.exists(p):
                    subprocess.run(["rm", "-rf", p])
            total_free += size
    print("freed: %.0f MB" % (total_free / 1048576))


if __name__ == "__main__":
    main()
