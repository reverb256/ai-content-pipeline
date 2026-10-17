# Proof

> Evidence, credentials, and receipts. What makes our claims credible. Every
> consequential claim in a campaign traces to a source listed here or in the
> campaign's evidence package.

## What We Have Built (live proof)

- **Omarchy cluster migration** — zephyr + nexus migrated off NixOS to
  Omarchy 4.0.0 (2026-08). Remaining hosts (forge, sentry) pending. Documented
  in `~/Projects/Reverb-OS`, omnigate, and the ops log.
- **omnigate** — a Windows/macOS/Linux → Omarchy migration tool. Union-mount
  lower layers, differential reflink sync, manifest-as-git-artifact. Repo:
  `reverb256/omnigate`.
- **Hermes agent fleet** — 7+ profiles (SPOC, software-factory, site-agency,
  nexus-core, sentry-core, researcher, analyst), kanban-driven dispatch,
  gateway orchestration, memlawb encrypted memory.
- **memlawb** — self-hosted, zero-knowledge encrypted persistent memory server
  with a Hermes MemoryProvider plugin. Client-side AES-256-GCM; server sees
  only ciphertext.
- **Mining fleet** — peakminer on zephyr (3060 Ti + 3090), nexus (3060 Ti),
  forge (2x 4060). ~261 TH/s fleet-wide (2026-08), 4 of 5 GPUs.
- **Garage S3** — self-hosted S3-compatible object storage on nexus, 391 GB
  backups bucket, 718k objects intact through a host wipe.
- **The AI content pipeline itself** — this repo. The system is its own proof.

## Numbers We Can Quote

- Fleet hashrate: ~261 TH/s (2026-08), 4 of 5 GPUs, verified via plugin
- nexus migration: 0 failed units (vs sentry's 8, forge's 2 on NixOS)
- memlawb: 77 sops secrets decrypt via YubiKey only, 5 recipients, verified
- Garage: 391.3 GB / 718,529 objects backups intact after emergency wipe
- Hermes real-profile browsing: verified signed-in as reverb256 across 6
  platforms via CDP (2026-08-29)

## Credentials

- GitHub: reverb256 (35+ public/private repos)
- Omarchy: zephyr + nexus on 4.0.0, 66 plugins harmonized
- Domains: reverb256.ca, reverb256.dev (portfolio/brand surface)

## Authority Boundaries (what we do NOT claim)

- We do not claim to be a media company with employees
- We do not claim revenue from content (none yet)
- We do not claim to be NixOS experts — we migrated OFF it, which is its own
  authority
- We do not claim Omarchy is perfect — we document what broke

## How Proof Is Used

- **Researcher**: verifies claims against sources; builds the evidence package
- **Strategist**: picks the angle that real proof supports
- **Writer**: cites proof at the moments a reader could doubt
- **Editor**: checks every consequential claim against the evidence package
- **Distributor**: picks the proof point that fits the platform

If a campaign needs proof we do not have, the researcher says so. It does not
invent it.
