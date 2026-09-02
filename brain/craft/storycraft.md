# Craft — Storycraft (engineering reference v1, 2026-09-02)

> Narrative structure, story management, character design, and authorship
> quality. Follows `brain/QUALITY_DOCTRINE.md`: every claim here is a
> measurable check, not a vibe. Read alongside `brain/stage-specs/story.md`,
> `brain/stage-specs/script.md`, `brain/stage-specs/audio-drama.md`, and
> `brain/audio-workflow-context.md`.

## 1. Narrative Structures — Decision Table

Pick ONE structure. Do not mix. The choice is determined by format, length, and
platform — not preference.

| Structure | Beats | Best for | Length | Platform |
|-----------|-------|----------|--------|----------|
| **3-Act** | Setup / Confrontation / Resolution | General drama, explanations | 5–60 min | YouTube, podcast |
| **Hero's Journey** | Ordinary World → Call → Refusal → Mentor → Tests → Ordeal → Return | Transformation arcs, epics | 30 min–8 hr | Serialized audio, audiobook |
| **Save the Cat** (Snyder) | Opening Image → Catalyst → Debate → Break into 2 → B Story → Midpoint → All Is Lost → Finale | Commercial fiction, high-retention hooks | 8–25 min | YouTube story, short film |
| **Cold-Open + Payoff** | Hook (tension/reveal) → Context → Escalation → Resolution → Payoff callback | Short-form, retention-critical | 2–15 min | YouTube Shorts, TikTok, Reels |
| **Audio-Drama Loop** | Cast lock → Scene (one emotion) → [pause] → Scene → ... → Payoff → CTA | Voiced drama, episodic | 15 min–8 hr | Podcast, Spotify, YouTube audio |

**Rule:** Cold-open is MANDATORY for any content < 15 min. The first 7–15
seconds must state tension or payoff — no "welcome back," no channel intro,
no context-before-conflict.

## 2. Story Engine — Checkable Criteria

Every story must answer these six questions. "No" to any = incomplete premise.

| Engine Element | Question | Pass criteria (measurable) |
|----------------|----------|----------------------------|
| **Premise** | What is the one-sentence situation? | Can be stated in ≤ 25 words; contains character + conflict |
| **Protagonist want/need** | What do they pursue (want) vs. what would actually fix them (need)? | Want ≠ need; both are explicit in the script |
| **Conflict** | Who/what opposes the want? | Antagonist or obstacle has clear motivation (not "just evil") |
| **Stakes** | What happens if they fail? | Concrete loss stated early (life, relationship, truth, freedom) |
| **Escalation** | Does each scene raise cost or tension? | No scene is a repeat; each beat adds new information or raises risk |
| **Resolution** | Is the want/need answered AND the theme landed? | Ending is earned (not deus ex machina); callback to opening image |

**Anti-pattern:** A protagonist who reacts but never chooses. Passive MCs fail
the escalation check — if every scene happens TO them, rewrite until they make
a choice that raises stakes.

## 3. Scene Mechanics

### 3.1 Scene Goal + Late/Early Discipline

Every scene must have ONE of these goals:
1. **Reveal** — new information that changes the reader's understanding
2. **Escalate** — raise tension, cost, or stakes
3. **Decision** — protagonist makes a choice that constrains future choices

**Enter late, exit early:** Start the scene at the LAST possible moment
(minimum 2 beats before the goal triggers). End the scene the MOMENT the goal
is achieved — never after the emotional beat lands. Cutting room floor test:
delete the first and last paragraph of every scene; if the story still works,
they were fat.

### 3.2 Tension Arc Per Scene

```
      [goal]
       /\
      /  \        ← peak: revelation / decision / setback
     /    \
    /      \      ← exit: new status quo (not flat)
   /        \
  ENTER     EXIT
 (late)    (early)
```

Flat scenes (same tension start to end) FAIL. Minimum 0.3-point tension delta
per scene on a 0–3 scale.

### 3.3 Scene-to-Scene Causation

Transitions MUST be one of two types:

| Transition | Form | Use |
|------------|------|-----|
| **Therefore** | "X happened, **therefore** Y must happen" | Consequence, choice-driven |
| **But** | "X happened, **but** Y blocks it" | Obstacle, reversal |

**Forbidden:** "And then" — the sign of episodic, unlinked storytelling. If you
cannot name the therefore/but between scene N and N+1, the story has a plot
hole.

## 4. Character Design

### 4.1 Protagonist — Flaw + Arc

| Element | Check |
|---------|-------|
| **Want** | Concrete, achievable-seeking (a person, object, state) |
| **Need** | Unconscious truth they resist; the arc is accepting it |
| **Flaw** | The specific blindness that prevents them from getting the need |
| **Arc** | Start with flaw active → midpoint crack → All Is Lost flaw-fuels-crisis → resolution: flaw overcome or fatal |

