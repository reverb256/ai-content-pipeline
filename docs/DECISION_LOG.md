# Decision Log

> Architectural decisions and rationale. Every non-trivial choice is recorded
> here so future sessions don't re-litigate settled questions.

## 2026-08-29 — Start the AI Content Pipeline

**Decision:** Build a full one-person media company system in
`~/Projects/ai-content-pipeline/`, GitHub-backed as `reverb256/ai-content-pipeline`.

**Rationale:** j_kro wants a content operation across X, YouTube, Substack,
LinkedIn, and a personal/ops blog. The system must be as automated as possible
while keeping human approval at the editorial boundary. Hermes provides the
infrastructure (profiles, kanban, bot mode, gateway, memory); this repo is the
content brain + operating system on top.

**Model:** The guide's six-role media company (signal scout → researcher →
strategist → writer → distributor → editor) mapped onto Hermes profiles, with
kanban as the durable production desk and bot mode as the visible coordination
layer.

## 2026-08-29 — One profile per bot, not one monolithic profile

**Decision:** Each of the six roles is a separate Hermes profile
(`scout`, `researcher`, `strategist`, `writer`, `distributor`, `editor`), not
stages inside one profile.

**Rationale:** Hermes profiles give isolated memory, sessions, and skills per
role (the guide's core requirement: "prevent one bot's memory from becoming
everyone else's memory"). Kanban provides the durable handoff records; bot
mode provides the visible roster. A single profile would collapse the
separation that makes the system work.

## 2026-08-29 — Platform interaction via CDP browser + captured APIs

**Decision:** The content system interacts with X/Substack/YouTube/LinkedIn
through a headless CDP Chromium running the real reverb256 profile, using
captured internal API endpoints for direct calls.

**Rationale:** Token-efficient, fast, structured (no DOM parsing), and
authenticated as the real account. The CDP path sidesteps the snapshot
mock-keychain limitation (verified 2026-08-29). Direct API calls need the
full header set; the browser provides it.

## 2026-08-29 — All automation on zephyr (exception to prior rule)

**Decision:** The content system's bots and browser run on zephyr (Omarchy),
the authoring host.

**Rationale:** The prior "no autonomous profiles on zephyr" rule was NixOS-era
(31GB RAM constraint, sentry/nexus as pipeline hosts). zephyr is now Omarchy,
it is the authoring host, and the browser + keyring + real sessions live here.
This is a conscious, documented exception.

## 2026-08-29 — RULINGS.md as the corrections memory

**Decision:** Every human correction becomes a permanent ruling in
`brain/RULINGS.md`, read by every bot before each run.

**Rationale:** The strongest pattern from X research (2026-08-29): corrections
written once become permanent institutional knowledge. Taste compounds without
the human repeating themselves.
