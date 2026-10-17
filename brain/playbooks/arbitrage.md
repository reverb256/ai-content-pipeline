# Arbitrage Playbook — Opportunity Oracle

> How the oracle finds where demand outruns supply, scores the opportunity,
> and routes production. The system does not assume a niche or platform — it
> scans for the biggest arbitrage and follows it.

## The Core Principle

Content arbitrage = existing demand + weak supply. The oracle finds places
where people are ALREADY searching/asking (demand) but few good answers exist
(supply gap). Then it routes the content machine there — niche, format,
platform, language, whatever wins.

```
demand signal (people asking/complaining/searching)
    + supply gap (no good, consistent, quality answers)
    + monetization (RPM / affiliate / product fit)
    + automation fit (can the machine produce it?)
    = opportunity score → route production
```

## Demand Signal Queries (x_search)

Run these per candidate topic/niche. High engagement on shallow posts = demand.

```
# Questions people are asking (headline gold)
("how do I" OR "why do I" OR "can someone explain" OR "does anyone know") "<topic>" lang:en -filter:links

# Explicit gaps ("I wish there was...")
("wish there was" OR "wish someone" OR "wish more content" OR "no one covers") "<topic>"

# Complaints / pain points (recurring = evergreen demand)
("frustrated with" OR "wish this worked" OR "tired of") "<topic>" min_faves:1

# What actually engages (proof of demand)
"<topic>" min_faves:200 -filter:replies since:<90d>
```

**Demand score signals:**
- High reply counts on shallow/unsatisfying posts → people care, supply is bad
- News cycles spiking interest (incidents, AI releases, regulations)
- Recurring questions with no canonical answer thread

## Supply Gap Queries (x_search)

```
# Are there good "best accounts" recommendation threads? (sparse = gap)
("best accounts for" OR "recommend accounts for" OR "good follows for" OR "who should I follow") "<topic>" min_faves:50

# Are there consistent high-engagement explainers?
"<topic>" ("explain" OR "breakdown" OR "thread") min_faves:100 -filter:replies

# Who owns the space? (dedicated consistent creators?)
from:<known-accounts> min_faves:50
```

**Supply gap signals:**
- "best accounts for X" searches return almost nothing → no one owns it
- Few dedicated, consistent, high-engagement creators in the exact framing
- Existing supply is news clips / sensational takes, not sourced explainers
- Fragmented specialists posting occasionally, not a go-to voice

## The Scoring Rubric

Score each opportunity 0-10 per dimension, multiply for the final:

| Dimension | How to score | Weight |
|-----------|-------------|--------|
| **Demand** | Question volume, engagement, news-cycle heat | 1.0 |
| **Supply gap** | Sparse quality supply, no dominant creator | 1.0 |
| **Monetization** | RPM (finance $12-25, tech $7-15, niche software $12-25), affiliate/product fit | 0.8 |
| **Automation fit** | Can the machine produce it? (screen-record/tutorial = high, original footage = low) | 0.8 |
| **Policy safety** | Original + educational + non-repetitive = high; slop-adjacent = low | 1.0 (gate) |
| **Platform fit** | X thread / YouTube long-form / Shorts / translation / blog — where does this win? | 0.5 |

**Final score = demand × gap × (monetization × automation × platform)** with
policy safety as a gate (score 0 if unsafe).

**Thresholds:**
- Score > 6: strong opportunity — create production card
- Score 4-6: monitor — add to watchlist, re-check weekly
- Score < 4: pass — do not waste production on it

## Routing Logic (what the oracle decides)

| Finding | Route |
|---------|-------|
| High demand, no supply, explainer-friendly | X threads first (fast) → YouTube long-form (compounding) |
| High RPM, screen-recording friendly | YouTube tutorials (niche software workflows $12-25) |
| Demand exists in another language, supply thin there | Translation arbitrage (auto-dub or translate winning content) |
| Short-form friendly, high virality | Shorts/Reels (subscriber acquisition) |
| Evergreen, search-driven | YouTube long-form + blog (SEO compounding) |

The oracle routes per-opportunity. It does NOT lock one format. Wherever the
biggest arbitrage is, the machine follows.

## Known Opportunity Clusters (from 2026 research, re-verify before producing)

1. **Aviation education / incident analysis** — high demand during incidents,
   near-zero quality supply (sourced, diagram-heavy, non-sensational threads)
2. **Applied psychology in the AI era** — endless evergreen demand, fragmented
   supply, no dominant explainer
3. **Practical longevity for normal people (35-55)** — high interest, scattered
   supply, avoid biohacker saturation
4. **Niche software workflows** — one tool per channel, $12-25 RPM, low
   competition ("how to build X in Y" with <50 watchable answers)
5. **Business case studies** — $9-18 RPM, medium competition, screen-recording
   friendly
6. **Translations** — auto-dubbing is a default growth lever; content that
   wins in English can win in other languages with thin supply
7. **Audio dramas / narrative stories with emotive TTS** — j_kro direction
   (2026-08-29). Reddit-story / audio-drama niches are battle-tested
   (RedditVideoMakerBot powers large channels). Highly emotive TTS
   (MiniMax TTS / Chatterbox) + simple visuals or pure audio. Monetizes via
   ad revenue + membership. Needs: emotive TTS provider research + a story
   source pipeline (Reddit prompts, classic fiction, original scripts).

## Weekly Oracle Run

The oracle runs daily (cron). Weekly it:
1. Re-checks the watchlist (score 4-6 items) for movement
2. Reviews the last 7 days of production performance (what arbitrage held up?)
3. Updates this playbook with what the data shows (keep/test/stop)

## Rules

1. **Never produce for a niche the oracle hasn't scored.** The oracle is the
   gate — no scored opportunity, no production card.
2. **Re-verify before producing.** A gap found last month may be filled now.
   The oracle re-runs its demand/supply queries before creating a card.
3. **Policy safety is a gate, not a score.** If content risks "inauthentic
   content" demonetization (template slop, mass-produced, repetitive), score 0.
4. **Route, don't lock.** The oracle routes per-opportunity across
   niche/format/platform/language. Today aviation threads, tomorrow translated
   software tutorials.
5. **The data closes the loop.** Production performance feeds back into the
   scoring (a niche that converts gets higher weights; one that flops drops).
