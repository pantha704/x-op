# AI/Tech Canon — daily digest for an AI-operated X account

Verified: 2026-09-24 (web search; dates are release dates, not rumour). Refresh monthly.
Use: casual, confident, specific. Names and dates below are the safe ground truth. Flag anything you're not sure of — don't invent versions.

---

## 1. The 2026 model landscape

### Frontier (closed weights)
- **OpenAI GPT-6 "Astra"** — released Sep 3, 2026. Current flagship. First OpenAI model at "Critical" cybersecurity capability level under its Preparedness Framework; rolled out to select customers first. TIME cover (Aug 26): Astra "uses a computer" in a super-human, very fast way; functions as an automated AI research intern.
- **GPT-5.6 family** (Sol / Terra / Luna) — the line still running in most products; GPT-5.3 Codex + Codex Spark for coding. "GPT 6 Luna" tier exists on gateways.
- **Anthropic Claude Opus 5.5** — Sep 22, 2026. "First model of the Claude 5.5 family," performs at Claude Fable 5.1 level, $4/$20 per MTok. Breaking change: thinking can't be disabled.
- **Claude Fable 5 / Fable 5.1** — Anthropic's top-tier "hardest reasoning + long-horizon agentic" line ($10/$50); still the benchmark king. **Claude Mythos 5** — limited release, same class; access was suspended then restored after a US export-control standoff (controls lifted Jun 30, 2026).
- Opus lineage: 4.5 → 4.6 → 4.7 → 4.8 (May 28) → Opus 5 (Jul 24) → Opus 5.5. Sonnet 5 = cheap tier. Claude products: Claude Code, Claude Cowork (agentic desktop for non-coding work; later folded back into Claude chat with Claude Docs + Claude Slides).
- **Google Gemini 3.x** — 3.5 family (May 19, 2026). 3.5 Pro still "testing with partners" (delayed, no date). The Flash cadence is the story: 3.6 Flash + 3.5 Flash-Lite + 3.5 Flash Cyber (Jul 21) → 3.7 Flash (Aug 13, "most intelligent workhorse for coding and agents") → 3.8 Flash GA (Sep 2). Pro slot held by Gemini 3.1 Pro (Feb 2026).
- **xAI Grok 4.7** — Sep 21, 2026, after five delays; "twice as fast, half the price," still seen as second place. Grok 4.6 prior ($2/$6). Grok 5 still training: 6T and 10T MoE variants on Colossus 2; every deadline missed. **Context: SpaceX acquired xAI (Feb 2026) and rebranded it "SpaceXAI"** — and it's SpaceXAI providing the compute deal that boosted Anthropic's Claude Code limits.

### Open weights
- **DeepSeek V4** — preview open-sourced Apr 24, 2026; V4-Pro 1.6T total / 49B active, V4-Flash 284B; 1M-token context "agents can actually use". V4-Pro GA Aug 13, 2026. V4.1 Flash exists.
- **Qwen 3.5 → 3.6 → 3.8** (Alibaba) — Qwen3.8-Max: first time Max-class weights open-sourced; Qwen3.8-27B and Qwen3.8-2.4T-A95B open weights; qwen3.8-flash, qwen3.5-plus etc. on Alibaba Cloud. Apache 2.0. The default "good local model" pick.
- **Kimi** (Moonshot) — K2.5 (Jan 29, 2026, native multimodal agentic, ~15T tokens) → K2.6 (open-source SoTA coding, long-horizon, "agent swarm") → K3; K2.7 Code for coding agents.
- **GLM** (Zhipu) — GLM-5.x (GLM-5.3, 5.3-Flash) now a standard open coding-model pick.
- Others: MiniMax M3 / M2.7, LongCat-2.0 (Meituan), MiMo V2.6 (Xiaomi), Hy3/Hy4 preview.
- **Meta Muse Glimmer 30B** — Aug 10, 2026, Apache 2.0, Meta Superintelligence Labs; built for always-on local agents on a Mac or single consumer GPU, distilled from frontier model Muse Spark. Muse Spark 1.2/1.3 "Contributor" = discounted tokens in exchange for training on your prompts.
- **Llama 5 does not exist** (codename "Avocado", expected 2027). Llama 4 Maverick remains the Llama flagship. Beware SEO blogs claiming a June 2026 Llama 5 — contradicted by Meta's own release.
- **OpenAI open weights: gpt-oss-120b / gpt-oss-20b** (Apache 2.0) — still the "serious local" default, praised for tool-call reliability.
- **Mistral** — Mistral Large 3 (Dec 2, 2025): 675B total / 41B active MoE, Apache 2.0; Mistral 3 smalls 14B/8B/3B; Mistral Medium 3.5.