**Arc test:** Can you state the protagonist's belief at scene 1 and the
opposite belief at the end? If not, there is no arc.

### 4.2 Antagonist as Obstacle

The antagonist is the protagonist's strongest teacher — they attack the flaw
directly. A weak antagonist is "in the way"; a strong antagonist makes the
protagonist's flaw the very tool of their defeat.

### 4.3 Supporting Cast — Function

Each supporting character must serve ONE primary function:
- **Mirror** — shows what the protagonist could become
- **Mentor** — gives the tool/knowledge the protagonist refuses to use
- **Shadow** — the dark mirror (already fell to the flaw)
- **Ally** — costs something for their loyalty (not free support)

Supporting cast > 5 in a short-form piece = bloat. Cut to the function and
merge.

### 4.4 Dialogue Voice — Per-Character Lock

Every named character gets a Voice Design block (see
`brain/audio-workflow-context.md`). Voice Design fields:
`gender, age, tone, emotion, pace` — e.g., *"woman in her late 30s, steady,
weary, quiet authority."*

**Voice lock rule:** Once cast block is written, NO ad-libbed speakers. If a
speaker appears in scenes but not cast, the script is INCOMPLETE. Dialogue
test: remove all attributions — can you still tell who speaks by word choice
and rhythm alone?

## 5. Pacing

### 5.1 Scene Length Targets by Format

| Format | Target scene length | Max words/scene |
|--------|---------------------|-----------------|
| YouTube script (8–15 min) | 60–120s | ~250 words |
| Audio drama Short (15–45 min) | 90–180s | ~300 words |
| Audio drama Long (1–2 hr) | 120–240s | ~400 words |
| Audio drama Epic (4–8 hr) | 180–300s | ~500 words |
| Hook (cold-open) | 7–15s | ≤ 25 words |

### 5.2 Revelation Timing

