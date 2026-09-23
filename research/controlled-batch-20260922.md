# Controlled compose batch - mimo-v2.6-flash vs grok-4.7 vs deepseek-v4.1-flash (2026-09-22)

**Method (controlled):** same 6-post pool, same compose prompt, same rules, run through `hermes chat --oneshot` pinned per model, all 54 output lines shuffled blind and judge-scored 1-10.

- Pool (from `targets/harvest-20260922-2150.json`): iPhone 18 Pro battery capacities (@theapplehub) / GTA VI $975k Miami Heat arena (@HeatvsHaters) / The Batman Part 2 ambitious (@DiscussingFilm) / luffy-blackbeard pie recognition (@kiyodia) / local models vs Luna/Sol pricing (@mweinbach) / Reed Sheppard haircut (@NBA).
- Prompt: 3 reply candidates per post; lowercase, no dashes/@/#/links, 45-110 chars, roast > agree, no questions, no compliment-shape.
- Runs: mimo-v2.6-flash/opencode-go, grok-4.7/xai-oauth, deepseek-v4.1-flash/opencode-go.
- Scoring: 54 lines shuffled (seed 43), scored blind before unblinding. 7.5+ = screenshot-grade, 7 = strong, 6.5 = solid, 6 = fine, <6 = flat.

## Results

| model | mean | >=7 lines | >=7.5 lines |
|---|---:|---:|---:|
| grok-4.7 | **7.03** | 16/18 | 3/18 |
| deepseek-v4.1-flash | **7.03** | 13/18 | 7/18 |
| mimo-v2.6-flash | 6.61 | 7/18 | 2/18 |

## Best lines per model

**mimo** (6.61):
- 7.5 - "vice city on real hardwood is the only place it runs at 60fps"
- 7.5 - "the entire war traces back to one man's opinion of dessert"
- 7.0 - "the heat court has more vice city budget than the game has release dates"

**grok** (7.03):
- 7.5 - "every sequel gets called ambitious and different right up until the same rain shows up"
- 7.5 - "ambitious and different is what you say when the suit still has the same eye holes"
- 7.5 - "975k to paint a fake city on a real court and the players still won't dribble in character"

**deepseek** (7.03):
- 8.0 - "luffy's memory palace is just a bakery with a guy attached to it"
- 7.5 - "rockstar spends 975k on arena paint and will still ship the pc version in 2031"
- 7.5 - "rockets media day: one (1) haircut, pending deletion"

## Read

- grok and deepseek tie on mean (7.03); deepseek owns the top end (7 lines >=7.5 vs grok's 3); mimo trails ~0.4 with the fewest strong lines (2/18 >=7.5).
- mimo stays the ops pick: 0 failed calls in 291, 0 throttles, day's highest reply pace. But if raw line ceiling matters most, deepseek/grok compose sharper on the same pool.
- n=18 lines/model - directional, not gospel. Rerun as needed: `hermes chat --query-file /tmp/batch-prompt.txt --oneshot -m <model> --provider <provider>`.