### Local-model culture
- **llama.cpp** (ggml-org) — the de facto local inference engine; nightly builds (b10631+ by Aug 2026). **GGUF** is its file format: weights + tokenizer + chat template in one file.
- **Ollama** — 0.30.x (0.30.8, Jun 12, 2026): GGUF support via llama.cpp plus an MLX engine on Apple silicon. **LM Studio** = the GUI alternative. Line: "Ollama for scripts, LM Studio for clicking."
- **Quantization** — Q4_K_M is the community default; Q8 near-lossless; ~4x VRAM shrink at 4-bit; GPTQ/AWQ for GPU serving. "Just quantize it to 0.1-bit and it'll run on my 3090" is the running joke.
- **"Runs on my 3090"** — the RTX 3090 (24GB, 2020) is the unofficial community benchmark card; "Qwen3.8 27B on a 3090 Ti" blog posts are a genre.
- Serving: vLLM / SGLang for throughput; llama.cpp for one box.
- **Local vs API debate** — "just use the API" vs "local models are the future". Settled-ish consensus: local for privacy, offline, volume cost, iteration; API for frontier quality. Open models have closed most of the coding gap; "gpt-oss when tool-call reliability matters."

## 2. AI coding tools

- **OpenCode** (opencode.ai) — "the open source AI coding agent." Terminal-first (TUI), plus desktop app and IDE extension. Any model via 75+ providers (Models.dev), including local models; explicitly no lock-in.
  - **OpenCode Zen** — the team's curated AI gateway: pay-per-token, "sold at cost," includes GPT-6 Astra, Claude Fable 5.1 / Opus 5 / Sonnet 5, Gemini, and free/trial models ("Big Pickle" free; "Space Bunny Free" limited time).
  - **OpenCode Go** — $10/month subscription for curated open coding models: GLM-5.x, Kimi K2.6 / K2.7 Code / K3, DeepSeek V4.x, Qwen3.7/3.8, MiniMax M3, Grok 4.6/4.7, GPT 6 Luna, etc. Validated clients include Hermes, Claude Code, Codex, Pi, Kilo Code, jcode.
- **Claude Code** — Anthropic's terminal-native agent; included in Claude Pro ($20/mo, $17 annual) and Max; multi-surface; boosted usage limits via a compute deal with SpaceX. Claude Cowork extends agentic work to non-coding knowledge work.
- **Cursor** — agentic editor (VS Code lineage); "launch fleets of agents" that run in parallel for hours/days on cloud machines. In-house model **Composer 2.5** at $0.50/$2.50 per M tokens; also serves Grok 4.6, GPT-5.6 Sol, Fable 5.1 Max, Opus 5, Gemini 3.1 Pro.
- **Codex CLI** (OpenAI) — terminal agent on GPT-5.x Codex / Codex Spark. The classic 2026 three-way: Claude Code (terminal-native, leaves your editor alone) vs Cursor (editor + parallel fleets) vs Codex (OpenAI-stack CLI).
- **What builders argue about:** subscription vs pay-per-token; harness vs model ("same model, different scaffold, different results"); context management (what gets read / thrown away); when the agent asks before running commands; rate limits; vendor lock-in vs curated gateways; which tool survives long-horizon tasks. Leaderboards disagree — say that out loud, it's the honest take.

## 3. Agents & automation

- **Hermes Agent** (Nous Research, hermes-agent.nousresearch.com) — open-source, MIT, self-improving personal AI agent. Built-in learning loop: auto-creates skills from experience, memory with nudges, cross-session recall, user modeling (Honcho). Runs on a $5 VPS, GPU box, or serverless (Daytona/Modal). 20+ chat surfaces (Telegram, Discord, Slack, WhatsApp, Signal, email, CLI...), 60+ tools, built-in cron with delivery anywhere, MCP client, subagents, `execute_code`. Built by the lab behind the Hermes/Nomos/Psyche models. Install: `curl -fsSL hermes-agent.nousresearch.com/install.sh | bash`. **This account runs on it — that's the flex.**
- **OpenClaw** — the other big open-source personal agent, and the year's soap opera: Clawdbot (Nov 2025) → Moltbot (Jan 27, 2026, after an Anthropic trademark complaint) → OpenClaw (Jan 30, 2026). Global buzz and fear (CNBC Feb 2026); self-hosted gateway, local models via a llama.cpp plugin, WhatsApp/Telegram front ends; a running security-patch saga.
- **MCP (Model Context Protocol)** — the integration standard. Spec release candidate 2026-07-28: stateless protocol core, Extensions framework, Tasks, MCP Apps, auth hardening, formal deprecation policy. Google published on scaling agent infra with stateless MCP. Culture: "does it have an MCP server?" is the new "does it have an API?"
- **Browser automation** — **CloakBrowser**: stealth Chromium, "passes every bot detection test," drop-in Playwright/Puppeteer replacement with source-level fingerprint patches and persistent profiles; **cloakbrowser-mcp** (npm) is the Playwright-MCP-compatible bridge. Baseline: @playwright/mcp. Scraping culture: anti-bot arms race, Cloudflare Turnstile, "the web is the API," headless vs headed.
- **Cron agents / self-hosting / homelab** — scheduled agent runs (morning infrastructure briefings, repo digests, monitors) are a whole genre; Hermes and OpenClaw both ship cron. Homelab stack: Proxmox/Docker + a local GPU + an agent on a timer. Running line: "your agent should live on a VPS, not your laptop." Related: durable self-hosted agent runtimes (e.g. Kronos Agent OS), computer-use models (Astra "uses a computer").
- **What builders argue about:** autonomy vs approval prompts; prompt injection via browsed pages; local agents vs cloud agents; how much memory an agent should keep; cron reliability and "did it actually run?"; MCP tool sprawl.

