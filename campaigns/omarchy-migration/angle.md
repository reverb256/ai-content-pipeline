# Angle — Omarchy migration: the personal autonomous corporation

> One complete angle brief. Returned by the strategist, awaiting HUMAN
> APPROVAL before the writer spends hours.

```
reader: the technical operator running 4+ machines (homelab or small infra)
        who is tired of NixOS rebuilds and curious about Omarchy — or
        curious about what "an autonomous personal company" actually looks like
reader outcome: a decision framework for whether to migrate (and how), plus a
        concrete picture of what a personal autonomous corporation running on
        Omarchy + Hermes + memlawb + kanban looks like — the reader can decide
        "I should/ shouldn't do this" and "here's the order of operations"
current source: zephyr + nexus migrated to Omarchy 4.0.0 (2026-08), 0 failed
        units on nexus, the migration direction locked, the tooling public
        (Reverb-OS, omnigate, memlawb)
central tension: declarative purity (NixOS) vs. working systems (Omarchy).
        Most people believe you must choose: reproducible and complex, or
        simple and fragile. The migration claims you can get the benefits of
        both — if you apply the right governing rule and layer the right
        tooling.
thesis: migrating off NixOS to Omarchy is not a downgrade — it is the release
        from a config treadmill. The personal autonomous corporation becomes
        possible when the OS defers to a curated base, the user layer is
        additive (Home Manager), and the agent fleet (Hermes) carries the
        orchestration. The migration is the enabler, not the point; the point
        is what you can run on the other side.
what becomes possible: a 1-person autonomous company — Hermes profiles doing
        research/writing/editing/distribution, encrypted memory (memlawb),
        kanban production desk, CDP browser acting as the operator — all on a
        stable, package-managed, snapshot-able base.
flagship format: a deep guide/essay (blog) — "How I migrated my NixOS cluster
        to Omarchy and built a personal autonomous corporation on top" — with
        the migration decision framework as the reusable object. Secondary:
        X thread with the migration numbers + the "defer to Omarchy" rule.
reusable object: the migration decision framework — the "defer-to-Omarchy
        rule", the per-host checklist (what to check: failed units, services
        carried over, secrets, data), and the 3-layer architecture (base
        Omarchy / additive HM / agent fleet). Plus the "personal autonomous
        corporation" blueprint (profiles, memory, kanban, CDP browser).
proof required: the verified claims in research.md (Omarchy 4.0 facts,
        memlawb zero-knowledge, 0 failed units, YubiKey secrets, garage
        backups, Hermes fleet). All present.
sections:
  1. The problem: NixOS config treadmill (the honest frustration)
  2. The decision: why Omarchy (what it actually is, 4.0 facts)
  3. The migration: 4 hosts, what broke, what survived (numbers)
  4. The governing rule: defer to Omarchy, add only what it lacks
  5. The autonomous layer: Hermes fleet + memlawb + kanban + CDP browser
  6. What I'd do differently (v2)
  7. The decision framework (the reusable object — checklist form)
distribution entryways:
  - proof: "4 hosts, 1 weekend, 0 failed units — the migration numbers"
  - mechanism: "the defer-to-Omarchy rule explained in one post"
  - workflow: "the per-host migration checklist (copy this)"
  - risk: "what I lost when I wiped nexus — and what survived"
  - result: "what a 1-person autonomous company looks like on Omarchy"
```

## Rejected Directions (why they are weaker)

1. **"Omarchy 4.0 is great, here's the review"** — no differentiation; 50
   review pieces exist. We are not a review site.
2. **"NixOS is bad, switch to Omarchy"** — a hot take without the working
   system. The audience hates hype; this reads as attack content.
3. **"The autonomous corporation" without the migration** — interesting but
   ungrounded. The migration is the proof that makes the autonomous layer
   credible.
4. **A pure how-to migration guide** — useful but boring; the reusable object
   is stronger when it includes the autonomous-company payoff.

## Recommendation

Proceed with the flagship as a deep guide/essay. The angle has a real tension
(declarative purity vs. working systems), a defensible thesis, a reusable
object (decision framework + blueprint), and 7 verified proof claims. It is
the strongest entryway to the "personal autonomous corporation" story — the
migration is the hook, the corporation is the payoff.
