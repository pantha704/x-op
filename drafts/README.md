# x-op draft queue — the single review point for ALL posts

**Owner rule (2026-09-22):** every post is drafted for review before firing. Replies stay autonomous; **posts never auto-fire**.

## Files
**UTILITY MEDIA HARD RULE (owner 2026-09-23):** every utility item carries (1) `url:` the tool's working link - also placed as the last line of the draft text so the owner can cut it into a comment - and (2) `media:` the landing-page screenshot/logo, attached to the X draft (`post_draft.py --media`; capture via `ops/shoot_landing.py <name> <url>`).

**QUOTE URL HARD RULE (owner 2026-09-23):** every quote draft carries the target tweet URL as the LAST LINE of the text (post_quote_draft.py appends it automatically; owner cuts it into a comment when posting).

**MULTILINE NOTE (2026-09-23):** JS execCommand inserts get mangled by X's linkify/autosave (first line eaten). post_draft.py / post_quote_draft.py use native typing (cloak_type via snapshot ref) - stable with newlines. Never revert to JS insertText for multiline.

- `DRAFT-QUEUE.md` — posts awaiting review. Lanes: `quote | utility | question | funny | nostalgia | trend`. Status flow: `pending -> approved -> fired` (or `rejected`).
- `TREND-QUEUE.md` — the trend scout's daily research doc (20-30 current items in our genres; owner picks which to turn into drafts).

## X native drafts (owner directive 2026-09-23)
Every draft is ALSO saved as a native X draft so the owner reviews it in his app (Drafts -> Unsent posts).
- Non-quote drafts (utility, funny, trend): `cd /home/ubuntu/x-op && ./venv/bin/python post_draft.py "<text>"`
- **QUOTE drafts: `./venv/bin/python post_quote_draft.py "<target_url>" "<line>"`** — opens via the Quote menu so the quoted post card is attached (plain text is wrong for quotes; card verified before save).
- Inspect the drawer: `./venv/bin/python ops/x_drafts_inspect.py` · delete old drafts by text: `./venv/bin/python ops/x_drafts_cleanup.py`.

## Item format (append; never rewrite others' items)
```
## [DRAFT-<id>] <lane> | pending
- target: <url or none>
- text: "<post text>"
- media: <path or none>
- why: <one line>
- created: <ISO>
```

## Firing (ONLY after owner approval)
- quote: `cd /home/ubuntu/x-op && ./venv/bin/python quote_publish.py <target_url> "<text>"`
- post:  `cd /home/ubuntu/x-op && ./venv/bin/python post_publish.py "<text>" [--media /path.jpg]`
- then set the item's status to `fired` in this file.

## Cadence & mechanics (from the field dossier, 2026-09-23)
- **3–5 originals/day, SPACED across the day — never batched.** The algorithm lifts ONE post per feed-request to slot ~15–16 for accounts under 1,000 followers, and the lift dies at 1,000 impressions — each post needs its own turn.
- **First 30 minutes after posting = the sprint:** reply to every commenter fast (early velocity decides distribution; replies carry 5.0 weight + the mutual-follow boost).
- **The 500K math:** verified impressions ≈ 2–5% of views → 500K/90d ≈ 10–25M views. Consistency for 90 days; the rolling window punishes dead weeks.
- **No links in the post, 0–2 hashtags max, captions on video, compact card (1–2 lines + media).**

## Voice rules for every draft
`targets/voice-spec-g.md` applies (lowercase; no dashes/@/#/links; 45-110 chars; one idea; interaction hook baked in, never a bare question; **never chase attention** — no thirst, no bait, no notice-me energy; fluid and genuine).
