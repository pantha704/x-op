# x-op — AI-operated X growth rig

The full operating system for **@your_handle**, an openly AI-operated X account.

**Goal:** earn verified Home Timeline impressions (X's Original Content Rewards gate: 500 verified
followers + 500,000 verified Home Timeline impressions / 90 days — replies excluded) while keeping
the account's behaviour human-like, genuinely funny, and within platform rules.

## Architecture

One account, one serialized human-like action stream. Three parts:

1. **Reply worker** — `worker/`, spec: [`worker/WORKER-SPEC.md`](worker/WORKER-SPEC.md).
   Runs every 10 min in the active window (06:30–23:30 UTC):
   harvest → select → **compose-wide** (5 candidates per target, kill the 4 safest) → QC +
   bot-tell gates → **fire a detached wave** (≤20 replies, 15–35s jittered gaps) → **prep pass**:
   compose the next batch during the cooldown so waves chain back-to-back with no idle lane.
   Includes the conversation pass (answer replies-back to our own posts/replies) and the quote lane
   (a genuinely great line becomes a quote *draft* instead of a reply).

2. **Draft scouts** — daily crons that write **only** to [`drafts/`](drafts/) for owner review:
   - **trend scout** — what's booming in tech/AI/gaming/anime right now (manual-only by owner order)
   - **utility scout** — timeless tools/repos/methods people save (10 drafts/day)
   - **human-lines scout** — genuine one-liners, nostalgia, absurdity (5–8/day)
   Nothing publishes without owner approval. Replies stay autonomous; posts never auto-fire.

3. **Support loops** — conversation farm (finds replies-back worth answering), +24h measurement
   (grades every fired reply winner/mid/dead and reports bangers), systems audit, rig watchdog.

## Gates (every reply passes all)

- The quality bar — [`skills/x-post-craft`](skills/x-post-craft/SKILL.md): 45–110 chars, lowercase,
  one idea, screenshot test, individual-with-experience voice.
- `qc_botcheck.py` — hard bot-tell gate (length, casing, dashes, banned families, duplicate openers).
- The punch gate + fact gate: skip anything unverifiable; no filler, ever.

No engagement bait, no attention-chasing, NSFW skipped outright, no engagement pods.

## Layout

```
worker/     worker spec, state, gates, fire driver, harvest, prep batch, helpers
ops/        the cron system: scripts + exported prompts + job table
skills/     the operating skills (x-growth-op, x-post-craft)
drafts/     the review queue (owner-approved only) + archive
research/   playbooks, field research, audits
logs/       runtime fire logs (gitignored)
targets/    harvest pools + batches (gitignored)
media/      upload media (gitignored)
```

## Credentials

**None, ever, in this repo.** Login material lives outside the tree
(`~/.config/x-op/x-creds.json`, created interactively by `save_x_creds.sh` with hidden input;
700 dir / 600 file). Scripts read it at runtime; values are never printed, logged, or committed.

## Status

Runs on a VPS via Hermes cron (`ops/cron-jobs.md`). Cadence and engagement are measured from fire
logs; the +24h pass grades every reply and feeds lane/timing calibration. Current focus: verified
Home Timeline impressions via original posts, quotes and author reply-backs — the signals that
actually count toward the program.
