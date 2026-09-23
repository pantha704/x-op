# CURATED TRACK — main rig, 24/7 (owner directive 2026-09-21, post-goal regime)

The main arm's permanent job: find trending, high-potential posts; compose the sharpest possible reply
for the context; post ONLY if it clears the banger bar; report the link to the owner.

## The banger bar (owner 2026-09-21: "curated replies are not banging enough")
A curated reply must do at least ONE of these — flat observation is a skip, not a post:
- **name the absurdity** in the parent ("and nobody stopped them", "who approved this")
- **deadpan approval** of something ridiculous ("and honestly, correct priorities") <- the thighs mechanism
- **specific detail** the parent glossed over (concrete noun from the post, zero invented numbers)
- **a turn** in the last clause (and still / except / somehow / meanwhile)
Never: compliment-shaped lines ("X is amazing"), sweet observations with no edge, essay similes, register mismatch.

**Screenshot test:** if a stranger wouldn't screenshot the line and send it to a group chat, it is not ready.

## Composition protocol
1. Shortlist 3-5 candidate posts (scorer: tier + sparse replies + freshness + live window).
2. For each: write **5 candidate lines**, then kill the 4 safest. Keep the one that survives the screenshot test.
3. Bot-tell gate (`qc_botcheck.py`): HARD disqualifies; soft flags fixed.
4. Punch gate (`score_candidates.py <file> --lines`): **punch >= 6 AND final >= 55**, else the slot is a SKIP.
5. Fire the argmax only. Resolve the permalink (`replylink.py`) and report it with one line of why.

## Cadence
- Target drumbeat: **at least one curated post per 30-60 min** during active windows (06:30-23:30 UTC; dark 23:30-06:30).
- **Never force.** If nothing clears the bar, skip — an empty slot beats a flat line.
- At most 2 back-to-back per cycle; extras re-score next cycle (48h age-out).

## Sources of truth (re-read per cycle)
Bible (`docs/05-op-bible.md` + private `AGENTS.md` block), `Noir - X Growth Playbook.md`, `campaign/winners.md`,
`pipeline/fired-reply-pairs.json`, pattern library, ledger, nightly audit.
Noir rules in force: E.S.S., timing heat lanes, roast arm ~20-25%, small-tier ~10-15%, non-publish mix, 48h limit, one action stream.

## What must NEVER happen
- Force-fire to meet cadence. Posting without the gates. Posting from stale/unverified context.
- Two arms firing simultaneously (flock orders everything; skip if any fire_driver/harvest_run/run_wave is live).
- Posting a flat-but-clean line and calling it curated (that was the 15:56-17:02 failure mode).
