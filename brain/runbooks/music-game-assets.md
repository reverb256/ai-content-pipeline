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
- [ ] `music/gates/gate_loop_points.py` PASS
- [ ] `music/gates/gate_sync_ready.py` PASS (`--lane game-assets`)
- [ ] All stems named according to `game-assets.py` naming convention.
- [ ] `perpetual_game_asset_v1.txt` included in `/docs`.
- [ ] Sample rate (44.1k/48k) explicitly stated in `metadata.json`.

Run the full gate matrix: `bash music/gates/check_gate_suite.sh`
