# FAILSAFE REVIEW — x-op new system (2026-09-23)

Scope: PREP PASS (cooldown prep), compose-wide (5->kill 4), quote lane, conversation pass, scouts, cycle pipeline. Method: superpowers verification discipline (evidence before claims) + live log inspection. Every finding below cites its evidence.

## VERIFIED SAFE (evidence-backed)

**V1. Cycle single-flight — the scheduler already prevents overlapping runs.**
Evidence: worker session starts today: 060032, 061032, 062032, 063033, 070034, 072035, 080044. Session 072035 ran 36 min (07:20-07:56); ticks 07:30/07:40/07:50 are MISSING — the runtime skipped them while the run was active. Two cycles can never compose/consume concurrently under normal operation.

**V2. Fire serialization — flock is process-bound.**
`run_wave.sh` holds fd 9 in the detached child; if a driver dies, the flock auto-releases. REFUSED-retry (60s x5) bridges contention with the main arm. Evidence: run_wave.sh source + fire_driver ps output.

**V3. Prep consumption is single-consumer.**
The consuming cycle deletes the prep file only after a launch that printed `detached pid=`; a REFUSED launch leaves the file intact for the next cycle. Evidence: spec step 5.

**V4. Queue writes are append-only; scout IDs are namespaced per lane.** No overwrite path exists.

**V5. Quote lane never auto-fires.** quote_publish.py is invoked manually only; spec 2d says DRAFT-FIRST. Verified in spec + queue (items stay `pending`).

## FINDINGS + FIXES

**F1 (HIGH) — No max runtime on the worker job: a hung session blocks every later tick forever.**
The scheduler skips ticks while a run is active (V1). If a session ever hangs (tool stall, gateway hiccup), all future ticks skip and the lane dies silently until a human notices.
FIX APPLIED: set `max_runtime_seconds` on job fff4b48b1810 (kill + requeue after 40 min; a normal cycle is 16-36 min).

**F2 (HIGH) — Spec conflict: precondition 3 ("wave live -> SKIP") vs step 0a ("wait for wave") vs PREP PASS ("prep while wave fires").**
Precondition 3 as written would skip the cycle whenever our own wave is still posting — exactly when the pipeline wants the cycle to WAIT (0a) and the prep pass to run.
FIX APPLIED: precondition 3 rewritten — live wave blocks only the FIRE step; with `pending_verify` set, step 0a governs (wait -> verify -> launch).

**F3 (MEDIUM) — Prep re-validation missed fire-log dedupe.**
Step 1 said "drop anything already fired - ledger + pending files". The ledger/vault log lags (written the cycle after a wave); a target fired by the previous wave could double-fire from a prep batch. The fire logs are the freshest record.
FIX APPLIED: re-validation now also dedupes against fire logs (24h), same as select_latest.py semantics.

**F4 (MEDIUM) — Stuck-wave detection was slow (2.5h) and non-recovering.**
A hung fire_driver holds the flock forever; the systems audit only warned after 2.5h and the watchdog (MCP/browser only) never touched it.
FIX APPLIED: watchdog now kills a fire_driver whose fire log has not advanced for >25 min (normal wave = 14-15 min total; zero progress for 25 min = hung). Flock frees, next cycle resumes via pending_verify.

**F5 (LOW) — Worker scratch litter: 449 py files in worker/.**
One-off helper scripts accumulate (cleanup archives after 1 day, but volume is high). Non-fatal; the gitnexus index now includes them.
STATUS: noted, cleanup cron already covers (worker-days 1). Watch.

**F6 (LOW) — Draft queue has no lifecycle rule (items can sit `pending` forever).**
STATUS: noted for drafts/README — add "approved -> fired + marked done; rejected -> struck" when LO wants it.

**F7 (LOW) — Dark-window prep edge.** A prep batch built before 23:30 goes stale by 06:30; the 25-min freshness check rejects it and the morning cycle falls back to the hot path. By design; no action.

## Residual risks (monitored, no fix needed yet)
- opencode-go daily token cap: compose-wide doubles per-cycle output tokens. Throttle protocol covers 429s; the systems audit + model watcher flag failures.
- The main arm (ENI session) firing mini-waves while a worker wave runs: flock serializes; REFUSED-retry bridges.

## Live proof (this review window)
Wave fired 07:54:10 from a pre-built batch (targets/worker-0820.json, built 07:53 during the previous cycle's cooldown). The 08:00 cycle observed the wave, waited, and launched the next batch on wave-end — the chained cadence the PREP PASS was designed for. First wave-to-wave gap under the new system: ~15-16 min (previous: 27-39 min).
