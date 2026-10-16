# Music Lane Architecture — genre-generic AI music operation

**Created:** 2026-10-08. **Owner lane:** `music` board. **Account:** Suno Premier.
**Research basis:** `brain/research/music-monetization-2026.md` (platform acceptance,
quota constraints, revenue lanes).

> **Core design rule: the pipeline is GENRE-GENERIC.** Genres are DATA, not code. Adding
> a genre means adding one row to the genre registry — never editing a script. j_kro's
> target set is explicitly open-ended ("infinite variety"), so any hardcoded genre list is
> a defect by construction.

---

## 1. Why a registry, not lanes-per-genre

The failure mode this avoids: five genre folders, five near-identical scripts, five places
to fix a bug. The 2026 platform reality makes this worse — **acceptance differs by genre**
(Beatport bans trance, stock libraries ban everything, YouTube takes everything but
punishes sameness), so genre and lane are two orthogonal axes that must combine
declaratively.

```
genre registry (data)  ×  lane registry (data)  →  generated pipeline graph
```

Add `boss-battle-epic` to the registry → the pipeline knows its prompt template, its
visual style, its target lane set, its cadence. No code change.

---

## 2. Genre registry — `music/genres.yaml`

Each entry is a complete lane definition. This is the SPOC surface for music.

```yaml
# music/genres.yaml — declarative genre registry.
# Add a genre = add a block. Never edit a script to add a genre.

version: 1

defaults:
  export: studio              # Studio = unlimited downloads (see quota gate)
  stems: true                 # stems mandatory for sync + direct-licensing
  lyrics: human-original      # original lyrics -> copyrightable -> SOCAN
  release_private: true       # never auto-publish
  gate_profile: reviewer-deepseek

genres:

  chill-lounge:
    family: ambient
    prompt_template: prompts/chill-lounge.md
    visual_style: visuals/lofi-room-rain.md
    lanes: [youtube-longform, streaming, sync, direct-license]
    cadence: 3/wk
    video_shape: album-30-60min
    notes: "Highest-volume lane. Needs visual identity to survive inauthentic-content review."

  trance:
    family: edm
    prompt_template: prompts/trance.md
    visual_style: visuals/neon-horizon.md
    lanes: [streaming, youtube-mix, direct-license, sync]
    cadence: 2/wk
    video_shape: mix-60min
    notes: "Beatport BANNED (2026-08-12). Independent release + DJ mixes only. No label path."

  jungle-dnb:
    family: edm
    prompt_template: prompts/jungle-dnb.md
    visual_style: visuals/urban-grain.md
    lanes: [streaming, youtube-mix, direct-license]
    cadence: 2/wk
    video_shape: mix-60min
    notes: "Same Beatport ban applies. Amen-break / ragga vocal direction."

  sentimental-piano:
    family: acoustic
    prompt_template: prompts/sentimental-piano.md
    visual_style: visuals/soft-window-light.md
    lanes: [sync, streaming, direct-license, youtube-longform]
    cadence: 3/wk
    video_shape: album-30-60min
    notes: "Sync-friendly: slow, predictable structure, easy to clear. Mood discovery trend."

  commentary-beds:
    family: utility
    prompt_template: prompts/commentary-beds.md
    visual_style: visuals/none.md
    lanes: [direct-license, sync]
    cadence: 5/wk
    video_shape: none
    notes: "Loopable + stemmed. Market: 82% of podcasts license stock themes."

  activist:
    family: vocal
    prompt_template: prompts/activist.md
    visual_style: visuals/documentary-grain.md
    lanes: [direct-fan, sync-documentary, streaming]
    cadence: 1/wk
    video_shape: lyric-video
    notes: "Ad-suitability risk — audience-funded > ad-funded. Sync for doc/film is the pro outlet."

  # ---- elemental / gamer family -------------------------------------------
  # One block per element. Copy the block, change prompt + visual. Infinite variety.

  elemental-fire:
    family: gamer
    prompt_template: prompts/elemental-fire.md
    visual_style: visuals/element-fire.md
    lanes: [game-assets, youtube-gaming, streaming]
    cadence: 2/wk
    video_shape: loop-10min
    notes: "Boss/battle theme. Target indie devs + gaming music channels."

  elemental-water:
    family: gamer
    prompt_template: prompts/elemental-water.md
    visual_style: visuals/element-water.md
    lanes: [game-assets, youtube-gaming, streaming]
    cadence: 2/wk
    video_shape: loop-10min

  elemental-earth:
    family: gamer
    prompt_template: prompts/elemental-earth.md
    visual_style: visuals/element-earth.md
    lanes: [game-assets, youtube-gaming, streaming]
    cadence: 2/wk
    video_shape: loop-10min

  elemental-air:
    family: gamer
    prompt_template: prompts/elemental-air.md
    visual_style: visuals/element-air.md
    lanes: [game-assets, youtube-gaming, streaming]
    cadence: 2/wk
    video_shape: loop-10min

  chiptune-8bit:
    family: gamer
    prompt_template: prompts/chiptune-8bit.md
    visual_style: visuals/pixel-scene.md
    lanes: [game-assets, youtube-gaming, streaming]
    cadence: 2/wk
    video_shape: loop-10min

  epic-orchestral-boss:
    family: gamer
    prompt_template: prompts/epic-orchestral-boss.md
    visual_style: visuals/dark-fantasy.md
    lanes: [game-assets, youtube-gaming, sync, streaming]
    cadence: 1/wk
    video_shape: single-4min
```

