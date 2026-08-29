# AI Content Pipeline — Agent Guidelines

> **Last reviewed:** 2026-08-29

This repo is the content brain and operating system for a one-person media
company powered by Hermes bots. It is NOT a marketing repo — it is the working
memory, playbooks, campaign records, and automation of a live content operation.

## HARD RULES

1. **Human approval gates are non-negotiable.** Publish approval and angle
   approval always go to the human. No bot publishes, no bot changes voice/
   audience/offer/evidence rules.
2. **RULINGS.md is read before every run.** Every bot reads `brain/RULINGS.md`
   before starting work. Corrections compound; they do not repeat.
3. **No fabricated claims.** Every consequential claim in a campaign must trace
   to a source in the campaign's evidence package. If the evidence is missing,
   return the task to the previous stage — never fill the gap with a plausible
   assumption.
4. **The campaign record is the state.** Chat is for coordination. Files and
   kanban are for state. If a handoff field is missing, the bot returns the task
   to the previous stage. It does not guess.
5. **Never touch cluster ops, mining, or code.** This system produces content.
   It does not manage infrastructure.

## Repo Layout

```
ai-content-pipeline/
├── brain/                  ← shared editorial knowledge (the "content brain")
│   ├── index.md            ← entry point every bot reads first
│   ├── voice.md            ← tone, stance, what we sound like
│   ├── audience.md         ← who we publish for, what they care about
│   ├── proof.md            ← evidence, credentials, receipts
│   ├── offers.md           ← what we sell / what the audience can take
│   ├── RULINGS.md          ← every correction, permanent knowledge
│   └── playbooks/          ← hooks.md, angles.md, platforms.md, performance.md
├── platforms/              ← per-platform playbooks + API catalogs
├── campaigns/              ← one folder per campaign (the handoff record)
├── performance/            ← numbers + weekly review outcomes
├── queries/                ← saved X search query recipes per pillar
├── profiles/               ← canonical SOUL.md + config.yaml for each bot
├── scripts/                ← browser, API clients, publish helpers, automation
├── docs/                   ← architecture, decisions
├── AGENTS.md               ← this file
└── README.md
```

## The Campaign Record

Every campaign has ONE record that travels through the system:

```
campaign: <name>
status: <stage>
signal: event, source, urgency, audience question
research: verified claims, sources, authority clips, contradictions, unknowns
angle: reader, outcome, tension, thesis, reusable object
flagship: format, path, approval state
distribution: x, substack, youtube, blog assets
review: issues, final decision
performance: observations, proposed rule changes
```

The record lives in `campaigns/<campaign>/` as markdown files. It gives the
next bot a predictable input and lets you inspect history without reopening
six conversations.

## Pipeline Stages

```
discovery → research → angle → draft → distribution → review → publish → performance
```

| Stage | Bot | Returns | Gate |
|-------|-----|---------|------|
| discovery | scout | signal candidate | — |
| research | researcher | evidence package | — |
| angle | strategist | angle brief | **HUMAN APPROVES** |
| draft | writer | flagship piece | — |
| distribution | distributor | platform assets | — |
| review | editor | approved / revision request | **HUMAN APPROVES PUBLISH** |
| publish | (via API layer) | live post(s) | — |
| performance | (weekly) | playbook updates | **HUMAN APPROVES RULES** |

## Bot Profiles

Profiles live in `profiles/` (canonical source of truth) and are deployed to
`~/.hermes/profiles/<name>/`. Each bot has a SOUL.md defining:
- owns: the decision this bot is responsible for
- reads: the files and handoff fields it may use
- returns: the exact artifact the next bot receives
- must not: decisions that belong to another bot or a human
- done when: observable conditions that make the handoff complete

## Development Workflow

All work goes through issue → worktree → PR → squash-merge → deploy, matching
the established pattern. Docs changes can be smaller but still honor the flow.

## Writing Style

User-facing prose follows ASD-STE100 plus Zinsser: imperative mood, one idea
per sentence, plain words, conclusion first. When unsure, say so; never fabricate.