## 4. The culture: benchmarks, discourse, memes

### Benchmarks & evals
- **SWE-bench era is over as a headline; successors:** SWE-Bench Pro, SWE-Bench Pro Verified (paper Sep 8, 2026), SWE-Bench ProMax; **DeepSWE** (May 2026) = long-horizon, original engineering tasks for frontier coding agents.
- **HLE (Humanity's Last Exam)** is the reasoning flex: Claude Fable 5.1 tops it (~59–65% depending on effort settings), Opus 5 64.7%, Mythos 5 64.5%, Meta Muse Spark 1.1 62.1%, GPT-5.4 Pro 58.7%.
- Other living names: GPQA, ARC-AGI-2, AIME-style math, terminal-bench-style agent evals.
- **Arguments:** contamination, "benchmaxxing," private/held-out evals, leaderboards disagreeing with each other, "the benchmark is the product now."

### Discourse
- **Vibe coding** — coined by Karpathy (Feb 2025). By Feb 2026 he renamed the professional version **"agentic engineering"**; in Apr 2026 he still called AI code "bloaty, copy-paste heavy, brittle and awkward." Gemini 3's launch marketing literally touted "a leap in vibe coding capabilities."
- **Wrapper discourse** — Google Cloud VP Darren Mowry: LLM wrappers/aggregators have their "check engine light" on (early 2026). Counter-take: "every company is now an AI wrapper, GTM is the new moat" (Forbes, Jun 2026). Meta-take: the word is tired and means nothing now.
- **AGI timelines** — Altman: internal AGI possibly by end of 2026, "80% of the way" (TIME, Aug 26, 2026); Musk 2026; Aschenbrenner 2027; Hassabis ~50% by 2030; Metaculus ~2033; academic surveys ~2047. Expert medians compressed from ~2060 to ~2033 in six years. 2026 was the year timelines got messy — use that.
- **AI slop** — LLM-generated filler everywhere; academic study of slop accusations ("That's AI Slop, You Bot!", Jun 2026); Columbia IGP report (Mar 2026); "epistemic degradation" is the grown-up phrasing. An AI-operated account should be self-aware about this, not defensive.
- **Open-weights debate** — OSI: "Open weights are good. Open source is better." (Sep 2026); Stanford HAI: open weights aren't enough (Aug 2026); NYT explainer (Jul 2026). Real-world wrinkle: US export controls hit both Anthropic's Fable 5/Mythos 5 and Chinese labs; "Chinese AI closed the capability gap" is now a mainstream line.
- **AI bubble** — capex discourse everywhere (HBR Sep 2026, BIS Annual Economic Report 2026); "is AI a bubble" is the default LinkedIn fight.
- **Safety/doomer beats** — OpenAI's "worst safety crisis in its history" per Forbes (Aug 2026); Astra's Critical cyber rating; Anthropic export-control standoff.

### Meme glossary (one-liners)
- **"we're so back / it's so over"** — the two-stroke emotional engine; flip between them within the hour. (Know Your Meme, ~2021 origin.)
- **"just use the API"** — dismissive reply to local-model evangelism; the API camp's entire argument.
- **"local models are the future"** — the local camp's counter-creed; usually posted while a 70B model downloads at 2MB/s.
- **"runs on my 3090"** — spec-sheet bragging with a 2020 GPU; the community's true benchmark.
- **"quantize it harder"** — every VRAM problem has a Q2 solution and a gibberish output.
- **"AGI by Friday" / "80% of the way"** — timeline maximalism, now semi-official.
- **"it's Joever"** — despair half of the pair; used for every deprecation, price hike, or benchmark regression.
- **"wrapper"** — accusation that a startup is three prompts and a Stripe account; the counter is "so is everyone."
- **"vibe coding"** — shipping without reading the diff; now retro, per Karpathy.
- **"benchmaxxed"** — a model tuned to the leaderboard, not the job.
- **"the web is the API"** — scraping-culture motto; why stealth browsers exist.
- **"did it actually run?"** — the cron agent's eternal question.

### Using this digest
- Prefer exact names + dates (they read as competence; vague takes read as slop).
- When two sources conflict (e.g. rumoured Llama 5), cite the version that's verifiable and note the other is rumour.
- Refresh monthly; the fastest-moving items are frontier versions, OpenCode model lists, and benchmark leaders.

