# FAILSAFE REVIEW — x-op new system (2026-09-23)

Scope: PREP PASS (cooldown prep), compose-wide (5->kill 4), quote lane, conversation pass, scouts, cycle pipeline, cron prompts. Method: superpowers verification discipline (evidence before claims) + live log inspection + GitNexus structural index. Every finding cites its evidence; every fix verified after application.

## VERIFIED SAFE (evidence-backed)

**V1. Cycle single-flight — the scheduler already prevents overlapping runs.**
Evidence: worker session starts today: 060032, 061032, 062032, 063033, 070034, 072035, 080044. Session 072035 ran 36 min (07:20-07:56); ticks 07:30/07:40/07:50 are MISSING — the runtime skipped them while the run was active. Two cycles can never compose/consume concurrently under normal operation.

**V2. Fire serialization — flock is process-bound.** `run_wave.sh` holds fd 9 in the detached child; a dead driver releases it automatically. REFUSED-retry (60s x5) bridges contention with the main arm.

**V3. Prep consumption is single-consumer.** The consuming cycle deletes the prep file only after a launch that printed `detached pid=`; a REFUSED launch leaves it for the next cycle.

**V4. Queue writes are append-only; scout IDs namespaced per lane.** No overwrite path exists.

**V5. Quote lane never auto-fires.** quote_publish.py is manual-only; spec 2d is DRAFT-FIRST.

## FINDINGS + FIXES (all applied and verified)

**F1 (HIGH→ACCEPTED) — No max-runtime field exists in this Hermes build for cron jobs.**
Checked: `hermes cron edit --help` (no runtime flag) and jobs.json (no job carries a timeout key). A truly hung session would block later ticks (V1 skip-while-running) — but a cycle cannot hang forever: tool calls are timeout-bounded, waits are bounded (15 min), and the model loop terminates. Longest observed cycle: 36 min. Residual risk accepted + documented; the systems audit flags staleness.

**F2 (HIGH) — Spec conflict: precondition 3 ("wave live -> SKIP") vs step 0a ("wait for wave") vs PREP PASS ("prep while wave fires").**
FIX APPLIED (spec): precondition 3 rewritten — `pending_verify` set => our wave => step 0a governs (wait -> verify -> launch); a foreign wave/harvest => skip fire only; the prep pass explicitly runs while our wave fires.

**F3 (MEDIUM) — Prep re-validation missed fire-log dedupe.** The ledger/vault log lags a wave; a prep batch could double-fire a target.
FIX APPLIED (spec step 1): re-validation now = "same way select_latest.py does (fire logs 24h + ledger + pending files; >60 min dropped)".

**F4 (MEDIUM) — Stuck-wave detection was slow (2.5h) and non-recovering.** A hung fire_driver holds the flock forever.
FIX APPLIED (watchdog): kills a fire_driver alive >25 min (normal wave 14-16 min total; verified `bash -n` clean). Flock frees; next cycle resumes via pending_verify. It reports on kill.

**F5 (HIGH) — The cron PROMPT contradicted the new spec ("END the cycle" right after firing; no prep-first, no prep-pass).**
FIX APPLIED: prompt rebuilt and verified in jobs.json — step 1 PREP FIRST, step 3 fire, step 4 PREP PASS, spec referenced as authority. (`it keeps firing after this cycle ends` removed; `PREP FIRST` + `PREP PASS` present.)

**F6 (LOW) — Worker scratch litter: 449 py files in worker/.** Cleanup cron archives after 1 day; volume noted, non-fatal. Watch.

**F7 (LOW) — Draft queue lifecycle rule missing (items can sit `pending` forever).** Noted for drafts/README when LO wants it.

**F8 (LOW) — Dark-window prep edge.** A prep built before 23:30 goes stale by 06:30; the 25-min check rejects it and the morning falls back to the hot path. By design.

## GITNEXUS INDEX (requested)

- x-op is now a git repo (initial commit + review commit) with `.gitignore` for venv/logs/targets/media/.gitnexus.
- `gitnexus analyze` completed 08:03:58Z: **958 files, 4,177 nodes, 4,976 edges, 243 communities, 49 processes.**
- `gitnexus check --cycles`: **clean — 0 elementary cycles, 0 circular components** (complete enumeration). No import tangles in the rig code.
- Value: impact analysis + structure queries available for future rig edits; git history now exists for rollback.

## Live proof (observed during this review)

- 07:54 wave fired from a batch pre-built at 07:53 (during the previous cycle's cooldown) — the prep pattern working in practice before it was even formalized.
- 08:00 cycle: found our wave live with pending_verify -> waited (bounded) -> ran vault_log/verify on the 0754 fire log -> launched the next batch on wave-end. Chained cadence confirmed: wave-to-wave gap ~15-16 min (previous days: 27-39 min).
- Fire-log timestamps remain the ground truth for the cadence claim; the +24h measure cron gives the engagement verdict.