**Extensibility contract:** a new genre requires ONLY a `prompts/<name>.md` template and a
registry block. The driver, gates, and dispatch are genre-blind.

---

## 3. Lane registry — `music/lanes.yaml`

```yaml
version: 1

lanes:

  youtube-longform:
    surface: youtube
    shape: album-30-60min
    bot: videobot
    publisher: publishbot
    gate: gate_youtube_authentic     # inauthentic-content policy check
    revenue: ads                      # $1-5 RPM music; 2-3x for 30-60min albums

  youtube-mix:
    surface: youtube
    shape: mix-60min
    bot: videobot
    publisher: publishbot
    gate: gate_youtube_authentic

  youtube-gaming:
    surface: youtube
    shape: loop-10min
    bot: videobot
    publisher: publishbot
    gate: gate_youtube_authentic
    notes: "Gaming-music channels; loopable visual + tracklist."

  streaming:
    surface: distributor
    bot: distributor
    publisher: distributor
    distributor: distrokid             # $24.99/yr, no caps, no exclusions
    alt_distributor: tunecore          # Suno partner-model tracks eligible
    gate: gate_release_ready
    requires: [ai_disclosure, isrc, metadata, master]

  sync:
    surface: songtradr,audiosparx
    bot: distributor
    gate: gate_sync_ready              # stems + metadata + clearance doc
    requires: [stems, metadata, clearance_doc, instrumental_version]

  direct-license:
    surface: own-site
    bot: distributor
    gate: gate_sync_ready
    requires: [stems, license_tiers]

  direct-fan:
    surface: patreon,ko-fi
    bot: socialbot
    gate: gate_human_approval

  game-assets:
    surface: itch.io,unity-asset-store,gamedev-market
    bot: distributor
    gate: gate_sync_ready
    requires: [stems, loop_point, seamless_loop, metadata]
    notes: "Loopable + seamless loop points mandatory. Indie devs buy asset packs."

  stock-ai-native:
    surface: loudly,soundraw,musicapi
    bot: distributor
    gate: gate_release_ready
    notes: "ONLY remaining stock door. Pond5/AudioJungle/Artlist/Epidemic all ban AI."
```

---

## 4. Pipeline stages

Reuses the existing `advance-stage.sh` + pipeline-driver contract. Music board stages:

```
brief → genre-select → lyrics → generate → curate → stems → master → gate → package → visual → publish → track
```

