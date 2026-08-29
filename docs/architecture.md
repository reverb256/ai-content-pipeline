# Architecture — AI Content Pipeline

> How the system is put together. Read this before changing the design.

## The Loop

```
idea → research → angle → long-form → distribution → review → performance → updated playbooks
```

Every stage is a kanban column or a bot artifact. The loop closes when
performance updates the playbooks and the next campaign starts from accumulated
judgment.

## Layers

| Layer | Tech | Owns |
|-------|------|------|
| Brain | git repo (`brain/`) | Voice, audience, proof, offers, RULINGS.md, playbooks (incl. viral-moments) |
| Bots | Hermes profiles (`~/.hermes/profiles/<name>/`) | One decision per bot, one artifact returned |
| Coordination | Bot Mode (Hermes Desktop) + CLI | Visible roster, group chats, @mentions, DMs |
| Production desk | Hermes kanban (sqlite) | Durable task state, handoffs, review, human gates |
| Platform interaction | CDP browser + captured APIs | Search, analytics, publishing as reverb256 |
| **Viral-moment engine** | `brain/playbooks/viral-moments.md` + clip pipeline | Outlier detect → decode → clip → convert. The strategist names entryways, the writer builds clip-ready sections, the distributor cuts clips, the review gate checks standalone value |
| Automation | cron / systemd timers | Discovery, campaign flow, performance loop |

## Bot Roster

| Bot | Decision owned | Returns | Reads |
|-----|---------------|---------|-------|
| scout | Is this worth pursuing NOW? | signal candidate | queries/, brain/index.md, RULINGS.md |
| researcher | Is this claim true and supported? | evidence package | signal, brain/proof.md |
| strategist | What is the story here? | angle brief (incl. distribution entryways) | evidence package, brain/playbooks/angles.md, brain/playbooks/viral-moments.md |
| writer | What is the flagship piece? | long-form draft (clip-ready sections) | angle brief, voice, proof, RULINGS.md |
| distributor | What does each platform need? | platform assets + clip list | angle brief, platforms/, playbooks/platforms.md, playbooks/viral-moments.md |
| editor | Is this ready for the human? | approved/revision (checks standalone value of clips) | all assets, RULINGS.md, voice, proof |

## The Automated Content Machine (separate project — faceless, no personal brand)

An AI-first content factory that finds arbitrage opportunities and produces
content automatically. Uses the same machinery (kanban, profiles, cron,
memlawb) but runs WITHOUT personal brand or manual content work.

```
OPPORTUNITY ORACLE (oracle profile, daily cron 8:30am)
    uses x_search: demand queries + supply-gap queries
    scores: demand × gap × monetization × automation × platform (policy gate)
    routes: niche, format, platform, language — follows the biggest arbitrage
        ↓
CONTENT MACHINE (faceless-youtube kanban board, 8 stages)
    research → script → voice → visuals → thumbnail → SEO → upload → analyze
        ↓
    review gate (human, 90s/batch — avoids demonetization)
        ↓
    platform (YouTube long-form / X / Shorts / translations — oracle-routed)
```

- Playbook: `brain/playbooks/arbitrage.md` (the method)
- Oracle role: `profiles/oracle/role.md`
- Board: `faceless-youtube`
- Video stack: manim-video skill (plan→code→render→stitch→audio), video_gen
  plugin, TTS (xai), ffmpeg
- Cron: oracle-daily-scan (8:30am)
- Revenue: YouTube RPM ($7-25 in high-value niches), affiliate, digital
  products — routed by the oracle per-opportunity

Full method: `brain/playbooks/arbitrage.md`.

```
strategist: angle brief → distribution entryways (proof, mechanism, workflow, risk, result)
    ↓
writer: flagship built with clip-ready sections (each section = a potential standalone)
    ↓
distributor: cut clips → per-platform assets (each clip standalone + CTA-staged)
    ↓
editor: review gate — checks every clip has standalone value + correct stage CTA
    ↓
human: approves publish
    ↓
performance: clip conversion data → updates viral-moments.md playbook
```

Full method: `brain/playbooks/viral-moments.md`. Revenue wiring:
`brain/offers.md`.

## Approval Gates

1. **Angle** — j_kro approves the angle brief before the writer spends hours.
   Taste matters most here; rework is cheapest.
2. **Publish** — j_kro approves every public post. The editor's review queue
   shows final copy, source, platform, media, and the decision required.
3. **Rulings** — performance lessons become permanent playbook rules only
   after j_kro approves.

## Platform Interaction

The headless CDP Chromium (`scripts/browser/`) runs the real reverb256 profile
on port 9222. Bots interact via:
- `browser_exec` (CDP) for flows that need rendering
- captured API endpoints (`platforms/*.md`) for token-efficient direct calls
- `x_search` tool for X discovery

Direct API calls carry session cookies; they are fast, structured, and bypass
DOM parsing. Re-capture endpoints when they drift (401/404).

## Automation

| Job | Schedule | What it does |
|-----|----------|--------------|
| scout run | daily | X search recipes → candidate signals → kanban discovery |
| campaign flow | on-task | kanban dispatcher routes stages through bots |
| performance review | weekly | pull analytics → keep/test/stop lists → kanban |
| browser health | on-boot | media-browser.service keeps CDP Chromium up |

## Host

All of this runs on **zephyr** (Omarchy 4.0.0). The browser, profiles,
keyring, and kanban DB live here. This is the authoring host.

## Decisions

See `docs/DECISION_LOG.md`.
