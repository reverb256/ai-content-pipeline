# Enterprise-Grade Quality Gates — Research Findings & Recommendations

> Source: external research into broadcast QC, LLM-as-judge calibration, and mature content factories.
> Date: 2026-09-02. Scope: gap analysis against our current gate system (3 executable gates + 13 stage specs).

## What the best systems do that we don't

### 1. Calibrate the LLM judge against human labels (CRITICAL)
Every mature pipeline that uses LLM-as-judge (InkWarden, futurecraft.pro, Confident AI, Divinci AI) maintains a **golden dataset** of 50-200 human-labeled examples and **measures agreement** (Spearman ρ ≥ 0.7, Cohen's κ ≥ 0.6) before trusting the judge with a gate. Uncalibrated judges carry position bias, verbosity bias, and self-serving bias — a judge that stamps everything "pass" hits 90% agreement while being useless.

**Our gap:** Our scored review layer (1-10 rubric) runs on the same model family that produced the work, with no calibration data. We don't know if a "7" means the same thing across runs or models. We have no adversarial test cases (fabricated citations, off-topic content) to verify the judge can actually catch bad output.

**Fix:** Build a golden set of 50+ human-scored scripts/videos. Run the judge quarterly, measure correlation vs human labels, and re-calibrate the rubric. Add 5-10 adversarial cases that MUST fail. Fail the judge if it passes them.

### 2. EBU R128 loudness + true peak + LRA gate (HIGH)
Broadcast-grade pipelines (Point Media Video Inspector, sonic-gate, loudcheck, oximedia-qc) don't just check "not silent" — they measure **integrated LUFS**, **true peak (dBTP)**, and **loudness range (LRA)** against a formal standard (YouTube/-14 LUFS, EBU R128/-23, ATSC A/85/-24). Platforms reject or normalize audio that misses these targets.

**Our gap:** `gate_voice.py` only checks `mean_volume < -45dB` (silence detection) and duration match. A clipped, hot, or LRA-flat file passes. We have no LUFS measurement, no true peak gate, no loudness range check.

**Fix:** Add a `gate_loudness.py` that runs `ffmpeg -af loudnorm=print_format=json` and gates on integrated LUFS (±1.5 of target), true peak (≤ -1.0 dBTP), and LRA (6-12 LU for dialogue). Use `loudcheck` or `sonic-gate` as a reference implementation.

### 3. ASR-based audio-to-script verification (HIGH)
MishkaVids (22-check pipeline) and others run **speech recognition over the final master** and diff against the script: word error rate > 6% = regenerate. This catches TTS mispronunciations, dropped words, and truncation that a duration check misses entirely.

**Our gap:** We verify duration (words/160wpm ±20%) and non-silence, but never verify that the audio actually *says what the script says*. A TTS glitch that drops 30% of words but stretches the rest to fill the duration would pass our gate.

**Fix:** Add ASR verification — transcribe the final audio (Whisper or similar), diff against script narration, fail if WER > 6% or if sections are missing.

### 4. Motion energy + freeze/black frame detection (HIGH)
MishkaVids measures **mean absolute luma change** over a center crop sampled 2x/sec. Below 0.05 for >10s = fail. Broadcast QC tools (Video Inspector, media-os) detect freeze frames via `freezedetect`, black frames via `blackdetect`, and bitrate anomalies.

**Our gap:** `gate_visuals.py` checks audio stream presence and truncation only. A video with a frozen first 30s, black frame runs, or parked visual for 60s passes. The anti-slideshow rule is in the spec but not mechanically enforced at the gate.

**Fix:** Add `gate_visual_qc.py`: freeze detection (`freezedetect=duration=0.5`), black detection (`blackdetect=d=1.0`), motion energy sampling, and per-section beat count verification (≥ ceil(words/45) scenes).

### 5. Thumbnail OCR + readability verification at feed size (MEDIUM)
VidNo and others resize thumbnails to 168×94 and OCR-verify text readability. GrabThumbs checks text density and line balance. YouTube serves thumbnails at this size in the feed — unreadable text = killed CTR.

**Our gap:** We check text word count (≤3) and file size (>10KB) but never verify readability at actual render size. A 3-word text in thin low-contrast font over a busy background passes.

**Fix:** Add a gate step that resizes the thumbnail to 168×94, runs OCR (Tesseract or vision model), and verifies the on-image text is actually extractable. Fail if OCR returns empty or low-confidence.

### 6. Evidence-trace mechanical gate (HIGH)
Elevarus and others enforce **source-grounded fact-checking**: every claim is checked against retrieved source passages, not against the model's own memory. The mechanic is "which claims are directly supported by these specific passages?"

**Our gap:** The stage spec says "every claim traces to research.md" but the mechanical gate only checks word count and skeleton structure. A script with 5 claims where only 3 are in research.md passes.

**Fix:** Add `gate_evidence.py`: extract claims from script.md (numbered bolded statements or statistics), verify each has a corresponding `Source:` line with a URL, and cross-check against research.md. Fail on unverified claims.

### 7. Pre-audit / quarantine before publish (MEDIUM)
The dev.to/morinaga pipeline runs a **pre-audit 15 hours before the publish window** — catching failures at breakfast instead of burning the midnight slot. Specs that would fail are quarantined and regenerated.

**Our gap:** Our upload gate runs at upload time. If it fails, the publish slot is already burned. No pre-audit step exists.

**Fix:** Add a pre-flight gate that runs all mechanical checks (loudness, ASR, evidence, visual QC) at the SEO/review stage — before the upload stage — so failures are caught with time to fix.

### 8. Metadata consistency cross-stage check (MEDIUM)
Our pipeline generates metadata (title, description, chapters, tags) that must be consistent with the script, research, and video. No gate verifies cross-stage consistency.

**Fix:** Add `gate_metadata_consistency.py`: verify the seo.json title matches the script hook (keyword overlap), chapters align with script section timestamps, tags include primary keyword, and description claims are supported by research.md.

### 9. Regression testing for the LLM review layer (MEDIUM)
Confident AI, Coverge, and Divinci maintain a **golden dataset** of known-good and known-bad examples, run the full eval on every prompt/model change, and block degrades >3%. This catches judge drift when models or rubrics change.

**Fix:** Build a golden set of 50+ campaigns with known outcomes. Run the scored review gate against them after any prompt/model change. Track pass rates over time.

### 10. Three-valued gate verdict (PASS/HOLD/RETRY) (MEDIUM)
The `content-qa-pipeline-public` framework uses three verdicts: PASS (advance), HOLD (park, reason recorded, human escalation), and RETRY (bounded retry then escalate). This prevents a flaky LLM judge from either blocking everything or rubber-stamping.

**Fix:** Our gates are binary (pass/fail). Add a HOLD state for uncertain verdicts (e.g., LLM judge score 6.5-7.5, or ASR WER 5-8%) that routes to human review instead of auto-passing or auto-failing.

### 11. A/V sync drift check (LOW-MEDIUM)
quevidkit and broadcast QC tools measure audio-video timing offset at 20+ checkpoints. Splicing without adjusting timestamps causes progressive drift.

**Fix:** Add A/V sync sampling to `gate_visuals.py`: extract audio from video at 5 checkpoints, compare timing against the narration file, fail if drift > 200ms at any point.

### 12. Per-section beat density enforcement (MEDIUM)
The anti-slideshow rule is in the script spec (≥ ceil(words/45) visual beats per section) but is NOT mechanically enforced at the visuals gate. A video with 8 scenes holding ~60s narration each would pass the current gate.

**Fix:** Parse script.md section word counts, count scene cuts in final.mp4 (via scene detection), and verify each section has ≥ ceil(words/45) visual beats.

---

## Ranked recommendations (by impact)

| # | Recommendation | Impact | Effort |
|---|---------------|--------|--------|
| 1 | **Calibrate LLM judge** — golden dataset, human labels, adversarial cases, quarterly recalibration | Critical | Medium |
| 2 | **EBU R128 loudness gate** — integrated LUFS, true peak, LRA | High | Low (ffmpeg) |
| 3 | **ASR audio-to-script verification** — WER diff, catch TTS glitches | High | Medium |
| 4 | **Evidence-trace mechanical gate** — every claim → URL in research.md | High | Medium |
| 5 | **Motion energy + freeze/black detection** — anti-freeze, anti-park | High | Low (ffmpeg) |
| 6 | **Per-section beat density enforcement** — mechanical anti-slideshow | Medium | Medium |
| 7 | **Thumbnail OCR at 168×94** — verify text is machine-readable | Medium | Low |
| 8 | **Pre-audit quarantine** — run all gates 15h before publish | Medium | Low |
| 9 | **Metadata consistency cross-stage check** | Medium | Low |
| 10 | **Regression testing for review layer** — golden set, block regressions | Medium | Medium |
| 11 | **Three-valued gate (PASS/HOLD/RETRY)** — handle uncertainty | Medium | Low |
| 12 | **A/V sync drift check** — sample 5+ checkpoints | Low-Medium | Low |

## Sources reviewed

- https://github.com/NesDevr/video-factory — word budgets, visual beat rules, mechanical validator
- https://github.com/codinglone/sonic-gate — LUFS, silence, format checking
- https://github.com/chaoz23/loudcheck — EBU R128 / ATSC A/85 compliance verdicts
- https://github.com/damionrashford/media-os — VMAF, loudness, freeze/black/silence detection
- https://github.com/GouthamUKS/QC_Scanner — broadcast QC, loudness, A/V sync
- https://github.com/thumpersecure/quevidkit — forensic A/V sync drift, thumbnail mismatch
- https://github.com/LesterALeong/llm-evalgate — calibrated LLM judges, regression gates
- https://github.com/euuuuuuan/content-qa-pipeline-public — three-valued verdicts, fail-closed rails
- https://github.com/bengodgart/llm-judge-calibration — Cohen's kappa, bias probes
- https://github.com/buildaloud/agentic-content-pipeline — 15-reviewer fan-out, tone gate
- https://github.com/ericosiu/ai-marketing-skills — content quality gate, AI slop penalty
- https://dev.to/mishkavids — 22-check pipeline, motion energy, ASR gaps, WER diffs
- https://dev.to/morinaga — pre-audit quarantine, Jaccard dedup
- https://elevarus.com — fail-fast gates, source-grounded fact-check
- https://www.inkwarden.io — LLM judge blind spots, calibration
- https://futurecraft.pro — judge calibration, bias tests, CI gates
- https://www.confident-ai.com — golden dataset, regression testing
- https://coverge.ai — golden dataset, slice-aware gates
- https://iotdigitaltwinplm.com — 5-stage eval pipeline, judge calibration
- https://galtea.ai — complete eval guide, Pearson r > 0.7
- https://llmversus.com — eval harness architecture
- https://divinci.ai — slice-aware, version-anchored regression
- https://clawrxiv.io — adversarial robustness of LLM judges
- https://point.tv — broadcast QC, EBU R128, 50+ rules
- https://vidno.ai — thumbnail generation with OCR readability
- https://github.com/AlperNab/thumbnail-analyzer — CTR heuristic, text readability
- https://lseo.com — OCR-ready design for thumbnails
- https://github.com/hotchilianalytics/verityngn-oss — multimodal claim verification
- https://stackcompass.dev — blocking scripts, gate gaming, calibration drift
