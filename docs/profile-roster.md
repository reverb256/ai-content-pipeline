# The Full Profile Roster — A Virtual Company Across All Businesses

> Brainstormed from the X research on virtual AI companies (2026-08-31).
> Structure: SPOC as chief of staff → C-suite → department leads → specialists.
> This covers ALL our operations: content machine, brand track, site-agency,
> maplespike/quill, trovesandcoves, and the infrastructure layer.

## The Research-Backed Principles

1. **Narrow scope beats vague generalists.** Every profile owns ONE decision,
   has a definition of done, and returns one artifact. (Validated across all
   sources + the MIPT study: protocol > model count.)
2. **Company Brain is shared; department brains are scoped.** memlawb = the
   shared brain; each profile has scoped skills/memory.
3. **SPOC is the orchestrator (chief of staff), not a doer.** Routes, reviews,
   escalates. Never does the work.
4. **C-suite owns numbers.** CCO owns content performance, CRO owns revenue,
   COO owns ops health. Each has a KPI.
5. **Rhythm keeps alignment.** Standups, reviews, weekly keep/test/stop.
6. **Model tiering:** frontier for exec/synthesis, free for workers.

## The Complete Org Chart

```
YOU (human — strategy, taste, approvals, money)
  ↓
SPOC / default (chief of staff — orchestrator, review, escalation, standup)
  ├─── CCO — Chief Content Officer (content quality + strategy)
  │      ├── oracle (discovery/arbitrage)
  │      ├── strategist (angles)
  │      ├── writer (flagship)
  │      ├── storyteller (audio dramas)
  │      └── editor (quality gate)
  ├─── CRO — Chief Revenue Officer (monetization + growth)
  │      ├── seobot (SEO/metadata)
  │      ├── publishbot (distribution)
  │      └── analyst (performance → revenue feedback)
  ├─── COO — Chief Operations Officer (pipeline health + production)
  │      ├── researcher (evidence)
  │      ├── scriptwriter (scripts)
  │      ├── voicebot (TTS)
  │      ├── videobot (rendering)
  │      └── thumbnailbot (assets)
  ├─── CAIO — Chief AI & Infrastructure Officer (the meta-system)
  │      └── (SPOC's own meta role: model routing, memory, the machine itself)
  └─── Business units (delegation targets)
         ├── site-agency (web builds: frontend-eng, backend-eng)
         ├── maplespike (maplespike-eng-1/2/3)
         ├── quill (content platform)
         └── trovesandcoves (e-commerce)
```

## Profiles We HAVE vs NEED

### Have (22) — already built
| Profile | Role | Business |
|---------|------|----------|
| oracle | Discovery/arbitrage | Content machine |
| researcher, scriptwriter, voicebot, videobot, thumbnailbot, seobot, publishbot, analyst, storyteller | Production crew | Content machine |
| scout, strategist, writer, distributor, editor | Brand track | Brand |
| site-agency, frontend-eng, backend-eng | Web builds | Site-agency |
| maplespike-eng-1/2/3 | MapleSpike dev | MapleSpike |
| ops | Cluster ops | Infra |
| analyst | General | All |

### NEED (the C-suite layer — the missing executive layer)
| Profile | Owns | Reports to | Status |
|---------|------|-----------|--------|
| **cco** (Chief Content Officer) | Content strategy, brand voice, quality bar, editorial calendar | SPOC | 🔴 build |
| **cro** (Chief Revenue Officer) | Monetization, offers, pricing, sponsorships, revenue feedback | SPOC | 🔴 build |
| **coo** (Chief Operations Officer) | Pipeline health, production flow, KPI dashboards, workflow | SPOC | 🔴 build |
| **caio** (Chief AI & Infrastructure) | Model routing, memory architecture, agent reliability, cost | SPOC | 🔴 build (or SPOC owns it) |

### The C-suite is the key insight
We have the **workers** (22 specialists). We have **SPOC** (the orchestrator).
What we're missing is the **middle management** — the C-suite that owns
departments, sets policy within their domain, and reports up to SPOC. The
research (both sources) is unanimous that this layer is what makes agent
orgs "get stuff done" instead of just producing.

## C-Suite Role Contracts (draft)

### cco — Chief Content Officer
- **owns:** Is the content on-strategy, on-voice, and good?
- **reads:** brain/ (voice, audience, proof), performance data, RULINGS.md
- **returns:** content strategy updates, editorial decisions, quality verdicts
- **routes to:** oracle, strategist, writer, storyteller, editor
- **done when:** the calendar is coherent, the voice is consistent, quality bar holds

### cro — Chief Revenue Officer
- **owns:** Does the content make money?
- **reads:** brain/offers.md, performance data, platform analytics
- **returns:** revenue strategy, offer/pricing decisions, growth experiments
- **routes to:** seobot, publishbot, analyst
- **done when:** every campaign has a revenue answer, conversion is tracked, offers exist

### coo — Chief Operations Officer
- **owns:** Is the machine healthy and flowing?
- **reads:** kanban boards, pipeline logs, model-routing log
- **returns:** ops status, bottleneck fixes, KPI dashboards
- **routes to:** researcher, scriptwriter, voicebot, videobot, thumbnailbot
- **done when:** cards flow, no stuck cards, quota is respected, costs are tracked

### caio — Chief AI & Infrastructure
- **owns:** Is the system itself reliable and improving?
- **reads:** model-routing, pipeline-driver, memory architecture
- **returns:** reliability reports, cost analysis, system improvements
- **routes to:** (the meta layer — may be SPOC's own role initially)
- **done when:** the machine runs unattended, costs are bounded, quality improves

## Business-Unit Profiles (existing, mapped)

| Business | Profiles | Owns |
|----------|----------|------|
| Content machine | oracle + 9 production crew | Faceless content |
| Brand track | scout, strategist, writer, distributor, editor | Personal brand |
| Site-agency | site-agency, frontend-eng, backend-eng | Web builds |
| MapleSpike | maplespike-eng-1/2/3 | Sovereign AI gov data |
| Quill | (part of maplespike/website work) | Content platform |
| Troves & Coves | (site-agency/frontend work) | E-commerce |
| Infra | ops | Cluster |

## The Build Order

1. **coo** first — the machine is already running; ops health is the urgent need
2. **cco** — content strategy/quality once production is healthy
3. **cro** — revenue once there's content to monetize
4. **caio** — the meta-layer (may fold into SPOC)

## The Translation of the Research

The virtual-company research says: **start with Chief of Staff + CCO + a few
workers, add CRO, then scale.** We've inverted that — we built the workers
first (production crew), now we add the C-suite. That's fine; it means the
C-suite has real work to manage.

The one thing the research stresses that we should adopt: **every profile
"owns a number."** The C-suite profiles must each own a KPI (content
performance, revenue, ops health) and report it in the standup.
