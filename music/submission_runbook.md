# Music Streaming Submission Runbook (DistroKid / TuneCore)

This runbook defines the human-gated process for moving a packaged release from the `music/packages/streaming/` directory to a live streaming platform.

## 1. Pre-Flight Check
Before starting, verify the release has passed the `gate_release_ready.py` check.
- Package Location: `/home/j_kro/Projects/ai-content-pipeline/music/packages/streaming/<track_id>/`
- Required Artifacts:
    - `master.wav` (Verified loudness -14 LUFS)
    - `artwork.jpg` (3000x3000px, RGB)
    - `manifest.json` (Contains title, artist, ISRC, AI disclosure)

## 2. Distributor Selection
Follow the Architecture Logic:
- **PRIMARY: DistroKid**
    - Use for most tracks.
    - Account: $24.99/yr (Unlimited).
    - Advantage: No caps, no exclusions.
- **SECONDARY: TuneCore**
    - Use ONLY for Suno partner-model tracks (eligible since 2026-09-08).
- **CRITICAL RULE:** Never upload the same track to both. This triggers Spotify's spam filters and can lead to account termination.

## 3. Submission Steps (Manual)
1. **Login** to the chosen distributor.
2. **Upload Audio:** Select `master.wav` from the package directory.
3. **Upload Artwork:** Select `artwork.jpg` from the package directory.
4. **Enter Metadata** (From `manifest.json`):
    - Artist Name
    - Release Title
    - Genre
    - Lyrics (if applicable)
    - Explicit Content Flag
5. **ISRC Management:**
    - If the manifest contains a pre-assigned ISRC, enter it manually.
    - Otherwise, allow the distributor to assign one and **record it back** into the `manifest.json`.
6. **AI Disclosure:**
    - Mark the "AI-Generated" or "Synthetic Voice" checkbox as required by the platform.
7. **Payment:** Confirm annual subscription is active.

## 4. Post-Submission
1. **Confirm Ingestion:** Wait for the "Processing" status to clear.
2. **Update Manifest:** Save the final Distributor-assigned ISRC and the "Live Date" to the track manifest.
3. **Notify Analyst:** Move the kanban card to the `track` stage for ROI monitoring.
