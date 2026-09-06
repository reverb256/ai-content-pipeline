# Media Literacy — Engineering Reference (2026-09-02)

> Applies the QUALITY_DOCTRINE standard: every check below is a scored criterion,
> not a vibe. Review stage scores each item 1-10; min pass = 7. Media literacy
> is the lens that catches what mechanical gates cannot: dishonest framing,
> manipulative hooks, and narrative bias that survives fact-checking.

## 1. Audience Cognition — Mapped to Editing Decisions

Viewers do not "watch." They predict, recognize patterns, and bail when
prediction is too easy or too costly.

| Cognitive phenomenon | What the viewer does | The editing rule |
|---|---|---|
| **3–5s hook window** | Decides whether the rest is worth the cost of attention | First frame must pose a question or show tension. No logo, no "hey guys." |
| **Pattern recognition** | Matches the clip against known templates (stock footage, AI voice, generic cuts) | Break the pattern every 60–90s. If the visual could appear in 100 other videos, cut it. |
| **Cognitive load** | Drops off when narration + visual + text compete for the same channel | One idea per beat. Narration explains what the eye cannot; visual shows what words cannot. No redundancy. |
| **Expectation vs. surprise** | Stays for the gap between what they predict and what arrives | Script the "expected" answer, then violate it with evidence. Surprise = retention. |
| **Emotional tagging** | Remembers how the video made them feel more than what it said | Every scene carries one emotion directive (see `brain/stage-specs/story.md`). Flat affect = forgotten content. |

**Concrete check (review gate):**
- Does the first 5 seconds contain a tension, question, or unexpected claim?
- Count pattern interrupts: ≥1 per 60–90s. Fewer = passive viewing = drop-off.
- Is any visual redundant with the narration? If yes, cut one or the other.

**Source:** Retention data (QUALITY_DOCTRINE §2), video-factory pacing rules, Sweller cognitive load theory.

## 2. Information Literacy — Research Stage

Research feeds every downstream claim. The spec in
`brain/stage-specs/research.md` defines the mechanical gate. This section adds
the media-literacy lens: **not all sources are equal, and not all numbers mean
what they appear to mean.**

### Source quality tiers

| Tier | Source type | Trust level | Use case |
|---|---|---|---|
| **T1 — Primary** | Official data, original study, primary document, direct observation | Verifiable, citable | Consequential claims, stats, quotes |
| **T2 — Secondary** | Reputable reporting on primary sources, expert analysis | Contextual, requires T1 trace | Background, framing, corroboration |
| **T3 — Tertiary** | Aggregators, listicles, AI summaries, social media one-liners | Lead-generating only | Finding T1/T2 leads. Never citable alone. |
| **T4 — Unverifiable** | Anonymous posts, deleted content, "studies show" with no link | Unusable | Flag as unknown, do not claim |

### Authority signals (and their failure modes)

- **Failure mode:** Expert in field A speaking on field B. (Nobel economist ≠ nutrition authority.)
- **Failure mode:** High follower count ≠ accuracy. Engagement rewards outrage.
- **Failure mode:** Recency bias. A 2020 paper may be obsolete; a 1995 paper may be foundational. Check the field's half-life.

### Verification workflow (concrete)

1. **Trace the stat to its origin.** "80% of X" — find the study. Read the sample, methodology, and date. A stat without a methodology is a rumor.
2. **Triangulate.** One source = claim. Two independent sources = corroborated. Three = reliable.
3. **Check the denominator.** "50% increase" from 2 to 3 is not the same as 50% of 1,000,000. Denominators reveal magnitude.
4. **Label inference explicitly.** "This suggests…" is not "This proves…". QUALITY_DOCTRINE requires the distinction.

### Fabricated-stat detection

| Tell | Action |
|---|---|
| Round numbers with no methodology ("studies show 73%…") | Flag: demand the study. |
| Stats that are always "many" or "most" without a number | Flag: unverifiable. |
| A single source making a dramatic claim that no other outlet repeats | Flag: likely cherry-picked or misread. |
| A stat that has been debunked but recirculates | Check Snopes, Retraction Watch, or the original retraction. |

