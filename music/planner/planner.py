#!/usr/bin/env python3
"""planner — brief -> a *constrained* song plan (option B).

WHY THIS EXISTS
---------------
Option A (the model's own planner, `RunningHub ACE-Step Artist`) is a black box
with its own priors. Measured on four probes, 2026-10-09: the specific subject
was ignored in 4 of 4, and one run violated a documented genre convention
(an anime opening planned at 70 BPM in 2/4 — anisong is 130-180 BPM in 4/4).
Two runs invented content wholesale (a "Middle Eastern or Balkan whistle" for a
rainstorm brief; Norwegian lyrics about mosques for a server-debugging brief
with language=en set).

This planner replaces the guess with OUR craft. It reads the researched
artifacts the pipeline already owns:

    music/genres.yaml                    genre -> template, visual, lanes
    music/prompts/<genre>.md             the style caption + section tag sheet
    music/lyrics/blueprints/<genre>.yaml structure, voice, rhyme, avoid list,
                                         bpm anchor, mood words

...then asks an LLM for the ONE thing that genuinely needs generating — the
lyrics and a caption — while CONSTRAINING it to those artifacts, and validates
the result against them before anything is rendered.

AUTHORSHIP — READ THIS BEFORE USING --lyrics-mode ai
----------------------------------------------------
The pipeline's copyright path depends on human-written lyrics. `music/lyrics/
lyrics.py` records a human-authorship claim with a sha256 of the lyric sheet,
and that claim is what makes a track registrable with SOCAN and acceptable to
distributors that screen for AI provenance. AI-written lyrics BREAK that claim.

So this planner defaults to `--lyrics-mode draft`: it produces a scaffold with
the blueprint's structure and per-section guidance, for a human to write into.
`--lyrics-mode ai` exists for lanes where the copyright claim is not the point
(volume catalogue, asset packs) and stamps the output so the difference can
never be lost.

`--lyrics-mode instrumental` is the third mode, for the genres whose own prompt
template says the lyrics box stays empty: chill-lounge, chiptune-8bit,
commentary-beds, elemental-air, elemental-earth, elemental-fire, elemental-water,
sentimental-piano (8 of the 14 templates, measured). Before it existed the queue
could not express such a track at all - `draft` produced a scaffold the renderer
refuses (exit 1, a `.refused` marker) and `ai` wrote words a track must not have,
which also voids the authorship claim. Both were wrong for the same reason: an
instrumental has no sung line for a human to author (card t_25a6499c D3).

An instrumental plan carries `"instrumental": true`, a section TAG sheet as
structure control (never singable text), and an authorship line that says
plainly there is no human-authored portion - so the difference cannot be lost
downstream. The renderer's draft refusal is untouched: it is the check that
stops a scaffold shipping as a track, and an instrumental is not a scaffold.

Output: a plan JSON. Feed it to a generator with `acestep_plan.py`.

Usage:
    python3 music/planner/planner.py plan --brief "..." --genre chill-lounge
    python3 music/planner/planner.py plan --brief "..." --genre anime-opening --lyrics-mode ai
    python3 music/planner/planner.py show --genre chill-lounge      # what it reads
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FATAL: PyYAML required", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
GENRES_YAML = REPO / "music" / "genres.yaml"
PROMPT_DIR = REPO / "music" / "prompts"
BLUEPRINT_DIR = REPO / "music" / "lyrics" / "blueprints"

# Default planner endpoint. Any OpenAI-compatible /chat/completions works.
# Default is the fleet's own PAIR router, which routes to the forge GPUs and so
# does NOT contend with the 3090 doing the rendering. Override with
# PLANNER_ENDPOINT / PLANNER_MODEL, or --endpoint / --model.
DEFAULT_ENDPOINT = os.environ.get("PLANNER_ENDPOINT", "http://127.0.0.1:1235/v1")
DEFAULT_MODEL = os.environ.get("PLANNER_MODEL", "forge-4060-0/bonsai2-27b-ptq1-forge0")

# A brief shorter than this carries no subject to honour; refuse rather than
# let the LLM fill the vacuum with priors (that is exactly what option A does).
MIN_BRIEF_WORDS = 5

# Duration guard rails. ACE-Step renders at 25 semantic tokens/second, so an
# absurd duration is a long generation, not a long song.
#
# MAX_DURATION_S was 420, which silently excluded the registry's own `loop-10min`
# video shape: 600 s. t_909069f0 measured the consequence - elemental-earth's
# documented entry is 220 whole bars at 88 BPM = 600.0 s, the planner refused it,
# and the shape could only be reached through the sunolocal API by hand. The
# ceiling is now the longest shape the registry actually names.
MIN_DURATION_S = 30
MAX_DURATION_S = 600


# ---------------------------------------------------------------------------
# the artifacts we read (data, not code — add a genre = add files)
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not GENRES_YAML.is_file():
        sys.exit(f"FATAL: genre registry not found: {GENRES_YAML}")
    with open(GENRES_YAML, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not data.get("genres"):
        sys.exit(f"FATAL: no genres in {GENRES_YAML}")
    return data


def load_template(genre: str) -> dict:
    """Parse music/prompts/<genre>.md -> {caption, structure[], craft[]}.

    The templates were authored for a human pasting into Suno's web form, so
    they are prose. We pull the two machine-useful pieces out: the fenced
    `text` block under "Style field" (the caption) and the section tag sheet
    under "Lyrics guidance" (the structure).
    """
    path = PROMPT_DIR / f"{genre}.md"
    if not path.is_file():
        return {"caption": "", "structure": [], "craft": [], "path": None}
    raw = path.read_text(encoding="utf-8")

    caption = ""
    m = re.search(r"##\s*Style field.*?```(?:text)?\n(.*?)```", raw, re.S | re.I)
    if m:
        caption = " ".join(m.group(1).split())

    # Section tags: [Intro], [Verse 1], ... in order of appearance.
    # NO dedup and NO length cap on purpose. In these forms the repetition IS
    # the structure (anisong is V1-PC-C-V2-PC-C-B-FINAL-C-O; collapsing the
    # second Pre-Chorus and Chorus loses the shape), and the genre's defining
    # tag is long: "[Final Chorus - KEY CHANGE UP ONE SEMITONE/TONE]".
    #
    # We also pair each tag with the parenthetical that follows it, because
    # that parenthetical is the per-section craft note a draft scaffold needs
    # ("2-4 lines. Tension climb - short lines, rising pitch..."). A scaffold
    # with bare tags tells a writer nothing.
    structure: list[str] = []
    detailed: list[dict] = []
    m = re.search(r"##\s*Lyrics guidance(.*?)(?:\n##\s|\Z)", raw, re.S | re.I)
    block = m.group(1) if m else raw
    lines = block.splitlines()
    for i, line in enumerate(lines):
        tm = re.match(r"^\[([^\]]{1,72})\]", line.strip())
        if not tm:
            continue
        tag = tm.group(1).strip()
        structure.append(tag)
        guidance_parts: list[str] = []
        for nxt in lines[i + 1:i + 9]:
            s = nxt.strip()
            if s.startswith("["):
                break
            if s.startswith("("):
                guidance_parts.append(s.lstrip("(").strip())
            elif guidance_parts and s:
                guidance_parts.append(s)
            elif guidance_parts:
                break
        guidance = " ".join(guidance_parts).rstrip(")").strip()
        guidance = " ".join(guidance.split())
        detailed.append({"tag": tag, "guidance": guidance})

    craft = [ln.strip("-* ").strip() for ln in raw.splitlines()
             if ln.strip().startswith(("-", "*")) and len(ln.strip()) > 12][:12]
    return {"caption": caption, "structure": structure, "detailed": detailed,
            "craft": craft, "path": str(path)}


def load_blueprint(genre: str) -> dict:
    """music/lyrics/blueprints/<genre>.yaml when it exists (3 of 15 genres do)."""
    path = BLUEPRINT_DIR / f"{genre}.yaml"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def bpm_in_caption(caption: str):
    """The BPM the genre's own caption states, e.g. "ragga jungle, 168 BPM".

    Every template in music/prompts/ states one. It is the researched tempo for
    the genre and the only tempo signal available for the 11 genres that have no
    blueprint yet - without it the draft path fell back to a flat 100, which is
    right for almost nothing: jungle-dnb came out at 100 against its own stated
    168, and anime-opening at 100 against its stated 160.
    """
    m = re.search(r"(\d{2,3})\s*BPM", caption or "", re.I)
    return int(m.group(1)) if m else None


def bpm_anchor_for(ctx: dict):
    """One resolution order, used by the draft path, the AI prompt and
    validation alike, so all three agree on what "the genre's tempo" means.

    Blueprint first: it is hand-researched and may deliberately differ from the
    caption (chill-lounge is 72 in the blueprint, 75 in the caption - the
    blueprint is the decision). Caption second. Nothing third: better to say we
    do not know than to invent a tempo and validate against it.
    """
    return ctx["blueprint"].get("bpm_anchor") or ctx.get("template_bpm")


# The key a caption states, and NOT the words that merely sound like one. This
# pattern is deliberately case-SENSITIVE on the note name: an uppercase pitch
# class followed by major|minor. elemental-water's caption says "a minor key
# with add9 color" AND ends ", C minor"; a case-insensitive version matches the
# lowercase "a minor" first and reports the WRONG key for the one genre whose
# caption names two. The uppercase form is the one these templates use when they
# mean a signature ("hall reverb, A minor,"), and the words that are not keys
# ("one key", "key lift", "key change", "key mechanism", "key-triggered",
# "minor key", "happy major key") carry no uppercase pitch class, so none match.
KEY_IN_CAPTION_RE = re.compile(
    r"\b([A-G](?:\s*(?:#|b|\u266f|\u266d|flat|sharp))?)\s*(Minor|Major|minor|major)\b")


def key_in_caption(caption: str):
    """The key signature the genre's own caption states, e.g. "A minor".

    The sibling of `bpm_in_caption`, and it exists for the same reason: the
    caption is the ONLY key claim backed by an artifact. Measured over the 14
    live templates (2026-10-16), exactly 3 state a key -
    elemental-water ("C minor"), epic-orchestral-boss ("150 BPM in C minor")
    and trance ("A minor") - and the other 11 state none at all. A genre that
    states no key must yield None, not a default: see `key_anchor_for`.
    """
    m = KEY_IN_CAPTION_RE.search(caption or "")
    if not m:
        return None
    return " ".join(f"{m.group(1)} {m.group(2)}".split())


def key_anchor_for(ctx: dict):
    """One resolution order for the plan's `key`, mirroring `bpm_anchor_for`.

    Blueprint first (`key_anchor`, else `key`): a genre may pin its key as a
    deliberate decision rather than a caption fact. Caption second. NOTHING
    third - and that is the point of this function.

    REGRESSION (card t_f65b0f4c, found while verifying the trance queue entry
    on card t_791b48f7). The draft and instrumental paths resolved the key as
    `args.key or "C minor"`. The scheduled CronJob passes no --key, so EVERY
    plan the pipeline ever produced claimed "C minor" regardless of genre: four
    live plans (chill-lounge 72, anime-ending 92, epic-orchestral-boss 150,
    trance 138) all said C minor, and for trance that contradicts the file's own
    caption ("hall reverb, A minor, extended club arrangement") and the queued
    brief ("Uplifting trance at 138 BPM in A minor"). A fabricated key is not a
    neutral default - it is a wrong answer that reads as a fact, and since card
    t_25a6499c D2 it is also carried to the engine as `keyscale`. `bpm` was
    fixed against the caption the same way; `key` was left behind.
    """
    bp = ctx["blueprint"]
    return bp.get("key_anchor") or bp.get("key") or ctx.get("template_key")


def is_instrumental_template(genre: str) -> bool:
    """True when the genre's own prompt template declares no vocals.

    THE TEMPLATE IS THE SPEC, and the markers below are the ones the 8
    instrumental templates actually use ("Leave the **lyrics box empty** — that
    is Suno's instrumental path"). The 6 vocal templates (activist, anime-ending,
    anime-opening, epic-orchestral-boss, jungle-dnb, trance) never say it.

    This mirrors `music/suno-gen.py:is_instrumental_template` on purpose: the
    CDP generate rail and this planner must agree on which genres are
    instrumental, or a genre can be queued as instrumental and generated as
    vocal. suno-gen.py is not in the CronJob payload (it needs the browser
    stack), so the predicate is duplicated rather than imported -
    `music/tests/test_planner.py` asserts the two agree over every genre, which
    is what keeps the copy honest.

    Only the "## Lyrics guidance" section is searched: a style caption may
    mention "no vocals" as an arrangement note without the genre being
    instrumental.
    """
    path = PROMPT_DIR / f"{genre}.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    m = re.search(r"##\s*Lyrics guidance(.*?)(?=\n##\s|\Z)", text, re.S | re.I)
    section = (m.group(1) if m else text).lower()
    markers = (
        "lyrics box empty",
        "leave the lyrics box empty",
        "suno's instrumental path",
        "that is suno's instrumental path",
    )
    return any(marker in section for marker in markers)


def instrumental_lyrics(ctx: dict) -> str:
    """The `lyrics` value for an instrumental plan: STRUCTURE, never words.

    Suno's instrumental path is an empty lyrics box, so nothing here is
    singable. What is kept is the template's section tag sheet, because the
    repeat count of the tags is the arrangement the genre asks for (a boss loop
    is a fixed seven-part cycle). Each tag is emitted with no body, which is what
    marks the plan as structure-only: the engine's own `translate.py` replaces a
    lyrics value of "[Instrumental]" with the canonical header, and
    `acestep_plan.py` recognises `instrumental: true` and does not refuse.
    """
    tmpl = ctx["template"]
    tags = [s.get("tag") if isinstance(s, dict) else str(s)
            for s in (ctx["blueprint"].get("structure") or [])] or tmpl["structure"]
    tags = [t for t in tags if t]
    if not tags:
        return "[Instrumental]\n"
    return "".join(f"[{t}]\n" for t in tags)


def context_for(genre: str) -> dict:
    reg = load_registry()
    if genre not in reg["genres"]:
        sys.exit(f"FATAL: genre '{genre}' not in genres.yaml. "
                 f"Known: {', '.join(sorted(reg['genres']))}")
    entry = reg["genres"][genre]
    tmpl = load_template(genre)
    bp = load_blueprint(genre)
    return {"genre": genre, "registry": entry, "template": tmpl, "blueprint": bp,
            "template_bpm": bpm_in_caption(tmpl.get("caption") or ""),
            "template_key": key_in_caption(tmpl.get("caption") or ""),
            "instrumental": is_instrumental_template(genre)}


# ---------------------------------------------------------------------------
# ad-hoc sound decomposition
# ---------------------------------------------------------------------------
# The registry is a curated shortcut, not a boundary. A user can describe any
# sound freely ("spooky halloween", "dark electro swing", "melancholic piano")
# and the planner decomposes it into NAMED ELEMENTS from the genre inventories,
# then composes a spec. The LLM picks elements; it does not invent them.

def load_element_index() -> dict:
    """Index every registered genre's parameters into a flat element library.

    The inventories in music-theory-for-fusion/references/genre-inventories.md
    are the research. This flattens them so a free-form sound description can
    be resolved against real, named elements instead of a closed registry.
    """
    reg = load_registry()
    elements = {}
    for gkey, gval in reg["genres"].items():
        if not isinstance(gval, dict):
            continue
        fam = gval.get("family") or ""
        entry = {
            "genre": gkey,
            "family": fam,
            "label": gval.get("label") or gkey.replace("-", " ").title(),
        }
        # pull the tempo from the template caption
        tmpl = load_template(gkey)
        bpm = bpm_in_caption(tmpl.get("caption") or "")
        if bpm:
            entry["bpm"] = bpm
        if tmpl.get("caption"):
            entry["caption"] = tmpl["caption"]
        if tmpl.get("craft"):
            entry["craft"] = tmpl["craft"]
        bp = load_blueprint(gkey)
        for field in ("structure", "voice_notes", "rhyme", "line_length",
                      "bpm_anchor", "key_anchor", "mood_words", "avoid", "theme"):
            if bp.get(field):
                entry[field] = bp[field]
        elements[gkey] = entry
    return elements


def decompose_sound(description: str, index: dict, endpoint: str, model: str) -> dict:
    """Map a free-form sound description to named elements from the index.

    The LLM is constrained: it can only pick element NAMES that exist in the
    index, and it must justify each pick with a one-line reason. It cannot
    invent a tempo, a mode, or an instrument that is not in the research.
    """
    # Build the element catalog the LLM chooses from
    catalog = []
    for gkey, e in index.items():
        row = {"genre": gkey, "label": e["label"]}
        if e.get("bpm"):
            row["bpm"] = e["bpm"]
        if e.get("caption"):
            row["caption"] = e["caption"][:120]
        if e.get("mood_words"):
            row["mood_words"] = e["mood_words"]
        if e.get("voice_notes"):
            row["voice_notes"] = e["voice_notes"]
        catalog.append(row)

    system = """You decompose a sound description into musical elements.
