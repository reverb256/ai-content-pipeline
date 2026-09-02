# Stage Spec — Script (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. Every stage = SPEC + MECHANICAL GATE +
> SCORED REVIEW. This file is the contract the scriptwriter bot reads before
> writing and the reviewer uses to judge.

## STAGE
script

## BOT
scriptwriter

## INPUT (read before writing)
- Evidence package: `campaigns/<name>/research.md`
- Opportunity / kanban card body (has score + route)
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md` (non-negotiable)
- Duration target comes from the CARD (set by oracle) or defaults below.

## OUTPUT (write these)
- `campaigns/<name>/script.md` — full narration script with per-section
  structure below.
- Self-report in the kanban comment: total word count, per-section counts,
  estimated duration at 160 wpm, and the mechanical check result.

## SPEC (measurable — the bot MUST satisfy these)

### Duration → word budget (NON-NEGOTIABLE, count words)
Spoken target: duration_target_minutes (default 8 for explainer, 10 for
long-form, card may set a target). Budget = minutes × 160 words, MINIMUM.

| Target length | Min words | Max words |
|---|---|---|
| 5 min | 750 | 900 |
| 8 min | 1,200 | 1,450 |
| 10 min | 1,500 | 1,800 |
| 15 min | 2,250 | 2,700 |

- You MUST write at least the MINIMUM. The system counts words after
  generation. Below minimum = FAIL, no advance.
- Do NOT write "approximately X minutes" in the script. Write words.
- Section budget: distribute the total across sections proportionally to
  importance; NO section may exceed ~40% of total words.

### Structure (required skeleton)
1. **Hook** (first 3-8s spoken / ~15-25 words): state the payoff or the
   tension. No "in this video", no channel intro, no filler openers.
2. **Stakes / context** (~15-30s / ~40-80 words): why it matters NOW.
3. **Body sections** (3-5 numbered): each opens with the ANSWER then
   explains (inverted pyramid). Every ~60-90s include a pattern interrupt /
   re-hook line.
4. **Payoff / CTA**: resolve the promised payoff; tell them what to watch
   next with a reason (not just "subscribe").

### TTS pacing (written into the script)
- Short sentences. Active voice. One idea per sentence.
- Numbers written as full words where spoken ("eighteen percent", not "18%").
- Mark pause beats: "Pause after X." for the TTS layer.
- Read-aloud test: if a sentence is a mouthful, cut it.

### Visual notes (per section — feeds videobot)
- Per section, note 2-5 visual beats (what the viewer sees).
- CRITICAL anti-slideshow rule: narration words per visual beat ≤ 45
  (~16s at 160wpm). A section with 200 words needs ≥ 5 visual beats or it
  must be split. Videobot will be held to this.
- Note transitions between sections.

### Evidence / no-fabrication
- Every claim traces to `research.md`. No invented numbers, quotes, or
  sources. No speculation presented as fact.

## MECHANICAL GATE (blocks advance — run BEFORE commenting done)
After writing script.md, the bot RUNS this check (copy to terminal):
```bash
python3 - <<'EOF'
import re, sys
p = "campaigns/<name>/script.md"
text = open(p).read()
# strip frontmatter + markdown headers + visual/TTS-note lines? No: count
# narration = ALL prose lines except headings/notes/bullets starting with
# ** or 'Visual:' or 'TTS note:' or source lines.
words = 0
for line in text.splitlines():
    s = line.strip()
    if not s or s.startswith('#') or s.startswith('**') or s.startswith('<!--'): continue
    if s.startswith('Visual:') or s.startswith('TTS note:') or s.startswith('Source') or s.startswith('>'):
        continue
    words += len(s.split())
print(f"narration_words={words}")
print("PASS" if words >= 1200 else "FAIL below minimum")
EOF
```
- PASS → advance. FAIL → expand the thin sections (the bot must NOT advance
  on a failed word count; comment the count and rework).
- If the script targets a card-specific duration, the minimum is
  (minutes × 160) with the same rule.

## SCORED REVIEW (when a review pass runs — 1-10, min pass 7)
1. **Hook strength** — does the first sentence make a viewer stay?
2. **Pacing/flow** — rhythm, no dead spots, pattern interrupts present.
3. **Evidence integrity** — every claim in research.md; nothing fabricated.
4. **Spoken clarity** — short sentences, active voice, TTS-readable.
5. **Structure** — hook/stakes/body/payoff present and proportional.
6. **Visual feasibility** — notes give videobot enough beats (no 60s park).
7. **SEO/angle alignment** — matches the opportunity score + audience.
8. **Overall watchability** — would you watch to the end?

PASS: all ≥ 7. FAIL: feedback must name the section + exact fix.

## DONE WHEN
script.md exists, word-count gate PASSED (>= min, counted), every claim
traces to research.md, visual notes satisfy the anti-slideshow beat rule,
and the comment reports the measured count.