The first major reveal (the thing the audience didn't know) must land before
the 25% mark. The final reveal resolves the opening question. Midpoint reveal
(at 45–55%) reverses the protagonist's understanding — this is the "truth
was backwards" beat.

### 5.3 Show, Don't Tell — Concrete Rule

**Show** = the audience infers the emotion from action, dialogue, or sensory
detail. **Tell** = the narrator or character names the emotion directly.

Rule: For every emotion beat, write the PHYSICAL MANIFESTATION first. Only use
the emotion word ("she was angry") if the physical beat is ambiguous.

| Tell (weak) | Show (strong) |
|-------------|---------------|
| "He was terrified" | "His hand missed the keyhole twice" |
| "She felt betrayed" | "She read the message twice, then set the phone face-down" |
| "He was angry" | "He closed the door. Opened it. Closed it again, quiet." |

### 5.4 Plant / Payoff Discipline

Every object, line of dialogue, or skill shown in Act 1 must EITHER:
- Pay off in Act 3 (Chekhov's gun), OR
- Be a deliberate red herring (signposted by over-emphasis)

Untracked plants = loose threads = FAIL on the coherence check.

## 6. Authorship & Originality

### 6.1 Anti-Cliché Checklist

Reject a draft if any tell fires:

| Cliché | Tell |
|--------|------|
| "It was all a dream" / fake-out without foreshadowing | Audience feels cheated |
| Protagonist stares into mirror to describe themselves | Lazy exposition |
| "Little did they know..." | Telling, not showing |
| Villain monologuing their plan | Low-tension reveal |
| Coincidence saves the protagonist | Deus ex machina = FAIL on resolution |
| Opening with a character waking up | Cold-open violation |

### 6.2 Source Synthesis — Making It Fresh

The goal is not "original" in the vacuum sense — it is **specific + unexpected**.

1. Combine two unrelated domains (horror + infrastructure documentation)
2. Ground every abstraction in a sensory detail (the smell of ozone, the hum of a rack)
3. Replace generic nouns with the SPECIFIC noun (not "a car," a '98 Corolla with a cracked dash)

### 6.3 Voice / Tone Consistency

Define the house voice per campaign in `brain/voice.md`. Per-story tone must
be a SPECIFIC deviation from house voice, not an accident. Read the first
scene aloud — if it sounds like a different narrator than scene 10, the voice
drifted.

### 6.4 Authored vs. Generated — The Specificity Test

Generated prose uses **plausible generalities**. Authored prose uses
**unrepeatable specifics**. The test: could this sentence appear in someone
else's story about the same genre? If yes, it is generic. Replace with a
detail only THIS story could contain.

## 7. Narrative QA — 15-Point Review Rubric

Score 1–10 per item. Min pass = 7. FAIL if any item < 7.

| # | Criterion | What "10" looks like | What kills it |
|---|-----------|----------------------|---------------|
| 1 | **Hook strength** | Listener is pulled within 7s; tension or payoff stated | Channel intro, "today we'll talk about" |
| 2 | **Protagonist want/need clarity** | Both explicit; want ≠ need | Passive MC; want = need |
| 3 | **Conflict & antagonist motivation** | Opposition has clear, understandable reason | "Just evil"; no motivation |
| 4 | **Stakes** | Concrete loss stated early; escalates | Abstract stakes ("failure is not an option") |
| 5 | **Scene goal** | Every scene has ONE of reveal/escalate/decision | Meandering; scene exists for vibe |
| 6 | **Enter late / exit early** | No scene starts before the last possible moment | Warm-up paragraphs; denouement after the beat |
| 7 | **Therefore / But transitions** | Every scene link is causal or reversal | "And then" / episodic |
| 8 | **Tension arc per scene** | Every scene has a rise and fall | Flat scenes; same energy throughout |
| 9 | **Show vs. tell** | Emotions shown through action/sensory detail | "He was sad" without physical beat |
| 10 | **Plant / payoff** | Every setup has a resolution; no loose threads | Chekhov's gun unfired |
| 11 | **Character arc** | Protagonist belief changes from start to end | No arc; same worldview throughout |
| 12 | **Voice lock** | Every speaker is distinguishable by word choice alone | All characters sound identical |
| 13 | **Anti-cliché** | No dream sequences, mirror descriptions, monologues | Any item from §6.1 |
| 14 | **Specificity / originality** | Contains details no other story in the genre has | Generic nouns; interchangeable scenes |
| 15 | **Resolution earned** | Ending flows from character choice, not coincidence | Deus ex machina; unforeshadowed save |

**PASS:** all ≥ 7. **FAIL:** any < 7. Feedback must name the scene + exact fix.
Max 2 retries; then flag for human review.

## 8. Story Bibles — Continuity Across Episodes

Serialized content (audio dramas, episodic video) requires a **story bible**:
a single source of truth that makes continuity repeatable and declarative.

### 8.1 Bible Components

| File | Contents | Update trigger |
|------|----------|----------------|
| `bible/cast.md` | Character sheets: name, Voice Design, motivation, flaw, arc state, current status | Every episode that changes a character |
| `bible/timeline.md` | Canonical event sequence (in-universe dates, cause→effect) | Every episode |
| `bible/world.md` | World rules: what is possible, what is not, tech limits, magic systems, social rules | When a new rule is introduced |
| `bible/canon.md` | Log of every episode with key events + callbacks | Every episode (append-only) |
| `bible/plants.md` | Outstanding plants (unpaid setups) + target resolution episode | Every episode (remove when paid) |

### 8.2 Continuity Checks (Mechanical Gate)

Before every episode ships, run:
1. **Cast check:** Every speaker in new episode matches `bible/cast.md` Voice Design.
2. **Timeline check:** New events do not contradict `bible/timeline.md`.
3. **World check:** No event violates a rule in `bible/world.md`.
4. **Plant check:** If a plant from `bible/plants.md` was resolved, log the payoff.

### 8.3 Declarativeness Angle

The bible must be **declarative, not narrative** — structured as facts, not
prose. A new writer (or bot) should be able to read ONLY the bible and
produce episode N+1 without re-reading all prior episodes. If the bible
cannot replace prior reading, it is incomplete.

```
# Good (declarative)
- Mara: Voice Design = "woman late 30s, steady, weary"
- Mara's flaw: trusts systems over people
- World rule: AI cannot lie (but can omit)
- Timeline: Episode 3, Day 12 — Elias discovered in server room

# Bad (narrative)
"Mara had always been the steady one, trusting in systems even when..."
```

---

## Sources

- Field, S. (2005). *Save the Cat!* — beat sheet structure.
- Campbell, J. (1949). *The Hero with a Thousand Faces* — Hero's Journey.
- Snyder, B. (2018). *Save the Cat! Writes a Novel* — fiction application.
- video-factory (NesDevr) — word budgets, per-slot pacing, scored review gates.
- brain/audio-workflow-context.md — Voice Design, emotion vocabulary, duration spectrum.
- brain/stage-specs/story.md — story stage contract, cast block, emotive annotations.
- brain/stage-specs/script.md — script structure, visual beat pacing, anti-slideshow.
- brain/stage-specs/audio-drama.md — pacing, character consistency, scene pauses.
- brain/playbooks/audio-dramas.md — production loop, emotion annotations, policy.
