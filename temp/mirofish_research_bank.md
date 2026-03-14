# MiroFish — Research Bank (for Twitter Article)

Date compiled: 2026-03-11 (Europe/Moscow)

Goal: build a pile of facts + plausible claims + “smart-sounding but understandable” concepts to later assemble into a viral Twitter Article.

---

## 1) What MiroFish is (plain language)

- “Crowd simulator” for information shocks: you feed a seed text (news / report / policy draft / story) and it spins up a parallel digital society of LLM agents that interact, form factions, argue, amplify narratives, and produce an outcome as a forecast report + an interactive world.
- It’s not “predict the world” directly; it’s “predict the conversation about the world” (which often drives the world).

---

## 2) Hard facts (safe to state as facts)

- Repo: `666ghj/MiroFish` on GitHub (AGPL-3.0 license).
- Stars/forks are public and update constantly; as of 2026-03-11 it’s ~13k+ stars (use live number at publish time).
- Docker deploy is supported via `docker compose up -d`.
- Default ports: `3000` (frontend) and `5001` (backend).
- Docker image: `ghcr.io/666ghj/mirofish:latest`.
- Inputs: user uploads seed materials (PDF/MD/TXT/Markdown) + writes forecasting requirement in natural language.
- Output: (a) detailed forecast/prediction report, and (b) a “high-fidelity digital world” you can interact with.
- The simulation engine is powered by CAMEL-AI’s OASIS (Open Agent Social Interaction Simulations).
- Backend dependencies explicitly include: `zep-cloud`, `camel-oasis`, and `camel-ai`.
- Two simulation “platform modes” exist in code/config: Twitter-like actions and Reddit-like actions.

### Source links (for you, not necessarily for the article)

- GitHub: https://github.com/666ghj/MiroFish
- README (EN): https://github.com/666ghj/MiroFish/blob/main/README-EN.md
- Backend deps: https://github.com/666ghj/MiroFish/blob/main/backend/pyproject.toml
- Config (platforms/rounds): https://github.com/666ghj/MiroFish/blob/main/backend/app/config.py
- OASIS: https://github.com/camel-ai/oasis

---

## 2.1) “Reported” facts (use wording like “reportedly / according to …”)

- “Strategic support and incubation from Shanda Group” is stated in the project’s own README (safe to quote as “project claims”).
- Funding amount “30 million yuan” appears in Chinese media writeups; BUT one prominent writeup contains an internal inconsistency (“300 million” vs “30 million” in the same piece). Treat the exact amount as “reported” unless you find a primary statement from Shanda/Chen Tianqiao.

Sources:
- README mention: https://github.com/666ghj/MiroFish/blob/main/README-EN.md
- Media writeup (contains inconsistency): https://www.tmtpost.com/7905996.html

---

## 2.2) Ecosystem / author credibility (use for FOMO + “track record”)

The author `666ghj` has other viral repos in the same “agents” lane:

- BettaFish (other repo, very large star count; check live number at publish time): https://github.com/666ghj/BettaFish
- MindSpider (another repo; also big): https://github.com/666ghj/MindSpider

Angle: “This isn’t a one-off. He’s shipping a whole stack: data → agents → simulation.”

---

## 2.3) The “deploy in minutes” reality check (pitfalls from issues)

Stuff people are already tripping on (useful for “you can be early because others will bounce”):

- Zep Cloud free tier / API rate limits → simulation stuck ~99% or slow profile generation (multiple issues mention this).
- CPU/architecture friction: no ARM image published yet (Mac M-series users complain); might require building locally.
- “It runs” ≠ “it’s cheap”: large simulations can burn tokens fast depending on model and rounds.

Sources (examples):
- Rate limit / stuck: https://github.com/666ghj/MiroFish/issues/99
- Rate limit: https://github.com/666ghj/MiroFish/issues/121
- ARM request: https://github.com/666ghj/MiroFish/issues/105

---

## 2.4) What the system ACTUALLY simulates (concrete nouns)

It simulates:

- agents with personas (identity-ish fields, preferences, triggers, stance)
- a social platform dynamic (either Twitter-like or Reddit-like)
- sequential “rounds” of posts/comments/likes/retweets/follows/search/trends
- memory updates (agents carry state across rounds)
- emergent “macro” stuff (dominant narratives, factions, cascades)

