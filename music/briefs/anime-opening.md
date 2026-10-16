# Brief — anime-opening

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_96821eed (`music-oracle: anime-opening (score 7.55)`)
> **Duplicate card:** t_abaa7e2d (`music-oracle: anime-opening (score 7.75)`) — same genre,
> same lanes, emitted ten minutes later by the same unguarded oracle run.
> Both resolve to THIS brief; the brief is keyed by genre, not by card.
> Root cause fixed with this card — see §7.
> **Written:** 2026-10-16T13:00-05:00 (CDT), profile `music-producer`, run 7
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `1553da2` (main)
> **Oracle score:** 7.55/10 (quota headroom 10.0, lane coverage 8.0, revenue 10.0,
> cadence fit 1.7, policy risk 9.0, trend signal 3.0). Threshold 5.0 → produce.
> **Consumed:** the Virtual Reflections album, tracks 7–8 (registry note).

Every number and quoted string below comes from a command or a file read during
this stage. Nothing is recalled. Commands and their real output are shown.

---

## 1. Genre resolution (live, not transcribed)

```
$ /usr/bin/python3 music/registry.py validate
registry OK: 14 genres, 10 lanes
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

`/usr/bin/python3` is the interpreter the systemd units invoke, and it has
PyYAML. The shell's bare `python3` is the Hermes bundled interpreter and does
not — `python3 music/registry.py validate` fails with
`ModuleNotFoundError: No module named 'yaml'`. Use the absolute path.

| Field | Value |
|---|---|
| Genre | `anime-opening` |
| Family | `anisong` |
| Prompt template | `music/prompts/anime-opening.md` — resolves; style block measures 754 chars (`awk` between the first ```` ```text ```` fences, newlines stripped) |
| Visual style | `music/visuals/anime-opening.md` — resolves |
| Lanes | `streaming`, `sync`, `direct-license`, `youtube-gaming` |
| Cadence | 1/wk |
| Video shape | `single-4min` |
| Lyric blueprint | `music/lyrics/blueprints/anime-opening.yaml` — **ABSENT** (only `activist`, `chill-lounge`, `trance` exist) |
| Registry note | "Anison idiom: 130-180 BPM, IV-V-iii-vi royal road, FINAL CHORUS JUMPS UP ONE KEY (the defining gesture), 90-second TV-edit density, Japanese vocals in Japanese script. Required by the Virtual Reflections album (tracks 7-8). A generation without the key-changed final chorus is OUT of genre - reject it." |

Registry `defaults:` that bind this track (`music/genres.yaml` lines 19–25):
export `studio`, stems `true`, lyrics `human-original`, release_private `true`,
gate_profile `reviewer-deepseek`.

---

## 2. Intent

An anime opening in the idiom's own grammar: a 90-second-density showpiece that
survives being cut to a TV edit, front-loads its hook, and pays off with a final
chorus that jumps up a key. It is not a rock song with anime stickers, and it is
not a loop — the registry's `single-4min` shape and the template's "this is a
SHOWPIECE ... not a loop" fix that.

