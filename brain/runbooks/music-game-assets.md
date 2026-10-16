# Marketplace Runbook: Game Asset Distribution (2026)

This runbook defines the operational procedure for shipping AI-generated music asset packs.

## 1. itch.io (Primary - Full Automation)
itch.io is the preferred target due to explicit AI Audio tagging and the `butler` CLI.

### Technical Workflow
- **Tool:** `butler` (Official itch.io CLI)
- **Authentication:** API Key stored in `~/.hermes/vault/itch_io_key`
- **Upload Command:**
  `butler push <package_dir> user/game-asset-pack:<channel> -t <version> -m "Update: New Elemental Fire Pack"`
- **Tagging:** 
  - Must set `AI-Generated` tag.
  - Set `Loopable`, `WAV`, `Stem-Pack` tags.

### Product Page Requirements
- **Description:** Clear list of what's included (X loops, Y stems, Z one-shots).
- **Licence:** Attach `perpetual_game_asset_v1.txt`.
- **Preview:** Upload a 30-second combined preview track.

---

## 2. Unity Asset Store (Secondary - Human Gated)
The Unity Asset Store requires a vetted Publisher Account and a manual review process.

### Setup (Human Gate)
- **Account:** Create Publisher Account at `publisher.unity.com`.
- **Verification:** Requires identity/tax documents (Human-only).

### Submission Workflow
- **Packaging:** Create a `.unitypackage` containing the `loops/`, `stems/`, and `metadata.json` directories.
- **Metadata:** Define "Category: Audio" -> "Sub-category: Music".
- **Review:** Expect 5-15 business days for moderation.
- **Automation:** Playwright adapter handles the upload of the `.unitypackage` once the account is live.

---

## 3. GameDev Market (General)
For other indie markets (e.g., Gamedev Market), use the "Direct License" pattern.

- **Mechanism:** Upload ZIP to Gumroad/own-site.
- **Linkage:** Post links to the packs in the `youtube-gaming` video descriptions.
- **Licence:** Apply `perpetual_game_asset_v1.txt`.

## Summary Checklist for Package Release
- [ ] `music/gates/gate_loop_points.py` PASS on EVERY loop — run the sweep:
      `python3 music/gates/gate_loop_points.py --pack-dir <pack>`
- [ ] `music/gates/gate_sync_ready.py` PASS in pack mode (default for this lane;
      it measures every loop's seam too):
      `python3 music/gates/gate_sync_ready.py --package-dir <pack> --lane game-assets`
- [ ] All stems named according to `game-assets.py` naming convention.
- [ ] `perpetual_game_asset_v1.txt` included in `/docs` (and copied into the
      pack as `LICENCE.txt`).
- [ ] Sample rate (44.1k/48k) explicitly stated in the manifest's `metadata`
      object — the gate ffprobes every file and checks the stated rate is real.

## Package shape the gates accept (measured 2026-10-16, card t_5ed495eb)

`gate_sync_ready --lane game-assets` validates a PACK, not a single track
(`--mode pack` is the default for this lane; `--mode track` keeps the sync /
direct-license shape for those lanes):

```
manifest.json      metadata object (title, artist, bpm, key, mood, genre,
                   sample_rate) + pack_manifest counts that MATCH the files
                   on disk + per-loop records
loop_points.json   a "loops" object: one entry per loop file, keyed by
                   pack-relative path, each {loop_start_s, loop_end_s, seamless}
loops/  stems/     real audio (ffprobe), counts as declared, stems mutually
(one_shots/, sfx/) time-aligned within +/-0.5 s, loops with a span >= 2 s
clearance_doc.pdf  a real PDF (%PDF-), not a renamed text file
ai_disclosure.txt  the AI role, for the marketplace AI-Generated tag
LICENCE.txt        the lane's licence of record, byte for byte
                   (music/licences/perpetual_game_asset_v1.txt); the gate
                   compares it and the manifest binds it by sha256
```

Generate the pack with `python3 music/assets/pack.py <master.wav> --genre <g>`
then run the two gates above. Loops are cut bar-aligned at the source tempo and
never shorter than the 2 s musical floor (`MIN_LOOP_SPAN_S`, one definition in
`music/gates/gate_loop_points.py`, imported by the gate and the generator).

Run the full gate matrix: `bash music/gates/check_gate_suite.sh`
