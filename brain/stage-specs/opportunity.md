# Stage Spec — Opportunity (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> This file is the contract the oracle bot reads before scoring and the
> reviewer uses to judge.

## STAGE
opportunity

## BOT
oracle

## INPUT (read before scoring)
- `brain/playbooks/arbitrage.md` (READ FIRST — the method, rubric, routing)
- `brain/RULINGS.md` (non-negotiable)
- `queries/x-search-recipes.md` (demand/supply query recipes)
- Kanban board `faceless-youtube` (existing cards — avoid duplicates)

## OUTPUT (write these)
- Production card on kanban board `faceless-youtube` (stage: opportunity)
  with the opportunity record in the card body (scores + evidence + route).
- `campaigns/<name>/opportunity.md` — scored opportunity record (use the
  template from `campaigns/translation-arbitrage/opportunity.md`).

## SPEC (measurable — the bot MUST satisfy these)

### Scoring rubric (per arbitrage.md)
Score each dimension 0-10 with evidence. Final = demand × gap ×
(monetization × automation × platform). Policy safety is a GATE (0 = no card).

| Dimension | Weight | What evidence looks like |
|-----------|--------|------------------------|
| Demand | 1.0 | Question volume, engagement numbers, news-cycle heat — cite posts/metrics |
| Supply gap | 1.0 | Sparse quality supply, no dominant creator — cite "best accounts" query results |
| Monetization | 0.8 | RPM range, affiliate/product fit — cite industry benchmarks |
| Automation fit | 0.8 | Can the machine produce it? (screen-recording = high, original footage = low) |
| Policy safety | 1.0 (gate) | Original + educational + non-repetitive = high; slop-adjacent = 0 |
| Platform fit | 0.5 | Where does this win? X thread / YouTube long-form / Shorts / translation / blog |

### Thresholds
- **Score > 6** → strong opportunity: create production card (stage: opportunity)
- **Score 4–6** → watchlist: add to watchlist.md, re-check weekly
- **Score < 4** → pass: do not waste production on it

### Evidence minimums
- Demand: ≥2 demand signal queries run, engagement data cited with URLs
- Supply gap: ≥1 supply gap query run, gap documented with source
- Each dimension score justified (URL or metric), no fabricated numbers
- Routing decision: niche + format + platform + language (specific, not vague)

### Anti-duplication
- Before creating a card, check the board + watchlist. Do not duplicate an
  active or watchlisted opportunity.

## MECHANICAL GATE (blocks advance — run BEFORE posting the card)
```python
python3 - <<'EOF'
import re, sys
p = "campaigns/<name>/opportunity.md"
text = open(p).read()
dims = ["Demand", "Supply Gap", "Monetization", "Automation Fit", "Policy Safety", "Platform Fit"]
found = {}
for d in dims:
    m = re.search(rf'\|\s*{d}\s*\|\s*(\d+)', text)
    if m: found[d] = int(m.group(1))
print(f"dimensions_scored={len(found)}/6")
print(f"scores={found}")
final = re.search(r'\|\s*\*\*Final\*\*\s*\|\s*([\d.]+)', text)
if final: print(f"final_score={final.group(1)}")
else: print("FAIL no final score")
policy = found.get("Policy Safety", 0)
if policy == 0:
    print("FAIL policy safety = 0 (gate failed)")
elif len(found) < 6:
    print("FAIL incomplete scoring")
elif not final:
    print("FAIL no final score")
elif float(final.group(1)) > 6:
    print("PASS production card")
elif float(final.group(1)) >= 4:
    print("PASS watchlist")
else:
    print("PASS below threshold (no card)")
EOF
```
- FAIL → rework the opportunity record (fix scoring / add evidence). Do NOT
  post a card with incomplete or fabricated scores.
- Card body must include the full scoring table so the driver can read the
  stage and route.

## SCORED REVIEW (1-10, min pass 7)
1. **Demand evidence** — queries run, engagement data real (not asserted)
2. **Supply gap evidence** — gap documented with source URLs
3. **Score math** — all 6 dimensions justified; no fabricated numbers
4. **Policy safety** — honest assessment, not rubber-stamped
5. **Routing** — specific niche/format/platform/language (not vague)
6. **Non-duplicate** — not already on the board or watchlist
7. **Conclusion clarity** — clear produce / watchlist / pass call

PASS: all ≥ 7. FAIL: feedback must name the dimension + exact fix.

## DONE WHEN
`campaigns/<name>/opportunity.md` exists with all 6 dimension scores + final
score + routing decision, mechanical gate PASSED, card created on
`faceless-youtube` with stage: opportunity, and no duplicate of an active card.
