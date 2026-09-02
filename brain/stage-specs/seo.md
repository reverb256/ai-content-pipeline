# Stage Spec — SEO (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> This file is the contract the SEO bot reads before optimizing and the
> reviewer uses to judge metadata quality.

## STAGE
seo

## BOT
seobot

## INPUT
- `campaigns/<name>/script.md` — the narration script (for keyword extraction).
- `campaigns/<name>/video/final.mp4` — the rendered video (for chapter timing).
- `campaigns/<name>/research.md` — evidence package (for authoritative terms).
- `brain/playbooks/platforms.md` — platform-specific SEO rules.
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md`.

## OUTPUT
- `campaigns/<name>/metadata/seo.json` — structured metadata package:
  ```json
  {
    "title": "<title>",
    "description": "<description with timestamps>",
    "tags": ["tag1", "tag2", ...],
    "chapters": [{"title": "...", "time": "0:00"}, ...],
    "keywords": {"primary": "...", "secondary": ["..."]},
    "mechanical_gate": {"passed": true, "checks": {...}}
  }
  ```
- Kanban comment: title length, tag count, chapter count, gate result.

## SPEC (measurable)

### Title
- Length: **60-70 characters** (hard limit 70 — YouTube truncates titles past ~70).
- Primary keyword **front-loaded** (within the first 30 characters).
- Must communicate the payoff/tension — no clickbait, no filler words.
- One title. No A/B variants at this stage (A/B is a distribution decision).

### Description
- First 2-3 lines (above the fold, ~150 chars) must contain the primary keyword
  + a value proposition.
- Include a **timestamps section** (chapters) in `MM:SS Title` format.
- 150-300 words total. Natural language, not keyword-stuffed.
- Include 3-5 secondary keywords woven into prose.

### Tags
- **5-8 tags** total (YouTube allows ~500 chars of tags; 5-8 well-chosen tags
  outperform 20 stuffed ones).
- Tag 1 = exact primary keyword phrase.
- Mix of broad (high-volume) and long-tail (specific) terms.
- No duplicate or near-duplicate tags.

### Chapters (timestamps)
- Minimum 3 chapters for videos >5 min; 1 per major section.
- Format: `MM:SS Chapter Title` — strictly increasing timestamps.
- First chapter starts at `0:00`.
- Each chapter title is a concise phrase (not a sentence).

### Evidence / no-fabrication
- Do not invent statistics or claims in the metadata. If the script makes a
  claim, the description may reference it but must not exaggerate.

## MECHANICAL GATE (BLOCKS — run before commenting done)
```python
import json, sys
p = "campaigns/<name>/metadata/seo.json"
m = json.load(open(p))
title = m["title"]
tags = m["tags"]
desc = m["description"]
checks = {}
checks["title_len_ok"] = 60 <= len(title) <= 70
checks["title_frontloaded"] = len(m["keywords"]["primary"]) > 0 and m["keywords"]["primary"].lower() in title[:30].lower()
checks["tags_count_ok"] = 5 <= len(tags) <= 8
checks["tags_no_dupes"] = len(tags) == len(set(t.lower() for t in tags))
checks["desc_has_timestamps"] = any(line.strip()[:2].isdigit() and ":" in line for line in desc.splitlines())
checks["chapters_valid"] = len(m.get("chapters", [])) >= 3 and m["chapters"][0]["time"] == "0:00"
all_pass = all(checks.values())
print(f"title_len={len(title)} tags={len(tags)} chapters={len(m.get('chapters',[]))}")
print(f"checks={checks}")
print("PASS" if all_pass else "FAIL")
```
Any check failing → the bot MUST fix the metadata and re-run. Do NOT advance
with a failed gate.

## SCORED REVIEW (1-10, min pass 7)
1. **Title quality** — front-loaded keyword, clear payoff, no truncation risk.
2. **Description completeness** — keyword in fold, timestamps present, natural prose.
3. **Tag strategy** — right count, mix of broad/long-tail, no dupes.
4. **Chapter accuracy** — timestamps align with actual video sections.
5. **Keyword alignment** — primary/secondary terms match script + research.
6. **Click-through likelihood** — would a viewer click based on title + thumbnail context?
7. **No fabrication** — no invented claims in metadata.

PASS: all ≥ 7. FAIL: feedback must name the field + exact fix.

## DONE WHEN
seo.json exists, title is 60-70 chars with front-loaded keyword, 5-8 non-duplicate
tags, description contains timestamps, chapters start at 0:00 and are strictly
increasing, mechanical gate PASSED, and the comment reports the measured counts.