You output ONLY a JSON object. You may only reference element names that appear
in the CATALOG provided. Do not invent tempi, modes, or instruments that are
not listed. Each element pick must have a one-line reason.

JSON shape:
{
  "sound": "<the original description, normalized>",
  "elements": [
    {"name": "<element name from catalog>", "role": "<what it contributes>",
     "reason": "<why it fits the description>"}
  ],
  "bpm": <int or null>,
  "key": "<e.g. C minor>",
  "structure": ["<section tag>", ...],
  "mood_words": ["<word>", ...],
  "avoid": ["<thing to avoid>", ...],
  "voice_notes": "<vocal direction or null>",
  "caption": "<a style caption synthesized from the chosen elements>"
}"""

    lines = [f"DESCRIPTION: {description}", "", "CATALOG:"]
    for c in catalog:
        lines.append(f"  - {c['genre']}: {c['label']}")
        if c.get("bpm"):
            lines.append(f"      bpm={c['bpm']}")
        if c.get("caption"):
            lines.append(f"      caption: {c['caption']}")
        if c.get("mood_words"):
            lines.append(f"      mood: {c['mood_words']}")
        if c.get("voice_notes"):
            lines.append(f"      voice: {c['voice_notes']}")
    user = "\n".join(lines)

    raw = call_llm(system, user, endpoint, model, temperature=0.4, timeout=180)
    d = extract_json(raw)
    if not d.get("elements"):
        sys.exit(f"FATAL: sound decomposition returned no elements:\n{raw[:400]}")
    return d


def compose_spec(sound: dict, index: dict) -> dict:
    """Build a plan context from decomposed elements.

    This is the same shape context_for() returns, but assembled from free-form
    picks instead of a registry block. The draft path, the AI prompt and
    validation all work unchanged because the context shape is identical.
    """
    picks = sound.get("elements") or []
    if not picks:
        sys.exit("FATAL: no elements to compose from")

    # Merge the contributing genres' parameters
    caption_parts = []
    mood = []
    avoid = []
    voice = None
    bpm = sound.get("bpm")
    seen_genres = set()

    for pick in picks:
        gkey = pick.get("name")
        if gkey not in index:
            continue
        seen_genres.add(gkey)
        e = index[gkey]
        if e.get("caption"):
            caption_parts.append(e["caption"])
        if e.get("mood_words"):
            mood.extend(e["mood_words"])
        if e.get("avoid"):
            avoid.extend(e["avoid"])
        if not voice and e.get("voice_notes"):
            voice = e["voice_notes"]
        if not bpm and e.get("bpm"):
            bpm = e["bpm"]

    # Dedupe while preserving order
    seen = set()
    mood = [x for x in mood if not (x in seen or seen.add(x))]
    seen = set()
    avoid = [x for x in avoid if not (x in seen or seen.add(x))]

    caption = sound.get("caption") or " ".join(caption_parts)
    structure = sound.get("structure") or ["Intro", "Verse 1", "Chorus",
                                            "Verse 2", "Chorus", "Bridge",
                                            "Chorus", "Outro"]

    return {
        "genre": sound.get("sound") or "ad-hoc",
        "registry": {"label": sound.get("sound") or "ad-hoc",
                     "family": "ad-hoc",
                     "contributors": sorted(seen_genres)},
        "template": {"caption": caption, "structure": structure,
                     "craft": [], "path": None, "detailed": []},
        "blueprint": {"structure": [{"tag": t, "guidance": ""} for t in structure],
                      "voice_notes": voice, "mood_words": mood,
                      "avoid": avoid, "bpm_anchor": bpm},
        "template_bpm": bpm,
        "sound_elements": picks,
        # An ad-hoc sound is composed from registry elements, not from one
        # genre template, so there is no template to declare it instrumental.
        # The caller says so explicitly if it wants that.
        "instrumental": False,
    }


# ---------------------------------------------------------------------------
# the LLM call
# ---------------------------------------------------------------------------

def auth_headers(endpoint: str) -> dict:
    """Authorization for the planner endpoint, when it needs one.

    Local endpoints (the fleet's llama-swap routers) take none. A hosted
    OpenAI-compatible endpoint needs a bearer token; we take it from
    PLANNER_API_KEY, or fall back to NOUS_API_KEY in the Hermes env file, so
    the pipeline can reuse the credential the agent already runs on without
    copying a secret into a repo.
    """
    key = os.environ.get("PLANNER_API_KEY")
    if not key:
        for candidate in (Path.home() / ".hermes" / ".env",
                          REPO / ".env"):
            if not candidate.is_file():
                continue
            for line in candidate.read_text(encoding="utf-8").splitlines():
                if line.startswith("NOUS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
            if key:
                break
    host = endpoint.split("//", 1)[-1].split("/", 1)[0].split(":")[0]
    if key and host not in ("127.0.0.1", "localhost", "10.1.1.110"):
        return {"Authorization": f"Bearer {key}"}
    return {}


def call_llm(system: str, user: str, endpoint: str, model: str,
             temperature: float = 0.7, timeout: int = 300) -> str:
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": temperature,
        # Generous on purpose: the fleet's local planners (Bonsai 2) are
        # REASONING models. They emit `reasoning_content` before `content`, so a
        # small budget is spent entirely on the thinking and the answer comes
        # back empty with finish_reason="length" — which looks like a broken
        # endpoint rather than a starved one.
        "max_tokens": 8192,
    }
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **auth_headers(endpoint)},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"FATAL: planner endpoint {e.code}: {e.read().decode(errors='replace')[:400]}")
    except Exception as e:
        sys.exit(f"FATAL: planner endpoint unreachable ({endpoint}): {e}")
    try:
        msg = data["choices"][0]["message"]
    except (KeyError, IndexError):
        sys.exit(f"FATAL: unexpected planner response: {json.dumps(data)[:400]}")
    content = msg.get("content") or ""
    if not content.strip():
        fr = data["choices"][0].get("finish_reason")
        sys.exit(f"FATAL: planner returned empty content (finish_reason={fr}). "
                 f"A reasoning model needs a larger max_tokens; "
                 f"reasoning_content length was "
                 f"{len(msg.get('reasoning_content') or '')}.")
    return content


def extract_json(text: str) -> dict:
    """LLMs wrap JSON in prose or fences. Take the outermost object."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        sys.exit(f"FATAL: planner returned no JSON object:\n{text[:500]}")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        sys.exit(f"FATAL: planner JSON invalid ({e}):\n{m.group(0)[:500]}")


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a song planner. You output ONLY a JSON object.

You will be given a BRIEF (the subject the song must be about), a GENRE, a
STYLE CAPTION (already written by a researcher - do not replace it), a
SECTION STRUCTURE (fixed - use exactly these tags, in this order), and
optionally craft notes and an avoid-list.

Rules, in priority order:
1. The song MUST be about the BRIEF's subject. Name its concrete details.
   Never substitute a generic or seasonal scene (no winter, snow, holidays,
   or "city lights" unless the brief asks for them).
2. Use the SECTION STRUCTURE exactly: same tags, same order, same count.
3. EVERY section carries lyrics. No section may be left as a bare tag. An
   [Intro] or [Outro] may be short - two to four lines - but it must have
   lines; a bare tag renders as a vocal-shaped hole and reads as a model
   failure when it is a plan defect.
4. Obey every craft note and every item in the avoid-list.
5. Write in the requested LANGUAGE only. Never mix languages.
6. Respect bpm_anchor if given.

JSON shape (no other keys):
{
  "title": "<=64 chars",
  "caption": "the style caption, refined for these lyrics",
  "bpm": <int>,
  "key": "<e.g. C minor>",
  "duration": <int seconds>,
  "timesignature": "4",
  "language": "<ISO code>",
  "lyrics": "[Section]\\nline\\nline\\n\\n[Section]\\n..."
}"""


def build_user_prompt(brief: str, ctx: dict, language: str, title: str | None,
                      duration: int | None) -> str:
    tmpl, bp = ctx["template"], ctx["blueprint"]
    parts = [f"BRIEF: {brief}", f"GENRE: {ctx['genre']}"]
    if tmpl["caption"]:
        parts.append(f"STYLE CAPTION (keep its sound, refine its wording):\n{tmpl['caption']}")
    structure = [s.get("tag") if isinstance(s, dict) else str(s)
                 for s in (bp.get("structure") or [])] or tmpl["structure"]
    if structure:
        parts.append("SECTION STRUCTURE (exactly these tags, this order):\n"
                     + "\n".join(f"  [{t}]" for t in structure))
    if bp.get("theme"):
        parts.append(f"THEME (genre-level; the BRIEF outranks it): {bp['theme']}")
    if bp.get("voice_notes"):
        parts.append(f"VOICE: {bp['voice_notes']}")
    if bp.get("rhyme"):
        parts.append(f"RHYME: {bp['rhyme']}")
    if bp.get("line_length"):
        parts.append(f"LINE LENGTH: {bp['line_length']}")
    anchor = bpm_anchor_for(ctx)
    if anchor:
        src = "blueprint" if bp.get("bpm_anchor") else "the genre's own caption"
        parts.append(f"BPM ANCHOR: {anchor} (from {src})")
    if bp.get("mood_words"):
        parts.append(f"MOOD WORDS (use some): {', '.join(map(str, bp['mood_words']))}")
    if bp.get("avoid"):
        parts.append(f"AVOID (hard rule): {bp['avoid']}")
    if tmpl["craft"]:
        parts.append("CRAFT NOTES:\n" + "\n".join(f"  - {c}" for c in tmpl["craft"]))
    parts.append(f"LANGUAGE: {language}")
    if title:
        parts.append(f"TITLE: use exactly {title!r}")
    if duration:
        parts.append(f"DURATION: {duration} seconds")
    return "\n\n".join(parts)


def scaffold_lyrics(ctx: dict, brief: str) -> str:
    """--lyrics-mode draft: structure + per-section craft, for a human to write into."""
    bp, tmpl = ctx["blueprint"], ctx["template"]
    struct = (bp.get("structure")
              or tmpl.get("detailed")
              or [{"tag": t, "guidance": ""} for t in tmpl["structure"]])
    if not struct:
        struct = [{"tag": "Verse 1", "guidance": ""}, {"tag": "Chorus", "guidance": ""}]
    out = [f"# brief: {brief}",
           "# provenance: human-original — write every sung line yourself",
           "# craft notes below each tag come from the genre template; they are",
           "# guidance, not lyrics. Delete them as you fill each section.",
           ""]
    for entry in struct:
        tag = entry.get("tag") if isinstance(entry, dict) else str(entry)
        guide = (entry.get("guidance") or "") if isinstance(entry, dict) else ""
        out.append(f"[{tag}]")
        if guide:
            out.append(f"({guide})")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# validate the plan against the artifacts (do not ship a drifted plan)
# ---------------------------------------------------------------------------

def validate(plan: dict, ctx: dict, brief: str, language: str,
             instrumental: bool = False) -> list[str]:
    """Check a plan against the genre's own artifacts.

    `instrumental=True` relaxes exactly the checks that are about SUNG words:
    an instrumental plan has no lyrics and must not be asked for any. Every
    other check (structure, tempo, duration, avoid-list) still applies - the
    point of the mode is to express an instrumental, not to skip validation.
    """
    problems: list[str] = []
    bp, tmpl = ctx["blueprint"], ctx["template"]

    if not plan.get("lyrics", "").strip():
        if not instrumental:
            problems.append("no lyrics")

    # structure must match the blueprint/template exactly when one is known
    want = [s.get("tag") if isinstance(s, dict) else str(s)
            for s in (bp.get("structure") or [])] or tmpl["structure"]
    got = re.findall(r"^\[([^\]]+)\]", plan.get("lyrics", ""), re.M)
    if want and got != want:
        problems.append(f"structure mismatch: planner used {got}, "
                        f"blueprint requires {want}")

    # EVERY section must carry singable lines. A section tag with nothing under
    # it renders as a vocal-shaped hole: the generator sings nothing there and
    # the result reads as a model failure when it is a plan defect. Observed on
    # the first live anime-opening plan, which left [Intro] and [Outro] bare.
    #
    # NOTE the separator is `[ \t]*\n`, NOT `\s*\n`. `\s` matches newlines, so
    # `\s*\n` lets an empty section swallow the blank lines AND the next
    # section's tag, giving it the following section's lyrics and reporting it
    # as full. That is exactly how the first version of this check passed a
    # plan whose Intro was bare. Verified with a negative control that empties
    # one section and expects this list to be non-empty.
    #
    # An instrumental plan emits bare tags ON PURPOSE (they are structure
    # control, and there is nothing to sing), so this check is skipped there -
    # but only there.
    if not instrumental:
        blocks = re.findall(r"^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)",
                            plan.get("lyrics", ""), re.M | re.S)
        empty = [tag for tag, content in blocks
                 if not [ln for ln in content.splitlines()
                         if ln.strip() and not ln.strip().startswith(("#", "("))]]
        if empty:
            problems.append(f"section(s) with no lyrics: {', '.join(empty)}")

    # bpm anchor
    anchor = bpm_anchor_for(ctx)
    if anchor and isinstance(plan.get("bpm"), (int, float)):
        if abs(plan["bpm"] - anchor) > max(8, anchor * 0.12):
            problems.append(f"bpm {plan['bpm']} is more than 12% off the anchor {anchor}")

    # duration guard rails
    dur = plan.get("duration")
    if not isinstance(dur, (int, float)):
        problems.append(f"duration is not a number: {dur!r}")
    elif not (MIN_DURATION_S <= dur <= MAX_DURATION_S):
        problems.append(f"duration {dur}s outside {MIN_DURATION_S}-{MAX_DURATION_S}s")

    # language: the plan's own lyrics must not be dominated by another script
    if language.startswith("en"):
        cyr = len(re.findall(r"[\u0400-\u04FF]", plan.get("lyrics", "")))
        if cyr > 3:
            problems.append(f"{cyr} Cyrillic characters in an English plan")
        if re.search(r"\b(og|det er|ikke|som|begynte)\b", plan.get("lyrics", ""), re.I):
            problems.append("Scandinavian function words in an English plan")

    # avoid-list
    avoid = str(bp.get("avoid") or "")
    for quoted in re.findall(r"[\"'\u201c\u201d]([^\"'\u201c\u201d]{3,40})[\"'\u201c\u201d]", avoid):
        if quoted.lower() in plan.get("lyrics", "").lower():
            problems.append(f"avoid-list term present: {quoted!r}")

    # the brief's own words should surface somewhere (subject actually honoured)
    # Instrumental plans are exempt: their caption is the genre's researched
    # style caption and their lyrics are bare tags, so there is no text field
    # the subject could appear in. The subject is carried in the plan's _meta
    # brief and rendered as music, not as words.
    if not instrumental:
        subject = [w for w in re.findall(r"[a-z]{4,}", brief.lower())
                   if w not in {"about", "track", "song", "that", "with", "keeps", "them", "their"}]
        body = (plan.get("lyrics", "") + " " + str(plan.get("caption", ""))).lower()
        if subject and not any(w in body for w in subject[:8]):
            problems.append(f"brief subject absent — none of {subject[:6]} appear in the plan")

    return problems


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_show(args) -> int:
    ctx = context_for(args.genre)
    # show the EFFECTIVE structure — the blueprint's when it exists, else the
    # template's. That is what plan() and validate() both act on.
    bp_struct = [s.get("tag") if isinstance(s, dict) else str(s)
                 for s in (ctx["blueprint"].get("structure") or [])]
    print(json.dumps({
        "genre": ctx["genre"],
        "registry": ctx["registry"],
        "template_path": ctx["template"]["path"],
        "caption_chars": len(ctx["template"]["caption"]),
        "structure_source": "blueprint" if bp_struct else "template",
        "structure": bp_struct or ctx["template"]["structure"],
        "blueprint": bool(ctx["blueprint"]),
        "bpm_anchor": ctx["blueprint"].get("bpm_anchor"),
        "avoid": ctx["blueprint"].get("avoid"),
        # Whether this genre's own template declares no vocals — the value
        # `--lyrics-mode instrumental` is valid for.
        "instrumental": ctx["instrumental"],
    }, indent=2))
    return 0


def cmd_plan(args) -> int:
    if len(args.brief.split()) < MIN_BRIEF_WORDS:
        print(f"FAIL: brief is too short ({len(args.brief.split())} words). "
              f"A vague brief is exactly what lets a planner invent content.",
              file=sys.stderr)
        return 2

    # Ad-hoc path: if the genre is not in the registry, decompose it into
    # named elements from the genre inventories and compose a spec. The
    # registry is a curated shortcut, not a boundary.
    reg = load_registry()
    if args.genre not in reg["genres"]:
        if not args.endpoint:
            print("FAIL: ad-hoc genre requires --endpoint and --model "
                  "(the LLM decomposes the sound description).",
                  file=sys.stderr)
            return 2
        index = load_element_index()
        sound = decompose_sound(args.genre, index, args.endpoint, args.model)
        ctx = compose_spec(sound, index)
        print(f"ad-hoc sound: {ctx['genre']}")
        print(f"  contributors: {', '.join(ctx['registry']['contributors'])}")
        for el in sound.get("elements", []):
            print(f"  - {el['name']}: {el.get('reason','')}")
    else:
        ctx = context_for(args.genre)
    mode = args.lyrics_mode

    # A genre whose own template says the lyrics box stays empty. The mode and
    # the template must agree, and when they do not the template wins a refusal
    # rather than a quiet downgrade:
    #   * asking for `instrumental` on a vocal genre would strip that genre's
    #     defining element (epic-orchestral-boss is "Choir only — no solo
    #     lyrical singing"); its `[Instrumental]` line is one SECTION, not a
    #     declaration. Measured: its template has 0 instrumental markers.
    #   * planning an instrumental genre as `draft` still produces a scaffold the
    #     renderer refuses, and as `ai` it writes words the genre must not have.
    #     That is not fatal here — a scaffold is a legitimate request for a human
    #     to write into — but it is warned about loudly.
    if mode == "instrumental" and not ctx["instrumental"]:
        print(f"FAIL: --lyrics-mode instrumental refused: '{ctx['genre']}' is not an "
              f"instrumental genre. Its template ({ctx['template']['path']}) does not "
              f"declare an empty lyrics box, so an instrumental render would drop "
              f"the element that defines the genre.", file=sys.stderr)
        return 2
    if mode != "instrumental" and ctx["instrumental"]:
        print(f"WARNING: '{ctx['genre']}' is an instrumental genre (its template says "
              f"the lyrics box stays empty) but --lyrics-mode {mode} was requested. "
              f"A draft plan is refused by the renderer; AI lyrics void the "
              f"authorship claim and are out of genre. Use --lyrics-mode instrumental.",
              file=sys.stderr)

    if mode == "instrumental":
        plan = {
            "title": args.title or (ctx["blueprint"].get("title_candidates") or ["Untitled"])[0],
            "caption": ctx["template"]["caption"],
            "bpm": args.bpm or bpm_anchor_for(ctx) or 100,
            # NOT `or "C minor"` (card t_f65b0f4c). The key is whatever an
            # artifact states - an explicit request, the blueprint's key_anchor,
            # else the genre's own caption - and null when none of them does.
            "key": args.keyscale or args.key or key_anchor_for(ctx),
            "duration": args.duration or 180,
            "timesignature": "4",
            "language": args.language,
            "lyrics": instrumental_lyrics(ctx),
            "instrumental": True,
            # NOT a human-authorship claim: there is no human-authored portion in
            # an instrumental rendered from a caption. See
            # music/docs/pro-registration.md §1/§3 — an AI-Generated Output is not
            # registrable with a PRO, and this line is what keeps that visible.
            "authorship": ("instrumental — no human-authored portion "
                           "(AI-Generated Output; not registrable with a PRO)"),
        }
        problems = validate(plan, ctx, args.brief, args.language, instrumental=True)
    elif mode == "draft":
        plan = {
            "title": args.title or (ctx["blueprint"].get("title_candidates") or ["Untitled"])[0],
            "caption": ctx["template"]["caption"],
            "bpm": args.bpm or bpm_anchor_for(ctx) or 100,
            # NOT `or "C minor"` (card t_f65b0f4c) - see key_anchor_for().
            "key": args.keyscale or args.key or key_anchor_for(ctx),
            "duration": args.duration or 180,
            "timesignature": "4",
            "language": args.language,
            "lyrics": scaffold_lyrics(ctx, args.brief),
            "instrumental": False,
            "authorship": "human-original (scaffold — write every sung line)",
        }
        problems = []  # a scaffold is not meant to pass content validation
    else:
        user = build_user_prompt(args.brief, ctx, args.language, args.title, args.duration)
        raw = call_llm(SYSTEM_PROMPT, user, args.endpoint, args.model,
                       temperature=args.temperature)
        plan = extract_json(raw)
        # An explicit request outranks the model's choice for the three fields a
        # caller may pin (tempo, key, length) — the same precedence the engine
        # applies to an explicit bpm.
        if args.bpm:
            plan["bpm"] = args.bpm
        if args.keyscale or args.key:
            plan["key"] = args.keyscale or args.key
        elif not plan.get("key"):
            # In `ai` mode the model writes the caption it keys against, so the
            # key it emits is its own claim about its own artifact - keep it.
            # Only a model that omitted the field falls back, and then to an
            # artifact (blueprint or caption), never to a default. An explicit
            # request already won above. Card t_f65b0f4c.
            plan["key"] = key_anchor_for(ctx)
        if args.duration:
            plan["duration"] = args.duration
        plan["instrumental"] = False
        plan["authorship"] = "AI-GENERATED (not eligible for a human-authorship claim)"
        problems = validate(plan, ctx, args.brief, args.language)

    plan["_meta"] = {
        "brief": args.brief,
        "genre": ctx["genre"],
        "lyrics_mode": mode,
        "instrumental": bool(plan.get("instrumental")),
        "planner_endpoint": args.endpoint if mode == "ai" else None,
        "planner_model": args.model if mode == "ai" else None,
        "template": ctx["template"]["path"],
        "blueprint": bool(ctx["blueprint"]),
    }

    out = Path(args.out) if args.out else (
        REPO / "music" / "plans" / f"{ctx['genre']}-{re.sub(r'[^a-z0-9]+', '-', args.brief.lower())[:40].strip('-')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"plan     : {out}")
    print(f"genre    : {ctx['genre']}   lyrics_mode: {mode}")
    if plan.get("instrumental"):
        print(f"mode     : INSTRUMENTAL — no lyrics; the template declares an empty "
              f"lyrics box. The renderer's draft refusal does not apply.")
    print(f"structure: {' -> '.join(re.findall(r'^\[([^]]+)\]', plan['lyrics'], re.M))}")
    print(f"bpm/key  : {plan.get('bpm')} BPM · {plan.get('key') or 'key=unknown'} · {plan.get('timesignature')}/4")
    print(f"duration : {plan.get('duration')}s   language: {plan.get('language')}")
    if problems:
        print(f"\nVALIDATION FAILED ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nvalidation: PASS")
    if mode == "draft":
        print("next: write the lyrics into the plan, then run acestep_plan.py")
    elif mode == "instrumental":
        print("next: run acestep_plan.py on the plan — no human step is needed")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="brief -> constrained song plan")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("show", help="what the planner reads for a genre")
    ps.add_argument("--genre", required=True)

    pp = sub.add_parser("plan", help="produce a plan")
    pp.add_argument("--brief", required=True)
    pp.add_argument("--genre", required=True)
    pp.add_argument("--lyrics-mode", choices=["draft", "ai", "instrumental"], default="draft",
                    help="draft = scaffold for a human (preserves copyright claim); "
                         "ai = LLM writes them (breaks the claim, stamped); "
                         "instrumental = no lyrics at all, for the 8 genres whose "
                         "template says the lyrics box stays empty (valid only for those)")
    pp.add_argument("--language", default="en")
    pp.add_argument("--title", default=None)
    pp.add_argument("--key", default=None,
                    help="explicit key signature for the plan (e.g. 'D Phrygian'); "
                         "wins over everything. Without it the blueprint's "
                         "key_anchor is used, else the key the genre's own caption "
                         "states, else null - never a default (card t_f65b0f4c)")
    pp.add_argument("--keyscale", default=None,
                    help="same as --key; the name the queue schema and the engine use")
    pp.add_argument("--bpm", type=int, default=None,
                    help="explicit tempo for the plan; wins over the genre's anchor. "
                         "Without it the anchor is used (blueprint, else the caption)")
    pp.add_argument("--duration", type=int, default=None)
    pp.add_argument("--out", default=None)
    pp.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    pp.add_argument("--model", default=DEFAULT_MODEL)
    pp.add_argument("--temperature", type=float, default=0.7)

    args = ap.parse_args(argv)
    return cmd_show(args) if args.cmd == "show" else cmd_plan(args)


if __name__ == "__main__":
    sys.exit(main())
