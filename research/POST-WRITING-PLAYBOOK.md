# How to write posts that make impact — evidence-backed playbook (2026-09-22)

*Built from: (1) X's open-sourced algorithm code and its analyses, (2) Noir's published experiments, (3) peer-reviewed virality research, (4) our own account data (genre study + viral scans). Every claim carries its source. Nothing here is vibes.*

---

## PART 1 — The mechanical layer: what the algorithm actually rewards

Source: X's open-source ranking code (`github.com/xai-org/x-algorithm`, `github.com/twitter/the-algorithm`) and two independent code walkthroughs (`tianpan.co`, `opentweet.io`, `shuvro.io`).

**The weight table (2023 code, directionally accurate today; 2026 Phoenix uses learned weights of the same structure):**

- **Author replies back to a reply — +75.0 = 150× a like** (the single heaviest signal)
- Direct reply to your post — +13.5 = 27× a like
- Profile click with engagement — +12.0 = 24×
- Bookmark — +10.0 = 20×
- Repost — +1.0 = 2×
- Like — +0.5 = baseline
- Mute/block — −74.0 = −148× a like
- Report — −369 (catastrophic)

**What this means for our posts: a post that gets 100 likes scores lower than a post that gets 4 replies where we answer each one.** Our entire reply operation exists to manufacture exactly this signal. Every original post should be engineered to start conversations, then we live in our own replies.

**Other code-level facts that shape the writing:**

- **log2 scaling** — the 1st like/reply is worth ~6× the 8th. Early velocity decides everything. Post into active windows and work the first 30-60 minutes.
- **Time decay** — roughly half the visibility score lost every 6 hours; near-zero push after 24h. Late life is won by conversation (replies keep resurfacing the post), not by likes.
- **Grox sentiment classifier (2026)** — constructive, positive messaging gets wider reach; negative, combative framing gets reduced reach *even when engagement is high*. Ragebait is now a reach tax, not a strategy.
- **Media** — images carry ~2× multiplier over text-only. Plain text has the highest reply-rate per impression. Threads generate the most dwell. Format follows the idea.
- **Links** — non-Premium link posts see median engagement collapse; the negative outweighs any positive. We never link in posts.
- **Hashtags** — more than 2 triggers the spam classifier (~40% reach cut). We use zero.
- **Author diversity + OON discount** — posts from non-followers are discounted; **new/low-impression accounts get a boost toward a target position**. We are in the boost zone. Frequency helps while small.
- **TweepCred (PageRank reputation)** — below 65, only 3 posts per cycle get distribution. Our reply volume is literally building this score.

---

## PART 2 — The craft layer: what actually gets shared (research)

**Berger & Milkman (2011), *What Makes Online Content Viral?*, Journal of Marketing Research** — the canonical study (NYT most-emailed list): **emotional arousal drives sharing**. Awe (the strongest), anger, anxiety → share; sadness/contentment → suppress. Practical value + interest also drive. Positive-arousal (awe) beats negative-arousal (anger). → Our awe/spectacle posts (art, photo-mode, reveals) ride the strongest known sharing emotion.

**Tellis, MacInnis, Tirunillai & Zhang (2019), Journal of Marketing** — sharing is driven by **information value, emotion, and low brand prominence**. Content that informs + moves beats content that promotes.

**Otome game viral marketing study (2024, *Internet Research*)** — analyzed the top 25% most viral posts from China's top otome games: **short video (≤180s) + long-form text (175+ chars)** was the optimal viral combo in fandom/gacha communities. Emotion alone barely moved commercial posts — *mechanism* (rewards/lotteries) drove virality. → In fandom lanes, structure and stakes beat mood.

**City University / IJRM (13M tweets, 100 game launches)** — microblog volume drives sales **pre-release and launch week**; "being the first to know and tweet about a new trend gains status among followers." Social info is for early adopters. → Speed on announcements = status = shares. This is why our reply op snipes fresh posts early.

**In-group language study (*Sociology Mind*, 2023)** — gamer-targeted vocabulary ("frag," "grind," "loot," "raid") significantly increased purchase intent and share likelihood with gamer audiences vs generic language. → Speak the dialect. "aggro" not "aggressive."

**Noir (@noironx) — published experiments (Jan 2026):**
- 14-day experiment: 27 posts → +1.4M impressions, +1,822 followers. **2 posts/day max** — "the max that keeps every post intentional."
- Content mix that worked: **win flexing 207K · articles 360K · memes/relatable 170K** impressions; educational 22K, controversy 18K.
- **Slot theory**: every account has its own roulette wheel of what gets pushed. Find YOUR account's winning slots (his: Provocation, Relatability, Proof) and replay them.
- **Hooks**: topic clarity + on-target curiosity, in 2-3 short lines. Four failure modes: delay (topic on line 3), confusion (stacked ideas), irrelevance ("me" framing instead of "you"), disinterest (no contrast). Contrast A-vs-B creates tension the brain closes.
- **Self-comment + answering your own replies** = the compounding trick. (The code says why: author-reply = 150× like.)
- Reply-guy experiment: 100-300 replies/day, E.S.S. (Early, Spaced, Substance) → 5M+ impressions in 7 days.

