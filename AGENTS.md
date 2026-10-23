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

---

## Git hygiene rules for every agent on this fleet

Status: shared rule block. Paste into a repo's `AGENTS.md`, `CLAUDE.md`, or a
profile's `SOUL.md`. Owner: Reverb. Added 2026-10-23 by fleet-leakguard.

This block starts at H2 on purpose: pasting an H1 into a document that already
has a title trips markdownlint MD025 (`single-h1`). Every fenced block here is
fenced rather than indented so MD046 (`code-block-style`) stays clean in the
host repo.

These rules are mandatory for all Hermes profiles, bots, and delegated agents.
They exist because an agent ran `git add -A` in `reverb256.github.io` and
committed `.freebuff/` session databases that held live Cloudflare OAuth tokens
plus the operator's real name and city into a public repo (commit `051a6be`).

### Stage explicit paths. Never stage a tree.

- Use `git add <path> [<path> ...]` with the paths you actually changed.
- Never run `git add -A`, `git add .`, `git add --all`, or `git commit -a`.
- Never use `git stash --include-untracked` as a shortcut before staging.

### Never commit tool or session state

Forbidden in any commit, at any depth:

```text
.freebuff/  .sisyphus/  .serena/  .playwright-mcp/  .codebuff/
.cursor/    .claude/    .aider*   .hermes/          .opencode/
.continue/  playwright-report/    .wrangler/        .dev.vars
*.db  *.db-wal  *.db-shm  *.sqlite*  .env*  *.pem  *.key
```

A global exclude file blocks most of these, but the exclude list is a net, not
permission. If a path is not part of the change, do not stage it.

### Do not bypass the gates

- Never pass `--no-verify` to `git commit` or `git push`.
- Never set `core.hooksPath` to an empty directory inside a repo.
- Never delete or edit `~/.config/git/ignore` or anything in `~/.config/git/hooks/`.
- Never unset `core.excludesFile`.
- A blocked commit is a finding: report it to the operator. Do not retry with a
  different flag, do not rewrite the finding, do not edit the pattern list.

If a hook blocks work that is genuinely correct, stop and report it. The
operator decides.

### Identity

- Commit as `Reverb <129622142+reverb256@users.noreply.github.com>`.
- Never commit with a real-name or ISP-provided address.
- Never put the operator's real name, city, ISP mailbox, or the `10.1.1.x`
  LAN plan into a tracked file.

### Before you push

```bash
git status --short          # read every line
git diff --cached --stat    # confirm the staged set
git log --oneline -3        # confirm the author identity
```

Install check on a host: `bash ~/.config/git/leakguard/doctor.sh` (17 checks).