The registry names the consumer: **Virtual Reflections, tracks 7–8** ("Opening
Theme", "Becoming") — "the explosive end of the intimate→explosive arc".

### Craft contract (from `music/prompts/anime-opening.md` — the write-to spec)

| Constraint | Value |
|---|---|
| Tempo | 130–180 BPM; J-rock pocket 160–170 (template style field uses 160) |
| Harmony | IV–V–iii–vi "royal road" (王道進行) **under the chorus** |
| Form | Hook inside 15 s; no wasted bars; must survive a 90-second cut |
| Layers | Busy double-kick drums, melodic eighth-note bass, piano **and** strings over rhythm guitars, synth pads beneath, brass stabs on the chorus |
| Vocals | Japanese, in **Japanese script** (kana/kanji) — Suno mangles romaji |
| Bridge | Half-time, piano + strings + voice only. "This silence is load-bearing" |
| Final chorus | **Jumps up one key.** "The single most important line in this template" |
| Ending | Hard unison hit, cut like a TV edit to black. **A fade-out is a defect** |
| Weirdness / Style Influence | 35% / 85% |
| Exclude styles | `acoustic folk, lo-fi, trap beats, EDM drop, rap verse, ballad, English lyrics` |

A generation without the key-changed final chorus, with English lyrics, or with a
long ambient intro is out of genre. Reject it.

---

## 3. Target lanes and what each lane demands

Live reads from `music/lanes.yaml` and `music/autonomy.yaml`.

| Lane | Surface | Gate | Required artifacts | Autonomy rung |
|---|---|---|---|---|
| `streaming` | distributor (DistroKid; alt TuneCore) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` | advisory |
| `sync` | songtradr, audiosparx | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` | advisory |
| `direct-license` | own-site | `gate_sync_ready` | `stems`, `license_tiers` | advisory |
| `youtube-gaming` | youtube (shape `loop-10min`) | `gate_youtube_authentic` | — | advisory |

Every rung is `advisory` (clean_publishes 0, platform_strikes 0, revenue_usd 0).
No lane may publish itself.

Two consequences that are decisions, not details:

1. **Stems are mandatory.** `sync`, `direct-license`, and the
   soundtradr/audiosparx package all require them. A track without stems is not
   sync-ready.
2. **The video shapes collide.** The genre's shape is `single-4min`; the
   `youtube-gaming` lane's own shape is `loop-10min`. One 4-minute showpiece
   render does not satisfy the gaming lane. Either render two shapes, or accept
   that `youtube-gaming` stays unreached. Flagged for j_kro — not resolved here.

---

## 4. Quota position (live read)

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

Full headroom: 0 standard downloads used this period. Generate and export
**through Suno Studio only** (unlimited), never the standard download button.
Run `gate_quota` before every generation and export.

---

## 5. Gate path for the finished artifact

1. `gate_lyrics_original` — human-authored lyric sheet, sha256-bound claim
2. `gate_stems_present` — ≥ 4 stems, non-zero bytes, ±0.5 s of the master
3. `gate_loudness` — −14 LUFS streaming / −16 LUFS sync, ±1 dB
4. `gate_quality` — reviewer model **different** from the producer model
5. `gate_release_ready` (streaming) / `gate_sync_ready` (sync, direct-license)
6. `gate_youtube_authentic` (youtube-gaming)
7. `gate_human_approval` — j_kro. Never auto-passes.

---

## 6. Reported engine path — verify, do not trust

The sibling briefs written today in this directory document the live generation
route and the queue schema (`music/briefs/sentimental-piano/room-with-the-light-going/brief.json`
`_queue` / `_route`; `music/briefs/trance/signal-before-dawn/brief.json` `_queue`).
That is another run's report, not a read made here. Verify the cluster state
before routing this track, and prefer a live probe over the transcript.

---

## 7. Defects found while writing this brief (with evidence)

### 7.1 The oracle emitted 28 cards for 14 genres — FIXED here

```
$ cat performance/music-oracle-runs.log      # before this run
2026-10-09T03:27:53 — oracle run: 14 scored, 14 created, top=chill-lounge(8.9)
2026-10-09T03:37:53 — oracle run: 14 scored, 14 created, top=chill-lounge(9.1)
```

`music/oracle.py` had no guard against a genre that already had an open card, and
the score drifts between runs (this genre: 7.55 → 7.75; chill-lounge 8.9 → 9.1 →
8.4 in a dry run today), so every run re-created every card. Each duplicate put a
second full stage chain in flight.

Fixed: `open_oracle_genres()` now maps genre → open card id from
`hermes kanban --board music list --json`, `create_kanban_card()` skips a genre
that is already open, and an unreadable board **fails closed** (no cards at all,
exit 1). Regression test: `music/test_oracle_dedupe.py` (12 tests, exit 0).

Proof against the real board payload, not a fixture:

```
$ python3 (probe) … /usr/bin/python3 …
tasks in payload      : 72
status distribution   : {'blocked': 3, 'done': 31, 'ready': 26, 'running': 6, 'todo': 6}
open genres from guard: 14        (one per registry genre)
cards created by a real run: 0 (create calls: 0)
skipped (genre already open): 14
guard vs live board: PASS
```

And end to end, in the unit's own context:

```
$ systemctl --user cat music-oracle.service   # ExecStart: /usr/bin/python3 …/music/oracle.py
$ systemctl --user start music-oracle.service
Result=success  ExecMainStatus=0
$ tail -1 performance/music-oracle-runs.log
2026-10-16T13:08:45 — oracle run: 14 scored, 0 created, 14 skipped (open),
  board_read_ok=True, top=chill-lounge(8.4)
```

### 7.2 The scheduled units pointed at the wrong repository — FIXED here

```
$ journalctl --user -u music-oracle.service -n 4     # before this run
Oct 16 08:00:00 nexus python3[185521]: /usr/bin/python3: can't open file
  '/home/j_kro/Projects/ai-content-pipeline/music/oracle.py': [Errno 2] No such file or directory
Oct 16 08:00:00 nexus systemd[1895]: music-oracle.service: Failed with result 'exit-code'.
```

`~/Projects/ai-content-pipeline` is a different tree with no `music/` directory.
The same mispointing was installed in all four music units. The oracle failed at
08:00 daily and the driver logged "dispatched 0" all day. The repo copies of the
units already held the correct path; the install step had been missed.

Installed and verified `music-oracle.service`, `music-policy-watch.service`,
`music-weekly-digest.service` (each byte-identical to the repo file after copy;
`daemon-reload` done). Backups of the previous units:
`/home/j_kro/.hermes/profiles/music-producer/cache/scratch/unit-backup-20261016/`.

### 7.3 Two dispatchers compete for the `music` board — NOT fixed, needs j_kro

`music/stages.yaml` routes by **stage** (`brief` → `producer`, `lyrics` → `writer`,
`gate` → `reviewer-deepseek`, `visual` → `videobot`, `publish` → `publishbot`).
The Hermes kanban dispatcher routes by **assignee**, and the oracle creates every
card with `--assignee music-producer`. The assignee path wins: the six oracle
cards running today were all claimed at 12:59:50 (event `claimed`, payload
`{"lock": "nexus:1113295", "run_id": 7}`) as `music-producer`, whatever their stage.

The installed `music-pipeline-driver.service` is inert and misdirected: it runs
the pre-parameterization driver from the other tree, which hardcodes
`BOARD="faceless-youtube"` and ignores `--board music`.

I did **not** install the corrected driver unit. Doing so would enable a second
dispatcher over the 26 ready cards the live payload reported at 13:08 while the
assignee dispatcher is already working them — duplicate agent runs on the same
cards. The fix is committed and one `install` away; the ownership decision is
j_kro's.

### 7.4 Gaps this stage cannot close

- **No anisong lyric blueprint** (§1). The planner reads
  `music/lyrics/blueprints/<genre>.yaml`; anime-opening has none, so the lyric
  sheet — the thing the `generate` stage is gated on — cannot be planned yet.
  Same gap independently reported for `anime-ending` by the sibling brief.
- `music/prompts/anime-opening.md` cites
  `campaigns/virtual-reflections/CAMPAIGN.md` as the source of the requirement.
  That directory does not exist in this tree (`find … -iname "*virtual*"` → no
  output). The album work is real (t_4bc3d251, t_93852e1f are `done`); the
  campaign file is not here.
- **`music-policy-watch.service` will still fail after the path fix.** It ran for
  5 min 3 s and was killed by its own `TimeoutStartSec=300`
  (`systemd: start operation timed out … status=130`, 2026-10-16T07:00). An agent
  run that web-searches six platforms does not fit in 5 minutes. Left unchanged —
  a timeout chosen without measurement is a guess.
- Whether the Virtual Reflections masters for tracks 7–8 already exist is not
  asserted here. Confirm before generating a duplicate master.

---

## 8. Recommended next stage

**`lyrics` → `writer`**, not `genre-select`: this brief already performs the
resolution `genre-select` would.

Deliverable for the writer: the anisong blueprint
(`music/lyrics/blueprints/anime-opening.yaml`) plus an **original, human-authored
Japanese lyric sheet** with the royal road under the chorus and a marked,
key-changed final chorus section. `--lyrics-mode ai` is forbidden for this genre:
the copyright path is the point, and the registry default is
`lyrics: human-original`.

Then, in order: `generate` (2 takes, Suno CDP, Studio export only — after
`gate_quota`), `curate`, `stems`, `master`, `gate` (different model),
`package`, `visual`, `publish` (PRIVATE / draft only — never public without
j_kro's approval), `track`.
