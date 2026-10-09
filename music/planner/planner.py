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
MIN_DURATION_S = 30
MAX_DURATION_S = 420


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


def context_for(genre: str) -> dict:
    reg = load_registry()
    if genre not in reg["genres"]:
        sys.exit(f"FATAL: genre '{genre}' not in genres.yaml. "
                 f"Known: {', '.join(sorted(reg['genres']))}")
    entry = reg["genres"][genre]
    tmpl = load_template(genre)
    bp = load_blueprint(genre)
    return {"genre": genre, "registry": entry, "template": tmpl, "blueprint": bp}


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
    if bp.get("bpm_anchor"):
        parts.append(f"BPM ANCHOR: {bp['bpm_anchor']}")
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

def validate(plan: dict, ctx: dict, brief: str, language: str) -> list[str]:
    problems: list[str] = []
    bp, tmpl = ctx["blueprint"], ctx["template"]

    if not plan.get("lyrics", "").strip():
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
    blocks = re.findall(r"^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)",
                        plan.get("lyrics", ""), re.M | re.S)
    empty = [tag for tag, content in blocks
             if not [ln for ln in content.splitlines()
                     if ln.strip() and not ln.strip().startswith(("#", "("))]]
    if empty:
        problems.append(f"section(s) with no lyrics: {', '.join(empty)}")

    # bpm anchor
    anchor = bp.get("bpm_anchor")
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
    }, indent=2))
    return 0


def cmd_plan(args) -> int:
    if len(args.brief.split()) < MIN_BRIEF_WORDS:
        print(f"FAIL: brief is too short ({len(args.brief.split())} words). "
              f"A vague brief is exactly what lets a planner invent content.",
              file=sys.stderr)
        return 2

    ctx = context_for(args.genre)
    mode = args.lyrics_mode

    if mode == "draft":
        plan = {
            "title": args.title or (ctx["blueprint"].get("title_candidates") or ["Untitled"])[0],
            "caption": ctx["template"]["caption"],
            "bpm": ctx["blueprint"].get("bpm_anchor") or 100,
            "key": args.key or "C minor",
            "duration": args.duration or 180,
            "timesignature": "4",
            "language": args.language,
            "lyrics": scaffold_lyrics(ctx, args.brief),
            "authorship": "human-original (scaffold — write every sung line)",
        }
        problems = []  # a scaffold is not meant to pass content validation
    else:
        user = build_user_prompt(args.brief, ctx, args.language, args.title, args.duration)
        raw = call_llm(SYSTEM_PROMPT, user, args.endpoint, args.model,
                       temperature=args.temperature)
        plan = extract_json(raw)
        plan["authorship"] = "AI-GENERATED (not eligible for a human-authorship claim)"
        problems = validate(plan, ctx, args.brief, args.language)

    plan["_meta"] = {
        "brief": args.brief,
        "genre": ctx["genre"],
        "lyrics_mode": mode,
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
    print(f"structure: {' -> '.join(re.findall(r'^\[([^]]+)\]', plan['lyrics'], re.M))}")
    print(f"bpm/key  : {plan.get('bpm')} BPM · {plan.get('key')} · {plan.get('timesignature')}/4")
    print(f"duration : {plan.get('duration')}s   language: {plan.get('language')}")
    if problems:
        print(f"\nVALIDATION FAILED ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nvalidation: PASS")
    if mode == "draft":
        print("next: write the lyrics into the plan, then run acestep_plan.py")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="brief -> constrained song plan")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("show", help="what the planner reads for a genre")
    ps.add_argument("--genre", required=True)

    pp = sub.add_parser("plan", help="produce a plan")
    pp.add_argument("--brief", required=True)
    pp.add_argument("--genre", required=True)
    pp.add_argument("--lyrics-mode", choices=["draft", "ai"], default="draft",
                    help="draft = scaffold for a human (preserves copyright claim); "
                         "ai = LLM writes them (breaks the claim, stamped)")
    pp.add_argument("--language", default="en")
    pp.add_argument("--title", default=None)
    pp.add_argument("--key", default=None)
    pp.add_argument("--duration", type=int, default=None)
    pp.add_argument("--out", default=None)
    pp.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    pp.add_argument("--model", default=DEFAULT_MODEL)
    pp.add_argument("--temperature", type=float, default=0.7)

    args = ap.parse_args(argv)
    return cmd_show(args) if args.cmd == "show" else cmd_plan(args)


if __name__ == "__main__":
    sys.exit(main())