| Stage | Bot | Output | Gate |
|---|---|---|---|
| `brief` | producer | card with genre + lane + intent | registry match exists |
| `genre-select` | producer | resolved registry entry | genre in genres.yaml |
| `lyrics` | writer | original lyrics (human-authored claim) | `gate_lyrics_original` |
| `generate` | producer | 2 tracks via Suno CDP | quota check first |
| `curate` | producer | picked track + reject reason | — |
| `stems` | producer | 12 WAV stems (Suno Studio) | `gate_stems_present` |
| `master` | producer | loudness-normalised master | `gate_loudness` |
| `gate` | reviewer-deepseek | pass/fail + findings | `gate_quality` |
| `package` | producer | manifest + metadata + ISRC | `gate_release_ready` |
| `visual` | videobot | platform-native video(s) | `gate_video_ok` |
| `publish` | publishbot / distributor | private upload / distribution | human approval |
| `track` | analyst | streams, revenue, lane ROI | — |

---

## 5. Gates (executable, never grep)

| Gate | Checks |
|---|---|
| `gate_quota` | Studio export path used; standard-download ledger < 55/60 |
| `gate_lyrics_original` | lyrics file exists, not a Suno-generated lyric; human-authored claim recorded |
| `gate_stems_present` | ≥4 stems, non-zero bytes, durations match master ±0.5s |
| `gate_loudness` | measured via `volumedetect`; −14 LUFS streaming / −16 sync, within ±1 |
| `gate_quality` | independent reviewer on a DIFFERENT model than producer |
| `gate_sync_ready` | stems + metadata + clearance doc + instrumental version all present |
| `gate_release_ready` | ISRC + metadata + AI-disclosure flag + master + artwork |
| `gate_youtube_authentic` | visual varies from prior uploads; not a raw dump; disclosure set |
| `gate_loop_points` | seamless loop verified (game-assets lane) |
| `gate_human_approval` | j_kro gate — never auto-passed |

Every gate is a script that EXERCISES the artifact. A gate that greps a file for a feature
name is a defect — it passes while the artifact is broken.

---

## 6. Quota ledger — `music/quota-ledger.json`

The 60/month standard-download cap is the pipeline's binding constraint. Track it.

```json
{
  "period": "2026-10",
  "standard_downloads_used": 0,
  "standard_downloads_limit": 60,
  "studio_exports": 0,
  "credits_used": 0,
  "credits_limit": 10000,
  "warn_at": 55,
  "hard_stop_at": 58
}
```

`gate_quota` reads this before `generate`/`export`. A 55/60 reading is a warning; 58 is a
hard stop that routes the export through Studio or halts.

---

## 7. Human gates (j_kro's desk — never dispatched to a bot)

1. **Publish approval** — every public release. Unchanged from the existing 90-second gate.
2. **Distributor accounts** — DistroKid/TuneCore signup + annual fee = money decision.
3. **PRO registration** — SOCAN (Canadian) enrolment, needs identity docs.
4. **Sync platform accounts** — Songtradr/AudioSparx signup.
5. **Direct-licensing storefront** — domain + licence tiers + payment processor.
6. **Platform accounts that need login/OAuth** — Fiverr, Patreon, itch.io seller, Unity
   Asset Store publisher.

Per the CoS dispatch boundary: a bot must never be sent to "go get credentials."

---

## 8. Reuse map — what already exists vs what is new

| Need | Already exists | New |
|---|---|---|
| Kanban driver + stages | `scripts/automation/pipeline-driver.sh`, `advance-stage.sh` | `music` board |
| Gate framework | `scripts/gates/*` + `advance-stage.sh` wiring | music gates |
| Lyrics / script | `writer`, `scriptwriter` profiles | lyric templates |
| Video render | `videobot` | album/mix/loop shapes |
| Thumbnails | `thumbnailbot` | genre visual styles |
| Publish | `publishbot` | distributor lane |
| Review | `reviewer-deepseek` (+ longcat/minimax/nemotron panel) | music rubrics |
| GPU jobs | `scripts/audio/gpu-director.sh` | — |
| Human review surface | content.lan + approval API :8791 | music section |
| **Suno generation** | — | **CDP generator (new)** |
| **Genre/lane registries** | — | **new** |
| **Quota ledger** | — | **new** |
| **Stems / master** | `storyteller.py` mix patterns | music mix/master |

---

## 9. Build order

