# Worker model comparison - deepseek-v4.1-flash vs grok-4.7 vs mimo-v2.6-flash (2026-09-22)

*Compiled from real logs: fire logs, agent.log + agent.log.1 (worker sessions), reply ledger. Windows by pin: deepseek 06:00-10:50Z, grok 10:50-18:35Z, mimo 18:35Z onward (running).*

## 1. Controlled batch scoring (same pool, same rules, line-by-line scored)

| model | mean score | notes |
|---|---:|---|
| deepseek-v4.1-flash | **8.1** | highest floor; best batch |
| grok-4.7 medium | 7.7 | close second; weak tail lines |
| grok-4.7 high | 7.5 | more abstract, less grounded |
| grok-4.7 low | 6.8 | clunkiest |
| mimo-v2.6-flash | _pending_ | controlled batch not run - fresh sample below |

All batches: 0 hard QC flags.

Fresh blind sample (21:50Z, n=12 fired replies per window, same judge rubric): **grok 6.38** (5/12 lines >=7), **mimo 6.00** (3/12), **deepseek 5.71** (0/12). Different pools/day-parts - directional only, not controlled.

## 2. Operational data - today's live windows

| metric | deepseek | grok | mimo |
|---|---:|---:|---:|
| waves fired | 15 | 14 | 6 |
| reply attempts | 147 | 238 | 82 |
| hits | 139 | 226 | 77 |
| hit rate | 95% | 95% | 94% |
| restricted skips | 7 | 11 | 1 |
| THROTTLED signals | 0 | 0 | 0 |
| other failures | 1 | 1 | 4 |

## 3. Model API behaviour (worker calls)

| model | calls | median latency | avg latency | max latency | failed calls |
|---|---:|---:|---:|---:|---:|
| deepseek-v4.1-flash | 436 | 8.1s | 15.2s | 232.7s | 1 |
| grok-4.7 | 650 | 7.3s | 15.0s | 395.8s | 4 |
| mimo-v2.6-flash | 291 | 8.0s | 18.8s | 287.5s | 0 |

## 4. Cycle behaviour (worker sessions)

| window | sessions | avg cycle length | model mix | error lines | timeouts | 429s |
|---|---:|---:|---|---:|---:|---:|
| deepseek | 8 | 30 min | grok-4.7 x1, deepseek-v4.1-flash x7 | 1 | 0 | 1 |
| grok | 15 | 24 min | grok-4.7 x15 | 4 | 4 | 0 |
| mimo | 5 | 33 min | mimo-v2.6-flash x5 | 0 | 0 | 0 |

## 5. Replies logged (ledger)

| window | replies |
|---|---:|
| deepseek | 127 |
| grok | 225 |
| mimo | 91 |
| **today total** | **443** |
| ledger all-time | 949 |

## 6. Read

- **Speed:** medians are near-identical (deepseek 8.1s, grok 7.3s, mimo 8.0s); mimo's average is slightly higher (18.8s vs 15.0-15.2s) on a few slow calls. Long max latencies (230-400s) appear in all three windows - those are big compose outputs, not hangs.
- **Reliability:** deepseek hit opencode-go's daily cap (HTTP 429) at 10:39; grok logged 4 failed calls / 4 timeouts; **mimo: 0 failed calls in 291, 0 throttles** - its 4 non-hit fire outcomes were benign skips (1 restricted box, 3 no-article), not errors.
- **Volume:** mimo's window runs the day's highest reply pace (14 -> 19 -> 27 -> 31+ per hour; 91 replies in ~3.2h, still climbing).
- **Quality:** controlled candidate-batch scoring has deepseek first (8.1 vs grok 7.7); the fresh fired-reply sample has grok first (6.38 vs mimo 6.00 vs deepseek 5.71). Both are real reads of different things (candidate ceiling vs fired mix) - a controlled mimo batch is the next hard test.
- **Caveat:** windows are different day-parts with different pools; operational table is directional. Quality verdict comes from scoring.
