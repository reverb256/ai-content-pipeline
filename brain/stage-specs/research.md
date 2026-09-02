# Stage Spec — Research (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> This file is the contract the researcher bot reads before building the
> evidence package and the reviewer uses to judge.

## STAGE
research

## BOT
researcher

## INPUT (read before building)
- Opportunity card on kanban board `faceless-youtube` (stage: research) —
  the scored opportunity with route + evidence leads.
- `brain/RULINGS.md` (non-negotiable)
- `brain/proof.md` (evidence standards)
- `brain/playbooks/arbitrage.md` (context — what the oracle found)
- Tools: `web_search`, `web_extract`, `x_search`, CDP browser

## OUTPUT (write these)
- `campaigns/<name>/research.md` — evidence package with verified claims,
  sources, contradictions, and unknowns.
- Kanban comment: claim count, source count, gate result.

## SPEC (measurable — the bot MUST satisfy these)

### Claim budget
- **3–7 verified claims** in the package.
- Every consequential claim (numbers, quotes, studies, statistics) MUST trace
  to a direct URL in the package. No URL = no claim.

### Claim structure (required)
Group claims into:
1. **Demand signals** — evidence people are asking / searching / complaining.
2. **Supply gap evidence** — proof the quality supply is thin.
3. **Mechanisms worth explaining** — the "why" / how-it-works facts that make
   a viewer stay (not just surface trivia).

### Honesty rules (non-negotiable)
- **No fabrication.** Never invent numbers, quotes, or sources. If evidence is
  missing, say so — do not fill the gap with a plausible assumption.
- **Separate inference from fact.** Label inference explicitly
  ("This suggests…", "Likely because…"). Verified facts get URLs.
- **State contradictions.** Where sources disagree, document the disagreement.
- **State unknowns.** What the evidence does NOT prove — gaps returned, not
  hidden. This is as valuable as what it proves.

### Source quality
- Primary sources preferred (official reports, data pages, original posts).
- X posts: prefer high-engagement threads from domain experts over viral
  one-liners.
- Each claim gets a full URL on its own `Source:` line.

## MECHANICAL GATE (blocks advance — run BEFORE commenting done)
```python
python3 - <<'EOF'
import re, sys
p = "campaigns/<name>/research.md"
text = open(p).read()
# Count verified claims (numbered bolded claim lines)
claims = re.findall(r'(?m)^\d+\.\s+\*\*', text)
# Count source URLs
urls = re.findall(r'https?://\S+', text)
# Count claims without a URL in the same block (within 3 lines)
unverified = 0
lines = text.splitlines()
for i, line in enumerate(lines):
    if re.match(r'^\d+\.\s+\*\*', line):
        block = ' '.join(lines[i:i+4])
        if not re.search(r'https?://', block):
            unverified += 1
print(f"claims={len(claims)}")
print(f"urls={len(urls)}")
print(f"claims_without_url={unverified}")
if len(claims) < 3:
    print("FAIL too few claims (<3)")
elif unverified > 0:
    print("FAIL claims without source URL")
else:
    print("PASS")
EOF
```
- FAIL → add sources for unverified claims or remove the claim. Do NOT advance
  with a claim that has no URL.

## SCORED REVIEW (1-10, min pass 7)
1. **Claim count** — 3–7 verified claims present
2. **Source density** — every consequential claim has a URL
3. **No fabrication** — no invented numbers, quotes, or sources
4. **Contradictions** — stated honestly (not smoothed over)
5. **Unknowns** — stated (what sources don't prove)
6. **Relevance** — evidence matches the opportunity score + route
7. **Mechanism depth** — explains the "why", not just the "what"

PASS: all ≥ 7. FAIL: feedback must name the claim + exact fix.

## DONE WHEN
`campaigns/<name>/research.md` exists, 3–7 claims each with a URL, gate PASSED
(no claim without source), contradictions + unknowns stated, and the kanban
comment reports claim count + source count + gate result.
