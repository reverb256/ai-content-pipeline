# Research — Omarchy migration: the personal autonomous corporation

> Evidence package. Verified claims with URLs, contradictions, unknowns, and
> mechanisms worth explaining. Every consequential claim in the flagship must
> trace to a claim here.

## Verified Claims

1. **Omarchy 4.0 (Quattro) is the biggest overhaul since the project's start.**
   Released 2026-08-14. Rebuilds the desktop environment around a single
   Quickshell/QtQuick process (bar, launcher, menus, notifications, OSD, lock
   screen, polkit). Source: https://www.heise.de/en/news/Omarchy-Linux-Desktop-Overhaul-and-10-Million-for-Foundation-11432304.html ;
   https://github.com/basecamp/omarchy/releases/tag/v4.0.0

2. **Omarchy 4.0 integrates AI coding agents as first-class citizens.** The
   system ships a default-agent picker (Claude Code, Codex, OpenCode, Gemini,
   Grok, Copilot, Crush, Pi), lazy-installed on first use, launched via
   keyboard shortcut (`SUPER+SHIFT+CTRL+A`). Source:
   https://github.com/basecamp/omarchy/releases/tag/v4.0.0 ;
   https://blog.desdelinux.net/en/omarchy-4.0-release-new-features-quickshell-omakase/

3. **Omarchy 4.0 is now distributed as native Arch packages, not a Git
   checkout.** Updates flow through pacman; user modifications are isolated.
   Source: https://blog.desdelinux.net/en/omarchy-4.0-release-new-features-quickshell-omakase/

4. **The Omacom Foundation secured multi-million-dollar backing.** Founded by
   DHH 2026-08-19; the Core Team shares responsibility for direction.
   37signals is migrating Ops/Ruby teams to Omarchy (announced 2025-08,
   completion ~2028). Source: https://www.heise.de/en/news/Omarchy-Linux-Desktop-Overhaul-and-10-Million-for-Foundation-11432304.html

5. **memlawb is open-source, self-hostable, zero-knowledge encrypted memory
   for AI agents.** AES-256-GCM, key derived from passphrase via scrypt; the
   server stores only ciphertext. Delta sync, MCP server included. Source:
   https://github.com/Gitlawb/memlawb

6. **reverb256 maintains 35 public repos on GitHub (verified 2026-08-29).**
   Including Reverb-OS (the Omarchy migration home), omnigate (the migration
   tool), memlawb-for-hermes (the Hermes memory integration). Source:
   https://github.com/reverb256

## Internal Verified Facts (from memlawb / live cluster state — the private proof)

7. **zephyr + nexus migrated to Omarchy 4.0.0 with 0 failed units on nexus**
   (vs sentry's 8 and forge's 2 on NixOS). Verified live 2026-08-26.
   Source: memlawb `infra/nexus-is-omarchy-now`, `omarchy-fleet-migration-direction-2026-08-24`

8. **77 sops secrets decrypt via YubiKey only, 5 recipients, all verified.**
   Source: memlawb `secrets-rekey-5-recipients-complete-2026-08-24`

9. **Garage S3 backups intact through emergency wipe: 391.3 GB / 718,529
   objects.** Source: memlawb `nexus-emergency-wipe-postincident-2026-08-24`

10. **Hermes agent fleet: 7+ profiles, kanban-driven dispatch, memlawb memory,
    headless CDP browser with real reverb256 sessions (verified 2026-08-29).**
    Source: this repo (ai-content-pipeline) + memlawb
    `hermes-real-profile-browsing-cdp-fix-2026-08-29`

## Public Story Facts (from X posts, verified via x_search 2026-08-29)

11. **September 2025: reverb256 "somewhat accidentally" killed Windows on the
    main PC while moving to Omarchy.** Source: x.com/reverb256/status/2093318293444608065
    (2026 retrospective).

12. **The distro-hopping arc: Omarchy → CachyOS (Omarchy over Arch base with
    CachyOS repos/kernels) → Fedora → Bazzite → NixOS (March 2026) → back to
    Omarchy (August 2026).** Source: x.com/reverb256/status/2093318293444608065

13. **NixOS was used as "AI-accelerated deep-end-first Linux learning" — the
    big win was giving agents full system context as he "experimented and
    broke everything." Went through "enough fucking builds."**
    Source: x.com/reverb256/status/2093318293444608065,
    x.com/reverb256/status/2091545952020512800

14. **After the NixOS phase, Home-Manager is "probably the right amount of
    Nix" on top of Omarchy, with potential to integrate Nix strengths into
    Omarchy's AI agent subsystem.** Source: x.com/reverb256/status/2091545952020512800

15. **Gaming works: "Beat saber, zenless zone zero and genshin, and soon
    vrchat working like a charm over here on my trusty 3090" (Aug 2025).**
    Source: x.com/i/status/1961388912141652294

16. **VRChat is a regular part of the voice and the FBT setup** (camera-based
    FBT pipeline per the repo skills; the account posts about VRChat
    community and "nobody cares what you look like IRL in vrchat").
    Source: x.com/reverb256/status/1975007466883809302,
    x.com/reverb256/status/1980271449362317405

17. **reverb256.ca profile: "15 years in food service. 20 years tech-curious.
    Now building production applications with NixOS infrastructure and
    AI-assisted development." 14 projects shipped, 4-host NixOS cluster,
    Rust→TypeScript→Python, open to junior roles/internships.**
    Source: https://reverb256.ca (extracted 2026-08-29)

## Contradictions

- **Omarchy's install speed claim varies.** Official FAQ says "10-15 minutes
  after installing Arch"; techaeris review measured "booted into desktop in 3
  minutes" on a Dell XPS 16. Both describe different stages (installer vs
  boot-to-desktop). Use the conservative official figure; note the review's
  faster measurement as an independent data point.
- **"Omarchy is not a standalone distribution" (official FAQ) vs press calling
  it "an Arch-based Linux distribution."** Both are true: it is a setup layer
  on Arch, and the packaged 4.0 ISOs are distributable. Frame as "Arch-based
  with an opinionated setup layer" to satisfy both.

## Unknowns / What Sources Do NOT Prove

- No public source documents a NixOS→Omarchy migration. This is genuinely
  novel — our content is the first (that we can find).
- No public source documents a "personal autonomous corporation" running on
  Omarchy with a Hermes agent fleet. Also novel.
- The long-term stability of Omarchy 4.0 (released 2 weeks ago, 4.0.1 already
  out) is unproven. We can only say "our experience so far."
- 37signals migration timing (through 2028) is a public claim, not our data.

## Mechanisms Worth Explaining

1. **The "defer to Omarchy" governing rule** — if Omarchy has a supported way
   to configure/install/manage something, defer to it; layer only what it
   lacks on top (Home Manager additive layer). This is the migration's
   architecture principle.
2. **Zero-knowledge memory architecture** — encryption happens client-side
   (AES-256-GCM, scrypt-derived key), the server is crypto-blind. Why this
   matters for an agent fleet that holds private facts.
3. **The CDP real-profile browsing mechanism** — how a headless Chromium with
   the real profile + real keyring lets bots act as the user without DOM
   scraping (and why the snapshot path fails without the keyring).
4. **The loop that makes a one-person media company possible** — idea →
   research → angle → long-form → distribution → review → performance →
   updated playbooks. Why the loop, not the drafts, is the valuable part.