1. **Registries + quota ledger** — data first; everything reads them.
2. **Suno CDP generator** — the one genuinely new component. Generation + Studio export.
3. **Gates** — quota, lyrics, stems, loudness, quality, sync-ready, release-ready, loop.
4. **Board + driver wiring** — `music` board, stages, bot assignment.
5. **Genre templates** — prompt + visual per registry entry.
6. **Lane adapters** — YouTube shapes, distributor packaging, sync deliverables.
7. **First proof** — one track per genre family end-to-end, human-reviewed.

---

## 10. Automatability matrix — what self-run actually requires

Verified 2026-10-08. This decides the self-run design: a lane with an API needs no human
after one-time account setup; a lane without one needs a Playwright adapter.

### 10.1 Full API / CLI — zero human after setup

| Surface | Mechanism | Notes |
|---|---|---|
| **itch.io** | **`butler` CLI** (`butler push`) — official, plus a GitHub Action | Game assets, loops, SFX packs. Also supports non-game projects |
| **Gumroad** | **Official API** — `POST /v2/products`, `POST /files/presign`, files upload | Digital downloads: sample packs, stem packs, albums, SFX. Community Playwright pipelines exist as reference (gumroad-autopilot, gumroad-automation-pipeline) |
| **Songtradr** | **Official API 3.0.0** + official Python client (`songtradr-api-client-python`, PyPI). Auth: `POST /api/v1/user/login` | Sync submission + deep metadata + auto-tagging |
| **Roblox** | `publish.roblox.com/docs/json/v1` → `UploadAudioRequest` | Game audio |
| **RouteNote** | Free distribution (keep 85%) | Excludes Content ID/Meta/Korean stores |

### 10.2 No API — Playwright adapter required

| Surface | Status | Mechanism |
|---|---|---|
| **DistroKid** | No official API. **Two community automations exist**: `Sam-r-ai/Automated_Distrokid_Uploader` (webupload.py) and `hlushchukm/Distrokid` (unofficial Go wrapper, iOS app reversal) | Playwright browser automation on the logged-in session |
| **Fab / Unreal publisher portal** | Publisher onboarding + 15-business-day review. No public API | Playwright after one-time publisher account |
| **Unity Asset Store** | Publisher portal, moderation. No public API | Playwright after one-time publisher account |
| **Splice / Loopmasters / ProducerLoops** | Curated submission | Email/form submission — semi-automated |

### 10.3 Closed — do not build

Pond5, AudioJungle/Envato, Artlist, Epidemic Sound, Soundstripe, PremiumBeat, Musicbed,
Bandcamp, Beatport, CD Baby.

### 10.4 Standing permission

j_kro (2026-10-08): "we can use api watchers to scrape or playwright and stuff like that if
necessary too." Playwright + API watchers + scraping are **authorized** as the mechanism of
record for any lane lacking an API. The automation breaks the glass — j_kro does not.

---

## 11. Self-run design — the autonomous loop

Target: **an individual's self-running music business.** Human involvement after setup is
limited to the approval gate (configurable) and money decisions.

```
┌─ MUSIC ORACLE (daily) ────────────────────────────────────────────────┐
│  Scans: lane performance, genre ROI, platform policy changes,          │
│  trend signals. Emits scored cards to the `music` board.               │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌─ PIPELINE DRIVER (every 30 min, ALWAYS-ON HOST) ──────────────────────┐
│  Walks the music board, dispatches the owning bot per stage,           │
│  enforces gates, advances or rejects. Cap 1 concurrent.                │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
   brief → genre-select → lyrics → generate → curate → stems → master
        → gate → package → visual → publish → track
                              ↓
┌─ PUBLISH LAYER (API-first, Playwright fallback) ──────────────────────┐
│  itch.io (butler) │ Gumroad (API) │ Songtradr (API) │ DistroKid (PW)   │
│  Uploads go PRIVATE/draft by default; a policy flag decides public.    │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌─ ANALYST (weekly) ────────────────────────────────────────────────────┐
│  Revenue per genre × lane × hour. Feeds cadence weights back to the    │
│  registry (earning genres get more cadence; losers pause).             │
└───────────────────────────────────────────────────────────────────────┘
```

### 11.1 The three always-on rules

