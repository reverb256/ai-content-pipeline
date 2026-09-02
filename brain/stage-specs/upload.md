# Stage Spec — Upload (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> This file is the contract the upload bot reads before publishing. The
> cardinal rule: NEVER set a video to PUBLIC without explicit human approval.

## STAGE
upload

## BOT
publishbot

## INPUT
- `campaigns/<name>/video/final.mp4` — the rendered video file to upload.
- `campaigns/<name>/metadata/seo.json` — title, description, tags, chapters.
- `campaigns/<name>/thumbnails/selected.png` — the chosen thumbnail.
- `platforms/youtube/upload-config.yaml` — channel-specific upload settings.
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md`.

## OUTPUT
- YouTube video uploaded as **PRIVATE** (or unlisted per upload-config).
- `campaigns/<name>/metadata/upload-report.json`:
  ```json
  {
    "video_id": "<real YouTube video ID>",
    "status": "private",
    "uploaded_at": "<ISO timestamp>",
    "title": "<title>",
    "duration_seconds": 0,
    "url": "https://youtu.be/<video_id>",
    "mechanical_gate": {"passed": true, "checks": {...}}
  }
  ```
- Kanban comment: video ID, status, URL, gate result, and a flag that human
  review is required before going public.

## SPEC (measurable)

### Video file validation
- `final.mp4` must exist and be non-empty (>1MB).
- Duration must match the narration duration (±5s) — same anti-truncation
  rule as the visuals stage. Re-verify with ffprobe before upload.

### Upload method
- Primary: **YouTube Data API v3** (resumable upload, supports metadata +
  thumbnail + chapters in one call).
- Fallback: **CDP (Chrome DevTools Protocol)** browser automation via the
  YouTube Studio upload flow if the API is unavailable.
- Log the method used in the upload report.

### Metadata application
- Apply title, description, tags, and chapters from `seo.json`.
- Set the selected thumbnail.
- Category, language, and license per `upload-config.yaml`.

### Privacy status — NON-NEGOTIABLE
- **ALWAYS upload as PRIVATE** (or unlisted if upload-config specifies).
- NEVER set to PUBLIC without explicit human approval via the review gate.
- The bot does NOT have authority to make content public. This is a hard
  pipeline rule: publishbot reports, human decides.

### Video ID — never fabricate
- The video ID in the report MUST be the ID returned by the upload API/CDP
  response. NEVER invent, guess, or synthesize a video ID.
- Verify the ID by querying the API for the video status after upload.

## MECHANICAL GATE (BLOCKS — run before commenting done)
```python
import json, os, subprocess, sys
name = "<name>"
checks = {}

# 1) Video file exists + non-empty
video_path = f"campaigns/{name}/video/final.mp4"
checks["video_exists"] = os.path.isfile(video_path) and os.path.getsize(video_path) > 1_000_000

# 2) Upload report exists + has a real video ID
report_path = f"campaigns/{name}/metadata/upload-report.json"
if os.path.isfile(report_path):
    r = json.load(open(report_path))
    vid = r.get("video_id", "")
    checks["has_video_id"] = bool(vid) and len(vid) >= 11  # YouTube IDs are 11 chars
    checks["id_not_placeholder"] = vid not in ("PLACEHOLDER", "TODO", "fake", "xxxx")
    checks["status_private"] = r.get("status") in ("private", "unlisted")
    checks["url_matches_id"] = r.get("url", "").endswith(vid) if vid else False
else:
    checks["has_video_id"] = False
    checks["id_not_placeholder"] = False
    checks["status_private"] = False
    checks["url_matches_id"] = False

# 3) Verify video ID via API (if credentials available)
try:
    result = subprocess.run(
        ["youtube", "videos", "list", vid], capture_output=True, text=True, timeout=30
    )
    checks["api_verified"] = "items" in result.stdout and vid in result.stdout
except Exception:
    checks["api_verified"] = False  # non-fatal if API unavailable, log warning

all_pass = all(checks.values())
print(f"video_id={json.load(open(report_path)).get('video_id','MISSING') if os.path.isfile(report_path) else 'NO_REPORT'}")
print(f"status={json.load(open(report_path)).get('status','MISSING') if os.path.isfile(report_path) else 'NO_REPORT'}")
print(f"checks={checks}")
print("PASS" if all_pass else "FAIL")
```
Any check failing → the bot MUST fix the issue (re-upload, correct metadata,
set to private) and re-run. Do NOT advance a failed upload.

## SCORED REVIEW (1-10, min pass 7)
1. **Video integrity** — file present, duration matches narration, not truncated.
2. **Metadata fidelity** — title/description/tags/chapters match seo.json exactly.
3. **Thumbnail set** — correct thumbnail applied, not default.
4. **Privacy correct** — status is private/unlisted, NOT public.
5. **Video ID real** — ID is from the API/CDP response, not fabricated.
6. **Report complete** — upload-report.json has all required fields.
7. **Human flag present** — comment explicitly states "human approval required before public."

PASS: all ≥ 7. FAIL: feedback must name the field + exact fix.

## HUMAN APPROVAL GATE (separate from scored review — MANDATORY)
After the scored review passes, the upload enters a **human approval queue**.
The bot MUST:
- Set status to PRIVATE (never auto-public).
- Comment on the kanban card: video ID, URL, "AWAITING HUMAN APPROVAL."
- NOT advance the card past the upload stage until the human approves.

The human reviews the private video, checks metadata, and either:
- Approves → bot changes status to PUBLIC (or schedules).
- Rejects → bot returns the card to the previous stage with feedback.

## DONE WHEN
final.mp4 exists and is valid, video uploaded via API or CDP, upload-report.json
contains a REAL video ID (verified via API if possible), status is PRIVATE,
mechanical gate PASSED, scored review ≥7, and human approval is explicitly
requested in the comment.