It does NOT natively simulate:

- the real market microstructure (order book, funding, liquidation cascades)
- real-world constraints (law enforcement timelines, supply chains) unless you encode them into agent rules/prompts
- ground-truth truth (LLMs will hallucinate if you let them)

---

## 2.5) Env / knobs (so you can talk about “control panel”)

From `.env.example` (paraphrased; check file for exact names):

- LLM: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL_NAME`, `TEMPERATURE`, `MAX_RETRIES`, `REQUEST_TIMEOUT`
- “Boost / cost / scale”: `LLM_BOOST` (project-specific knob), `MAX_ROUNDS`
- Zep Cloud: `ZEP_API_KEY`, `ZEP_API_URL` (plus collection/project identifiers)
- Infra: `BACKEND_PORT`, `FRONTEND_PORT`, `LOG_LEVEL`

Source:
- https://github.com/666ghj/MiroFish/blob/main/.env.example

--- 

## 3) What it can output (artifacts you can describe)

### A) “Forecast report” (human-readable)

- Structured, multi-section report (looks like a consulting memo / analyst note).
- Includes reasoning + scenario trajectories + “why different groups react differently”.

### B) Interactive “world” you can interrogate

- Knowledge graph / relationship graph visualization (entities + edges).
- Agent profiles/personas generated from extracted entities.
- Simulation timeline (rounds) with dynamic memory updates.
- Ability to “interview” any agent (ask: what do you believe, what do you do next, what changed your mind?).
- A “ReportAgent” that uses tools to query the simulated environment and compile the report.

### C) Machine-readable / operational artifacts (API side)

- APIs to fetch filtered entities from a graph.
- APIs to create simulations, prepare (async) a simulation environment, check status, fetch profiles.
- Simulation history includes fields like `entities_count`, `profiles_count`, `total_rounds`, `current_round`, `status`, etc.

### D) “Explainability” artifacts (super important for credibility)

There’s a persistent simulation state on disk and structured events:

- `state.json` holds simulation environment state (so the run is inspectable).
- Events like `simulation_start` / `simulation_end` are emitted (useful to claim “auditable runs”).
- “Actions” are recorded (platform actions per round) — you can describe it like: “you can replay the crowd’s chain-of-causality”.

Source:
- https://github.com/666ghj/MiroFish/blob/main/backend/app/services/simulation_runner.py

--- 

## 4) How it works (conceptual model you can explain simply)

Think of it like a pipeline:

1. **Seed → Graph**: extract entities/relations from the seed and build a GraphRAG-style memory graph.
2. **Graph → People**: generate personas (agents) from entities (stances, backgrounds, incentives).
3. **People → Society**: run social interaction simulation (Twitter/Reddit action space) for N rounds.
4. **Society → Report**: a report agent interrogates the simulation + tool calls to produce a forecast report.

Key “smart words” you can sprinkle while keeping meaning:

- agent-based simulation
- emergent behavior
- narrative cascades
- coordination / herding
- GraphRAG (graph retrieval-augmented generation)
- personas + incentives
- action space (Twitter/Reddit)
- rounds / temporal memory updates

### 4.1) Under-the-hood pipeline (more specific, still explainable)

Actual internal steps you can name-drop:

- Zep graph read + filter of entities (avoids junk labels, retries, etc.)
- “Profile generator” turns entities into personas and long-term memory
- “Config generator” infers simulation parameters (duration, minutes-per-round, polarization settings, etc.)
- “OASIS” executes the multi-agent social simulation
- “Tools” layer lets the report agent query graph + interview agents + search simulation results

Sources:
- Entity reader: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/zep_entity_reader.py
- Profile generator: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/oasis_profile_generator.py
- Config generator: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/simulation_config_generator.py
- IPC + interviews: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/simulation_ipc.py
- Report agent + tools: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/zep_tools_service.py

### 4.2) The “persona depth” (this is how you justify “patterns of behavior”)

Personas include (seen in generator code):

- name, role, background, interests, communication style
- personality traits (including MBTI-like labels in some branches)
- opinion preferences / stance tendencies
- “emotional triggers”
- long-term memory seed (what they already “believe”)

This is your hook ammo: “not just bots that reply — bots with priors + triggers + memory.”

Source:
- https://github.com/666ghj/MiroFish/blob/main/backend/app/services/oasis_profile_generator.py

### 4.3) The “society knobs” (good ‘smart words’ you can explain)

From config generator, parameters include ideas like:

- `polarization_factor`
- `echo_chamber_strength`
- `viral_threshold`
- total simulated duration (the code suggests “72 hours” style setups)
- minutes-per-round (discretization)

Translate for humans:

- polarization = how quickly we split into camps
- echo chamber = how much people only hear their side
- viral threshold = how easily a meme crosses the room

Source:
- https://github.com/666ghj/MiroFish/blob/main/backend/app/services/simulation_config_generator.py

--- 

## 5) Claims: “maximalist hook” vs “defensible body”

### Maximalist hook (bait; keep as vibe)

- “Simulate almost any situation in minutes.”
- “Predict the crowd with 99% accuracy.”
- “Reverse the crowd → profit.”

### Defensible body (how to make it survive replies)

- Reframe “99%” as: “in many info-driven situations, what matters is the direction + shape of reaction, not exact numbers.”
- Emphasize: the tool maps reaction surfaces, not ground-truth future.
- Claim edge: “You get a better model of *crowd belief dynamics* than your intuition.”

### 5.1) “Reverse the crowd” — what that can mean (choose 1 for the article)

There are 3 different “reverse” meanings; you can pick whichever is spiciest:

1) **Reverse to trade**: identify when crowd belief is at an unstable extreme (panic/mania) → fade it.
2) **Reverse to message**: find what sentence flips the majority (pre-bunk / reframe).
3) **Reverse to design**: engineer incentives/UX so the crowd chooses your desired equilibrium.

All 3 are consistent with “simulate → find levers → reverse.”

--- 

## 6) Use cases (some documented, some plausible)

### Documented / directly implied by project materials

- PR / policy “rehearsal lab”: run a public statement through a simulated society; see what gets attacked and by which factions.
- Creative sandbox: simulate story endings by letting characters act.
- Financial/political prediction examples are “coming soon” per docs; the project already positions itself around those seeds.

### Plausible (speculative, but logical from how it works)

- Crisis comms: try alternate wordings; find the minimum-change patch that prevents a narrative cascade.
- Product launches: simulate what different segments will nitpick, meme, or misunderstand.
- Legal/regulatory drafts: simulate how stakeholders will frame your language, then “pre-bunk”.
- OSINT narrative mapping: if a leak drops, simulate first 24–72h of discourse branches.

### 6.1) “Seeds” that work well (and why)

Seeds that produce strong simulations:

- clear event + uncertainty + high emotions (laws, war, hacks, layoffs)
- a draft statement with ambiguous phrases (lets factions interpret differently)
- a numeric report (earnings, CPI) + a single “surprising” line

Seeds that produce weak simulations:

- too little context (agents hallucinate)
- too much noise (a huge dump without a question)

Trick: always pair seed with a crisp requirement prompt like:

- “Simulate reactions by stakeholder group. Identify top 5 narratives and the turning points.”
- “What’s the most likely misinformation variant and what phrasing preempts it?”
- “Which faction becomes the price-setting narrative in the first 6 hours?”

--- 

## 7) Mandatory section: Prediction markets (Polymarket angle)

Core idea for the article:

- Prediction markets are “Bayes in public”: prices ≈ crowd probability.
- Crowd probability is often contaminated by narrative/attention/panic.
- MiroFish is a tool to model *why* the crowd is at a certain probability — and whether that probability is inflated by herding.

Simple mispricing story (your version, in 3 steps):

1. A shocking event happens → market odds swing to 90% “bad outcome”.
2. You simulate the event as a seed → agents show this is peak-panic narrative (not stable belief).
3. You buy the mispriced side → profit when panic decays and odds mean-revert.

Extra “smart but understandable” angles:

- identify which narrative is price-setting (dominant coalition)
- look for “fragile consensus” (high confidence but low evidence)
- run counterfactual injections: “what if a credible clarification drops?” → estimate how quickly odds unwind

### 7.1) Polymarket mechanics (facts you can drop as “smart words”)

Polymarket is built around a CLOB (central limit order book) for prediction markets (“prices as probabilities” framing).

Official docs:
- Polymarket docs: https://docs.polymarket.com/
- Polymarket CLOB docs: https://docs.polymarket.com/#clob

Useful “smart but digestible” lines:

- “Odds are a compressed representation of crowd belief.”
- “Prices move on information *and* attention.”
- “Illiquidity + narrative shock = mispricing.”

### 7.2) Mispricing playbook (your simple example, expanded)

Vocabulary to sound smart:

- “belief dynamics”
- “attention shock”
- “panic premium”
- “fragile consensus”
- “narrative decay”

How to operationalize it with MiroFish outputs:

- Look for **panic peak** signals:
  - agents converge to extreme probability quickly with thin evidence
  - high emotional language / moral outrage dominates reasoning
  - rapid formation of echo chambers
  - “everyone shares, few verify” behavior
- Then run **counterfactual injections**:
  - add a credible clarification
  - add a denial from a trusted source
  - add a new datapoint that resolves ambiguity
  - see if the crowd belief collapses fast (fragile) or resists (sticky)

Interpretation rule:

- If belief collapses under a minimal credible counterfactual → odds are likely “panic-inflated” (fade).
- If belief persists across counterfactuals → odds are likely “evidence-rooted” (don’t fight).

### 7.3) “Reverse the crowd” in prediction markets (safe framing)

Safe framing (avoid manipulation vibes):

- You are not “controlling” the crowd. You’re measuring when the crowd is irrationally overconfident due to attention cascades.

If you want extra “intellectual aura”:

- “Markets aggregate information; simulation helps you model the information pipeline itself.”

--- 

## 8) FOMO lines (for later)

- “It’s open-source. The playbook is lying on the ground.”
- “The edge exists because people haven’t operationalized crowd simulation yet.”
- “Once this becomes standard in PR/markets, the advantage disappears.”
- “You’re not late — the repo is public, but the workflow isn’t common knowledge.”

### 8.1) Stronger FOMO angles (non-false, but high heat)

- “Open-source is the real alpha leak: the edge isn’t access, it’s implementation.”
- “Everyone can clone a repo. Almost nobody can turn it into a repeatable decision workflow.”
- “First-mover advantage here is building intuition: which seeds produce reliable reaction maps, and which don’t.”
- “Soon every PR shop + macro desk will run crowd sims by default. Right now they don’t.”

--- 

## 9) Things to be careful with (so you don’t get dunked on)

- Investment claims: treat as “reported by X / according to Y” unless you have a primary statement.
- “Guaranteed profit” triggers instant pushback; keep it as a rhetorical line, then pivot to “edge”.
- Don’t imply literal price prediction; it’s sentiment/narrative simulation.
- Mention license (AGPL) if you hint at “deploy as a service”.

### 9.1) Likely reply-attacks + pre-baked rebuttal angles

Attack: “LLMs hallucinate, this is cosplay.”
- Rebuttal: “Yes, so treat it as a *reaction simulator*, not a truth engine. It’s for mapping narratives, not facts.”

Attack: “You can’t predict humans.”
- Rebuttal: “You can’t predict individuals, but you can model *crowd phase transitions* (panic/mania) surprisingly well.”

Attack: “99% accuracy is BS.”
- Rebuttal path (if you want to keep the maximalist hook): “It’s a hook. The real claim: it makes you less blind to second-order reactions.”

Attack: “This is just roleplay.”
- Rebuttal: “Roleplay becomes useful when it’s systematic: many agents, memory, interaction rounds, and observable artifacts.”

---

## 10) Extra ammo: “smart words” glossary (with one-line explanations)

- **Agent-based simulation**: model a system bottom-up via many interacting individuals.
- **Emergence**: group-level patterns not explicitly coded in any single agent.
- **Narrative cascade**: an idea spreads because people see other people spreading it.
- **Echo chamber**: belief reinforcement due to selective exposure.
- **Phase transition**: the moment a conversation flips from calm → panic (or vice versa).
- **Counterfactual injection**: add a plausible new fact and see if beliefs change.
- **Belief dynamics**: how probabilities shift over time with social influence.
- **GraphRAG**: retrieval over a graph of entities/relations to ground generation.