1. **The scheduler runs on an ALWAYS-ON host (nexus), not zephyr.** Workstation crons pause
   when the workstation sleeps. A self-running business cannot sleep with the laptop.
2. **Event where an event exists; timer for time, drift, and absence.** Platform policy
   changes and quota resets are time-based (legitimate timers). New-artifact detection is an
   event (fire on the write site, not a poll).
3. **Every open item is owned in code.** The backlog register is the carry-forward; a
   completed item moves to the changelog or it is not done.

### 11.2 The autonomy ladder — earn it per lane

Lanes start at **advisory** (produces, waits for approval) and graduate:

| Rung | Behaviour | Promotion evidence |
|---|---|---|
| advisory | produces, human approves each publish | — |
| supervised | publishes to private/draft, human flips public | 10 clean advisory publishes |
| monitored | publishes public, human audits weekly | 20 clean supervised, zero platform strikes |
| full | publishes public, human audits monthly | 50 clean monitored, revenue positive |

Promotion is proposed on the board with evidence; j_kro approves the rung change. This is how
the system earns the right to self-run rather than being handed it.

### 11.3 Quota-aware pacing

The 60/month standard-download cap (Studio = unlimited) plus the YouTube "one quality video
per day per channel" guard plus the anti-spam rules bound the loop. `gate_quota` is checked
before every generation. The driver never outruns the quota.

### 11.4 Failure handling — self-healing, not self-stopping

- Platform 429/5xx → cooldown, retry with backoff, log to the rate-limit watcher.
- Gate failure → returns to the maker with the specific finding; never advances.
- Credential expiry → surfaces in the daily digest as a human-gated item (never a bot
  hunting for credentials).
- Sustained failure → the lane pauses itself and pages the digest. It does not loop.

---

## 12. The glass-break — one-time human actions

Everything after this list is autonomous. These are the irreducible human actions: they
require identity, money, or a legal agreement.

| # | Action | Why human-only | Cost |
|---|---|---|---|
| 1 | **DistroKid account** | annual fee + legal agreement | $24.99/yr |
| 2 | **Gumroad account + API token** | identity + payout setup | free |
| 3 | **itch.io account + butler API key** | identity | free |
| 4 | **Songtradr account** | identity + sync agreement | free tier |
| 5 | **SOCAN registration** | legal identity, Canadian PRO | free/join fee |
| 6 | **Payout/tax details** on each | tax law | — |
| 7 | **Approve the publish policy** — the autonomy rung for each lane | creative-direction call | — |

After 1–6 exist and 7 is set, the loop runs. The system generates, gates, packages,
uploads, and reports. j_kro reviews a weekly digest and audits on the cadence the rung
allows.

**Deliverable for the glass-break:** a single checklist with the exact URL, the exact
fields needed, and the credential location to store each value. One sitting, done.

---

## 13. Additional lane: asset packs (the "assets" market)

j_kro: "any sort of 'assets' pack type market things too."

An asset pack is a *derived product*: it monetizes work already done for the sync lane.

| Product type | Surface | Automation |
|---|---|---|
| Loop packs (elemental, chiptune, jungle breaks) | itch.io (butler), Gumroad (API) | ✅ full |
| Stem packs | Gumroad, itch.io | ✅ full |
| One-shots / SFX | Gumroad, itch.io | ✅ full |
| Sample packs | Gumroad, itch.io, (Splice/Loopmasters = curated) | ✅ full for own store |
| Game music asset packs | itch.io (AI Audio tag), Unity/Fab (Playwright) | ✅ itch.io full |
| Album / track bundles | Gumroad, Bandcamp(✗ banned) | ✅ Gumroad |

**Packaging requirements** (from the research): loops must be seamless + click-free with
stated BPM/key; stems time-aligned; clean WAV with stated sample rate; consistent file
naming; multi-tier licences with explicit permitted use, distribution, and derivative-work
rules. Vague licence language is the #1 failure mode.

**Verified market rates:** production libraries $50–500/track; perpetual licences
$1,000–10,000; asset packs $2,500–7,500 for 5–10 tracks; indie game sync $500–15,000/track.

The asset lane is the **highest-automation, lowest-gatekeeper** revenue path — which makes it
the natural first lane to run at full autonomy.