**Source:** APA guidelines on source evaluation, CRAAP test (Currency, Relevance, Authority, Accuracy, Purpose), research.md §Source quality.

## 3. Visual Literacy — What the Viewer Decodes

Viewers are not media scholars, but they recognize inauthenticity at a gut
level. Trust breaks at specific markers.

| Marker | What reads as "fake/stock/AI" | The rule |
|---|---|---|
| **Generic stock footage** | Identical clip in competitor videos, watermark haze, mismatched lighting | Use original footage or properly licensed assets. If the clip could be in a template, don't. |
| **AI-video uncanny valley** | Too-smooth motion, inconsistent lighting, morphing backgrounds, no breath in human subjects | Disclose AI generation. Reviewer flags any clip that triggers "something is off" — it will for the audience too. |
| **Mismatched B-roll** | Narration about servers, visual of a coffee cup | Every visual beat must illustrate or complicate the narration. Mismatch = cognitive friction. |
| **Over-produced polish** | Perfect lighting, no ambient noise, no human imperfection | Imperfection signals authenticity. Faceless ≠ soulless. |

**Concrete check (review gate):**
- Does any visual beat break immersion? If a viewer would think "that looks AI-generated," it fails.
- Is every B-roll choice motivated by the narration? Random footage is a trust leak.

**Source:** QUALITY_DOCTRINE §2 (uniformity is the demonetization risk), YouTube inauthentic-content policy.

## 4. Persuasion Ethics — Manipulation vs. Clarity

Persuasion is not the enemy. Deception is. The line: **does the viewer get what
they were promised, and can they verify the promise?**

| Technique | Ethical use | Unethical use |
|---|---|---|
| **Hook** | Promises a question that the content answers | Promises a claim the content does not deliver (clickbait) |
| **Thumbnail** | Reflects a genuine moment or tension from the content | Uses a face/emotion/scene not in the video to drive clicks |
| **Urgency** | Real deadline or time-sensitive insight | "This will be banned tomorrow" (false scarcity) |
| **Emotional appeal** | Connects the evidence to a real human outcome | Manufactures outrage or fear disconnected from the evidence |
| **AI disclosure** | Clear labeling of AI-generated content, especially human subjects | Hiding AI generation to make content appear authentic |

### Thumbnail honesty rule (concrete)

The reviewer asks: **"If a viewer watches the full video and then sees the thumbnail, do they feel misled?"** If yes, the thumbnail fails — regardless of CTR.

**Concrete check (review gate):**
- Does the thumbnail promise a specific outcome, emotion, or claim?
- Is that outcome delivered within the first 30 seconds?
- Would a viewer who clicked on the thumbnail feel satisfied or deceived?

**Source:** FTC endorsement guidelines, YouTube thumbnail policy, persuasion ethics (Cialdini, influence vs. manipulation).

## 5. Narrative Bias Literacy — Avoiding Misleading Stories

A script can be factually accurate and still misleading. Bias hides in what is
**selected, framed, and omitted**.

| Bias type | How it appears in our content | The countermeasure |
|---|---|---|
| **Selection bias** | Cherry-picking case studies that support the thesis | Include the strongest counterexample. If you can't refute it, the thesis is weaker than you claim. |
| **Survivorship bias** | "All 5 founders I interviewed succeeded" — what about the 50 who didn't? | State the selection criteria. Report the denominator. |
| **Framing bias** | Presenting a stat as "95% success" instead of "5% failure" | Frame both ways. Let the viewer choose. |
| **Anchoring** | Opening with a large number to make the rest seem small | Lead with context, not just the dramatic figure. |
| **Narrative fallacy** | Imposing a clean story on messy reality | Acknowledge the mess. "It's complicated" is honest; "here's the simple answer" is usually a lie. |

**Concrete check (review gate):**
- Does the script include at least one counterexample or limitation?
- Are case studies representative, or are they the winners who confirm the thesis?
- Is there a statistic that would tell a different story if framed inversely?