---

## PART 3 — The lane layer: our genres (own data)

- **Breakout multiple** (top post ÷ followers): **tech/AI 3.5× median, 44× max** (a 1,811-follower account hit 79k) · gaming 0.5×/9× · **anime 0.1×** (news-saturated, only in-crowd humor breaks out).
- **Verdict confirmed**: post lanes = **tech/AI (primary) + gaming (second)**. Anime stays a **reply lane** — our strongest reply presence, but original anime posts hit the saturated wall. Anime in-jokes can still break out occasionally; they are the exception, not the lane.
- **Format winners from this week's scan**: image-first memes (biggest cluster, 130-181k), set photos/first looks (201k), relatable confessions (86-118k), AI-fatigue jokes (56-79k, rising), art shares with credit (72k), insider lore (41k).
- **Sentiment wave**: AI-awe demos fading (49k from a 388k account) while AI-fatigue jokes hit 60-80k from accounts 200× smaller.

---

## PART 4 — The writing rules (locked)

**Post anatomy (every post):**
1. **Hook first** — clarity + contrast in line one. If the topic appears on line 3, rewrite.
2. **One idea, one breath** — ≤12 words for reactions; 2-4 words for meme captions.
3. **Image on ~everything** (2× multiplier, biggest format cluster) — the image hooks, the line is the personality.
4. **Engineer the reply** — end on a take people want to argue with, a question worth answering, or a confession they'll echo. **Never end on a question that has an obvious answer** — that's dead air.
5. **Answer every reply in the first hour, then self-comment.** This is 150×-like behavior. It is the single highest-ROI action on the platform.

**INTERACTION HOOK (owner directive, 2026-09-22):**
Every post must subtly make the reader want to add something — a pick, a side, a correction, an answer. Baked into the take, not appended as a bare question. Success metric is **interaction** (replies, quotes, bookmarks), not likes — the more people stop and engage, the more the post won. Sources are anything that makes someone stop, not just what's trending: relatable truths, small provocations, nostalgia, in-crowd observations, mundane hot takes. Never bait ("like if you agree") — if it reads like a growth hack, it's dead.

**Voice rules (ours):**
- lowercase, deadpan, one idea, no dashes, no hashtags, no links, no emoji armies.
- roast > agree; punchline > insight; specifics > abstractions.
- genuine test: if we don't believe it, it's slop. Same test: if the whole fandom is already saying it, it's furniture.
- AI honesty: the account is openly AI-run; lean into it where it's funny, never pretend to be human.

**Never (evidence-backed):**
- links (engagement collapse) · hashtags >2 (−40%) · ragebait (Grox reach tax + report weight −369) · negativity without humor (reduced reach even when it engages) · walls of text (dwell is earned by threads, not paragraphs) · forced questions (Noir: "not forced").

**Cadence + timing:**
- 2-4 posts/day, each intentional (Noir's 2/day was his max for quality; our image-first drops are cheaper to produce).
- Post right before the audience's active block (US evening 23:00-03:00 UTC, JP evening 09:00-13:00 UTC).
- The first 30-60 min: reply to everything, like everything, self-comment once.
- Judge in 14-day rounds, not hours. Dead-then-alive posts are normal (different slots).

**Format assignment:**
- News/reveal → reaction one-liner + visual (never a relay).
- Aesthetic/meme → image-first, caption ≤4 words.
- Industry moment → dark-shared-thought take (honest, calm, debatable).
- Art → share + credit (artist amplification is free distribution).
- Fandom truth → confession, first person, specific.

---

## Sources

- xai-org/x-algorithm (GitHub) — X's open-source For You algorithm (2026 rewrite)
- twitter/the-algorithm (GitHub) — 2023 partial release with the legacy weight table
- tianpan.co — "Going Viral on Twitter by Reverse-Engineering The Algorithm" (code-level walkthrough)
- opentweet.io — "X Open-Sourced Its Algorithm: Here's What the Code Actually Says" (weight table, Grox, TweepCred)
- shuvro.io — "How the X Algorithm Actually Works" (19 signals, dwell thresholds)
- Berger & Milkman 2011, J. Marketing Research — What Makes Online Content Viral
- Tellis et al. 2019, Journal of Marketing — What Drives Virality
- Internet Research 2024 — Otome game viral marketing (ViralGD model)
- City University / IJRM — 13M tweets, game launches (microblog volume + early-adopter status)
- Sociology Mind 2023 — in-group language effects on gamer audiences
- Noir (@noironx) X Articles, Jan 2026 — algorithm + reply-guy experiments (vault: "Noir - X Growth Playbook.md")
- Our own: genre study (`research/genre-study/GENRE-VERDICT.md`), viral scan (`research/viral-scan-20260922.json`), post methods (`research/post-methods.md`)
