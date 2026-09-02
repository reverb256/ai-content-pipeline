# Stage Spec — Thumbnail (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> This file is the contract the thumbnailbot reads before generating and the
> reviewer uses to judge.

## STAGE
thumbnail

## BOT
thumbnailbot

## INPUT (read before generating)
- `campaigns/<name>/script.md` (the hook + key moments — what the thumbnail
  must match)
- `campaigns/<name>/video/final.mp4` or key frames (to match content — no
  misleading thumbnails)
- `brain/RULINGS.md` (non-negotiable)
- `brain/playbooks/model-routing.md` (provider chain)
- `scripts/api/pick-provider.sh image` (provider router)

## OUTPUT (write these)
- `campaigns/<name>/thumbnails/variant-1.png`, `variant-2.png`, `variant-3.png`
  — 2–3 variants per video.
- Kanban comment: paths, variant count, text word count per variant, provider
  tier, gate result.

## SPEC (measurable — the bot MUST satisfy these)

### Variant budget
- **2–3 variants** per video. More than 3 wastes generation; fewer than 2
  gives no A/B signal.

### Text rule (NON-NEGOTIABLE)
- **≤3 words of on-image text per variant.** Count words, not estimated.
- Text MUST be readable at **168×94** (YouTube feed size). If you can't read
  it at that size, the text is too small or the contrast is too low.

### Visual rules
- **High contrast** — one focal subject pops at feed size.
- **Emotion or curiosity** — the image earns the click (face expression,
  tension, unexpected visual).
- **Title accuracy** — the thumbnail MUST match the actual video content.
  Misleading thumbnails = policy risk + audience trust loss.

### Anti-template rule (inauthentic content defense)
- Variants must differ **visually** from prior thumbnails in the campaign
  history. No copy-paste template with only the text swapped. Per
  QUALITY_DOCTRINE.md: uniformity is the demonetization risk.

### Provider chain
- Use `scripts/api/pick-provider.sh image` — ComfyUI FLUX (local) > xAI image
  > Ideogram. Best available first. Log the tier to
  `performance/model-routing.log`.

## MECHANICAL GATE (blocks advance — run BEFORE commenting done)
```python
python3 - <<'EOF'
import os, glob, re, sys
d = "campaigns/<name>/thumbnails"
files = glob.glob(f"{d}/*.png") + glob.glob(f"{d}/*.jpg")
print(f"variant_count={len(files)}")
all_ok = True
for f in files:
    size = os.path.getsize(f)
    status = "OK" if size > 10000 else "FAIL too small"
    if size <= 10000: all_ok = False
    print(f"  {os.path.basename(f)}: {size} bytes {status}")
    # Text overlay count from filename convention: variant-1-2words.png
    base = os.path.basename(f)
    m = re.search(r'(\d+)words?', base)
    if m:
        wc = int(m.group(1))
        tstatus = "OK" if wc <= 3 else "FAIL >3 words"
        if wc > 3: all_ok = False
        print(f"    text_words={wc} {tstatus}")
if len(files) < 2:
    print("FAIL too few variants (<2)")
    all_ok = False
print("PASS" if all_ok else "FAIL")
EOF
```
- FAIL → regenerate (fix text count / contrast / file size). Do NOT advance
  with a thumbnail that fails the gate.

## SCORED REVIEW (1-10, min pass 7)
1. **Text economy** — ≤3 words, readable at feed size
2. **Contrast** — focal subject pops at 168×94
3. **Title accuracy** — matches the video (no misleading)
4. **Anti-template** — visually distinct from prior thumbnails (not slop)
5. **Emotion/curiosity** — earns the click
6. **Provider logged** — tier recorded in model-routing.log
7. **Overall clickworthiness** — would you click?

PASS: all ≥ 7. FAIL: feedback must name the variant + exact fix.

## DONE WHEN
2–3 variant files exist in `campaigns/<name>/thumbnails/`, each >10KB, ≤3 words
text per variant, high contrast, readable at feed size, anti-template check
passes, provider tier logged, and the kanban comment reports paths + variant
count + gate result.