**Source:** Taleb (survivorship bias, narrative fallacy), Kahneman (framing), selection bias in research methodology.

## 6. Media-Literacy QA — Review Stage Checklist

The reviewer scores each item 1–10. **Min pass = 7.** Any item scoring < 7 is a
FAIL with a specific fix.

| # | Criterion | Question | Pass threshold |
|---|---|---|---|
| 1 | **Honesty** | Is the content honest about what it knows and what it doesn't? | No overclaimed certainty; unknowns stated. |
| 2 | **Hook integrity** | Does the hook promise something the content delivers? | The promise is fulfilled within 30s. |
| 3 | **Number context** | Are statistics in context (denominator, date, methodology)? | Every stat has a source and a denominator. |
| 4 | **Shock value audit** | Is a "shocking" stat actually meaningful, or just cherry-picked? | Meaning survives removing the emotional language. |
| 5 | **Expert objection** | Would a domain expert object to the framing or claim? | No obvious expert objection; if yes, flag. |
| 6 | **Visual trust** | Does any visual break the viewer's trust in authenticity? | No stock-feeling, mismatched, or undisclosed AI footage. |
| 7 | **Bias check** | Is there selection, survivorship, or framing bias in the narrative? | Counterexamples included or bias acknowledged. |
| 8 | **AI disclosure** | Is AI-generated content clearly labeled? | Every AI asset disclosed. |
| 9 | **Platform-native quality** | Does the content meet the quality bar of the target platform? | See §7 below. |
| 10 | **Overall trust** | After consuming this content, does the viewer trust us more or less? | The content earns trust; it does not extract it. |

**Mechanical gate for QA:**
- Every item must have a score. No score = incomplete review.
- Any item < 7 = FAIL, with the exact section named and the exact fix specified.
- Two consecutive FAILs = escalate to human (QUALITY_DOCTRINE default).

## 7. Platform Literacy — What "Good" Looks Like Per Platform

Each platform shapes attention differently. "Good" is not the same everywhere.

| Platform | Attention shape | Quality bar | Slop signal |
|---|---|---|---|
| **YouTube** | Long-form, search-driven, retention-gated | 50%+ retention at 30s; hook in first 7s; pattern interrupt every 60–90s; AVD 50%+ for algorithm boost | Flat narration, stock footage recycling, no chapter breaks, thumbnail-title disconnect |
| **X (Twitter)** | Thread-driven, authority-gated, scannable | One insight per tweet; sources in replies or linked; thread has a payoff | Threads that bury the lede, engagement bait, unverified claims as headlines |
| **TikTok** | Short-form, pattern-driven, loopable | Hook in first 1–2s; loop structure; native pacing; text-on-screen | Repurposed YouTube content, low-res exports, no pattern interrupt, stock watermarks |
| **Substack/Newsletter** | Depth-driven, subscription-gated | Original reporting or novel synthesis; actionable takeaway; honest about uncertainty | AI-summarized news, no original sourcing, surface-level takes |

**Concrete check (review gate):**
- Is the content native to the target platform, or is it repurposed from another format?
- Does the pacing match the platform's attention curve? (YouTube: 60–90s interrupts; TikTok: 1–2s hooks.)
- If the same content ships on multiple platforms, is each version adapted — or is it the same file re-uploaded?

**Source:** Platform-specific retention data (QUALITY_DOCTRINE §2), YouTube Creator Academy, X best practices.

## 8. Cross-References

- `brain/QUALITY_DOCTRINE.md` — the meticulous standard (read first).
- `brain/stage-specs/research.md` — evidence package contract.
- `brain/stage-specs/review.md` — review stage contract (where this QA runs).
- `brain/stage-specs/story.md` — emotive scripting and narrative arc.
- `brain/proof.md` — evidence standards.
- `brain/playbooks/hooks.md` — hook taxonomy.
- `brain/playbooks/platforms.md` — platform playbooks.
- `brain/voice.md` — tone and stance.
