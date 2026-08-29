# AI Content Pipeline

A one-person media company powered by a team of Hermes bots. Research, writing,
editing, and distribution capacity of a full content operation — driven by a
shared content brain, a visible bot roster, and a durable kanban production desk.

## The Loop

```
idea → research → angle → long-form → distribution → review → performance → updated playbooks
```

The valuable part is not the number of drafts produced. It is the loop
connecting attention, research, editorial judgment, distribution, and feedback.
Break any connection and quality drops.

## Architecture

| Layer | What it is | Where |
|-------|-----------|-------|
| **Brain** | The shared editorial knowledge — voice, audience, proof, offers, RULINGS.md, playbooks | `brain/` |
| **Bots** | Six Hermes profiles, each owning one decision and returning one artifact | `profiles/` |
| **Kanban** | The production desk — durable task state, handoffs, review, human approval | `hermes kanban` board `media` |
| **Platforms** | Per-platform playbooks + captured API catalogs | `platforms/` |
| **Browser** | Headless CDP Chromium with real sessions (X, Substack, YouTube, LinkedIn) | `scripts/browser/` |
| **Campaigns** | One folder per campaign — the handoff record travels with the work | `campaigns/` |
| **Performance** | Numbers + weekly review outcomes | `performance/` |

## The Bots

| Bot | Decision it owns | Artifact it returns |
|-----|-----------------|---------------------|
| **scout** | Is this worth pursuing NOW? | Signal candidate(s) |
| **researcher** | Is this claim true and supported? | Evidence package |
| **strategist** | What is the story here? | Angle brief |
| **writer** | What is the flagship piece? | Long-form draft |
| **distributor** | What does each platform need? | Platform assets |
| **editor** | Is this ready for the human? | Approved / revision request |

Every bot reads `brain/RULINGS.md` before starting work. Every correction you
make becomes permanent institutional knowledge.

## Quick Start

```bash
# 1. Start the headless browser (real sessions)
systemctl --user start media-browser.service

# 2. Create a campaign
hermes kanban boards switch media
hermes kanban create "campaign: <idea>"

# 3. Watch it flow through the pipeline
hermes kanban boards list

# 4. Approve at the gates (you are the editor-in-chief)
```

## Human Approval Gates

You approve:

- the central angle (before the writer spends hours)
- the flagship draft
- every factual claim carrying real consequence
- every public post
- changes to voice, audience, offer, or editorial policy
- performance lessons that become permanent playbook rules

Autonomy removes repeated decisions. It never removes your taste.

## License

MIT (see LICENSE)
