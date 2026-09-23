# x-op cron system (exported 2026-09-23)

| job | schedule | model | deliver | state | skills |
|---|---|---|---|---|---|
| x-op +24h measure + banger report (`3f38ac433cb4`) | `10 1 * * *` | default | local | scheduled | - |
| x-op conversation farm (`485d2e6e8bf5`) | `*/30 6-23 * * *` | default | local | scheduled | - |
| x-op curated banger track (24/7) (`f7b2e108fbdc`) | `5,35 6-23 * * *` | mimo-v2.6-flash | origin | paused | x-growth-op |
| x-op grok fallback watcher (`6ad16f254c07`) | `*/20 * * * *` | default | origin | scheduled | - |
| x-op human lines (daily) (`56c26d272c21`) | `0 3 * * *` | grok-4.7 | origin | scheduled | x-growth-op, x-post-craft |
| x-op nightly engagement audit (`a41aa6db4201`) | `40 23 * * *` | default | origin | scheduled | - |
| x-op rig watchdog (server+browser keepalive) (`9523a34b5173`) | `*/15 6-23 * * *` | default | local | scheduled | - |
| x-op stale cleanup (nightly) (`64c19769ad08`) | `20 0 * * *` | default | local | scheduled | - |
| x-op systems audit (hourly) (`bb7d3b9248db`) | `25 * * * *` | default | origin | scheduled | - |
| x-op trend scout (daily) (`8123453d996f`) | `30 2 * * *` | grok-4.7 | local | paused | x-growth-op |
| x-op utility scout (daily) (`948a45cac221`) | `45 2 * * *` | grok-4.7 | local | scheduled | x-growth-op, x-post-craft |
| x-op worker cycle (24/7 volume arm) (`fff4b48b1810`) | `*/10 6-23 * * *` | deepseek-v4.1-flash | local | scheduled | x-growth-op, x-post-craft |
| x-op worker cycle (today dark-window exception) (`1f084e2cd680`) | `*/20 4-5 * * *` | deepseek-v4.1-flash | local | completed | x-growth-op |
