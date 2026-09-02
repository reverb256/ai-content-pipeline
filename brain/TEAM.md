# TEAM.md — Living Roster (2026-09-02)

> Written by the CoS. Read before routing. Every bot has ONE lane, a fence,
> and an autonomy level. If a bot's lane is not here, it is not trusted to
> act beyond L1.

## The org shape

```
j_kro (board — strategy, approvals, the only human)
 └── SPOC/CoS (orchestrator — routes, sequences, surfaces decisions)
      ├── C-suite: caio (AI/infra), cco (content), coo (pipeline health), cro (revenue)
      ├── Production crew: oracle, researcher, scriptwriter, voicebot, videobot,
      │     thumbnailbot, seobot, publishbot, analyst, storyteller
      ├── Brand track: scout, strategist, writer, distributor, editor
      └── Business units: site-agency, maplespike-eng, ops, web-designer
```

## Autonomy ladder (default policy — every SOUL carries the level)

| Level | Meaning | Default for |
|---|---|---|
| L0 | Observe / log only | New bot's first 48h |
| L1 | Draft only | All external comms, all publishing |
| L2 | Act inside fence | Archive, tag research, move kanban, write vault notes |
| L3 | Act + notify | Recurring internal ops approved once |
| L4 | Autopilot | NEVER — until a playbook has a written kill switch |

Start every bot at L1. Promote one action class at a time after 10 correct
runs. Demote on first silent failure. **Fence: nothing leaves the building
(send/post/publish/pay/delete) without human approval.**

## Current roster (from profile audit 2026-09-02)

| Bot | Lane | Autonomy | Fence |
|---|---|---|---|
| analyst | analyze/learn: pull real numbers, keep/test/stop | L2 | no playbook changes without approval |
| caio | AI/infra meta: routing, memory, cost | L2 | no routing changes without SPOC approval |
| cco | content strategy/voice/quality | L2 | no voice changes without approval |
| coo | pipeline health/ops | L2 | no config changes without approval |
| cro | revenue/offers/CTA | L2 | no offer changes without approval |
| oracle | opportunity arb (gate not factory) | L2 | cards only, no production |
| researcher | evidence packages (3-7 verified claims) | L2 | never fabricate |
| scriptwriter | retention-optimized scripts per stage-spec | L2 | word-budget gate |
| storyteller | audio-drama synthesis (VoxCPM) | L2 | pacing gate |
| voicebot | narration audio | L2 | duration gate |
| videobot | visuals/final video | L2 | truncation gate |
| thumbnailbot | thumbnail variants | L2 | 3-word text rule |
| seobot | title/desc/tags/chapters | L2 | SEO gate |
| publishbot | upload PRIVATE only | **L1** | NEVER public without j_kro |
| scout | signal discovery | L2 | never write posts |
| strategist | angle briefs | L2 | human approves angle |
| writer | flagship drafts (brand) | L1 | human approves publish |
| distributor | platform assets | L1 | drafts only |
| editor | review/critique gate | L2 | can KILL handoff, never fixes |
| site-agency | lead gen + sites | L2 | consent gates |
| maplespike-eng | maplespike build | L2 | issue-driven |
| ops | homelab/cluster ops | L2 | never miners revenue-critical |
| web-designer | content.lan / web | L2 | — |

## Rules
1. Maker-checker: the bot that did the work does NOT grade it. Gate/editor
   (a different profile) reviews. Evidence sidecar required on handoff.
2. Never steal a lane. Out-of-lane request → back to CoS.
3. Missing data is UNKNOWN, never invented.
4. Fences are hard: send/post/publish/pay/delete = human. No exceptions.
