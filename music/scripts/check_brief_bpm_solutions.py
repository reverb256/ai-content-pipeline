#!/usr/bin/env python3
"""check_brief_bpm_solutions — recompute the BPM a brief's `styleWeight` claim actually buys.

WHY THIS EXISTS
---------------
This lane cannot request a tempo: `POST /api/v1/generate` has no `bpm` field (17
properties, measured from the live `openapi.json`), so `sunolocal/translate.py`
derives one:

    bpm = 120                                  # default
    if req.style_weight is not None:
        bpm = int(60 + req.style_weight * 120)  # the style dial used as a tempo control
    bpm = max(30, min(240, bpm))

`int()` TRUNCATES. So the 4-decimal value a brief derives by algebra —
`styleWeight = (anchor - 60) / 120` — lands on the *previous* BPM whenever the
product falls a hair short of the next integer. Every brief that carries such a
value has to be recomputed against the truncation, and nothing did that.

INCIDENT (2026-10-16, card t_55e37b88, recorded by the duplicate t_c92f566d)
---------------------------------------------------------------------------
`music/briefs/elemental-earth.md` states, in three places (§5, §7a, §10, and the
child card `t_909069f0` carries it too):

    styleWeight = (88-60)/120 = 0.2333   -> "buys 88 BPM"

Executed against the DEPLOYED module inside pod `sunolocal-source-65fcc845d-fd5r6`
(2026-10-16, image `localhost/sunolocal:v0.1.2`):

    0.2333   -> int(60 + 27.996)  = 87   (1 BPM short of the anchor)
    0.23334  -> int(60 + 28.0008) = 88
    0.2334   -> int(60 + 28.008)  = 88

The genre anchor is 88 BPM (`prompts/elemental-earth.md`), so the quoted value
renders the genre one BPM flat — and 0.2667 in the sibling elemental-air brief is
correct only by luck (0.2667*120 = 32.0040, which clears the truncation).

WHAT IT DOES
------------
For every `music/briefs/**/*.md`:

 1. genre = the brief's own path (`briefs/<genre>.md` or `briefs/<genre>/<slug>/brief.md`);
 2. anchor = the first `NNN BPM` inside that genre's template's first ```` ```text ````
    block (`music/prompts/<genre>.md`) — the caption the engine is actually given;
 3. a LINE is a claim when it names `styleWeight`/`style_weight` AND carries either
      * a `NNN BPM` literal, or
      * the solve form `(NNN - 60)/120`;
 4. the weight is the last float in (0,1) on the line, after the token;
 5. the claim passes when `int(60 + w*120)` equals the BPM named on the line.

Exit codes: 0 = every claim recomputes, 1 = at least one does not, 2 = usage error.

This deliberately does NOT check every `style_weight` in a brief: a brief may quote
the template's own Style Influence as a counter-example (elemental-fire quotes
`style_weight = 0.80 -> 156 BPM` as the defect it is), and that number is supposed
to miss the anchor. Only a line that pairs a weight with the tempo it buys is a claim.

cited: t_55e37b88 / t_c92f566d (this incident), t_92a09bdc (elemental-air, 0.2667),
t_25a6499c (D1 the fix: bpm is not requestable), t_55379aba (the sibling gap: no check
recomputed a brief's figures at all).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BRIEF_GLOB = "music/briefs/**/*.md"
ANCHOR_RE = re.compile(r"(\d{2,3})\s*BPM")
TOKEN_RE = re.compile(r"style[_ ]?[Ww]eight")
WEIGHT_RE = re.compile(r"(\d\.\d+)")
SOLVE_RE = re.compile(r"\(\s*(\d{2,3})\s*-\s*60\s*\)\s*/\s*120")


def genre_of(rel: str) -> str | None:
    """`music/briefs/elemental-earth.md` and `music/briefs/elemental-earth/x/brief.md`
    resolve to the same genre — briefs are keyed by genre, not by card."""
    parts = Path(rel).parts
    if len(parts) < 3 or parts[0] != "music" or parts[1] != "briefs":
        return None
    return parts[2][:-3] if len(parts) == 3 and parts[2].endswith(".md") else parts[2]


def first_text_block(raw: str) -> str | None:
    m = re.search(r"```text\n(.*?)\n```", raw, re.DOTALL)
    return m.group(1) if m else None


def anchor_bpm(repo: Path, genre: str) -> int | None:
    tmpl = repo / "music" / "prompts" / f"{genre}.md"
    if not tmpl.is_file():
        return None
    block = first_text_block(tmpl.read_text(encoding="utf-8"))
    if block is None:
        return None
    m = ANCHOR_RE.search(block)
    return int(m.group(1)) if m else None


def engine_bpm(w: float) -> int:
    return max(30, min(240, int(60 + w * 120)))


def smallest_fix(anchor: int, digits: int = 4) -> float | None:
    """The smallest value at this precision whose truncation lands on anchor."""
    step = 10 ** -digits
    w = anchor_to_floor(anchor)
    for _ in range(10 ** digits):
        w = round(w + step, digits)
        if engine_bpm(w) == anchor:
            return w
        if w >= 1.0:
            return None
    return None


def anchor_to_floor(anchor: int) -> float:
    return max(0.0, (anchor - 60) / 120.0)


def claims_in(text: str):
    """Yield (lineno, line, weight, stated_bpm)."""
    for lineno, line in enumerate(text.splitlines(), 1):
        tok = TOKEN_RE.search(line)
        if not tok:
            continue
        stated = ANCHOR_RE.search(line)
        solve = SOLVE_RE.search(line)
        stated_bpm = int(stated.group(1)) if stated else (int(solve.group(1)) if solve else None)
        if stated_bpm is None:
            continue
        tail = line[tok.start():]
        ws = [float(x) for x in WEIGHT_RE.findall(tail) if 0.0 < float(x) < 1.0]
        if not ws:
            continue
        yield lineno, line, ws[-1], stated_bpm


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Recompute the BPM a brief's styleWeight buys.")
    ap.add_argument("--repo", default=str(here.parents[2]))
    ap.add_argument("--briefs", action="append", default=[])
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    briefs = sorted(str(p.relative_to(repo)) for p in repo.glob(BRIEF_GLOB) if p.is_file())
    if args.briefs:
        want = {b.lstrip("./") for b in args.briefs}
        briefs = [b for b in briefs if b in want or any(b.endswith(w) for w in want)]
    if not briefs:
        print("FAIL check_brief_bpm_solutions: no briefs matched")
        return 2

    checked = 0
    skipped: list[str] = []
    failures: list[str] = []
    for rel in briefs:
        genre = genre_of(rel)
        anchor = anchor_bpm(repo, genre) if genre else None
        if anchor is None:
            skipped.append(f"{rel} (no genre template / no anchor BPM in its caption)")
            continue
        for lineno, line, w, stated in claims_in((repo / rel).read_text(encoding="utf-8")):
            got = engine_bpm(w)
            checked += 1
            if got == stated:
                continue
            fix = smallest_fix(stated)
            failures.append(
                f"  {rel}:{lineno}  owns \"styleWeight {w} -> {stated} BPM\"\n"
                f"      deployed rule: int(60 + {w} * 120) = {got} BPM"
                f"  ({stated - got:+d} against the claim)\n"
                f"      smallest 4-decimal value that buys {stated}: {fix}"
                f"    |  line: {line.strip()[:110]}")

    if failures:
        print(f"FAIL check_brief_bpm_solutions: {len(failures)} of {checked} "
              f"styleWeight claim(s) do not buy the BPM they state")
        print("\n".join(failures))
        print("  Fix: correct the value in the citing brief. The engine TRUNCATES "
              "(int), so the algebra (anchor-60)/120 lands one BPM short.")
        print("  cited: t_55e37b88/t_c92f566d (elemental-earth 0.2333 -> 87); "
              "t_25a6499c (bpm is not requestable)")
        return 1

    print(f"PASS check_brief_bpm_solutions: {checked} styleWeight claim(s) across "
          f"{len(briefs) - len(skipped)} brief(s) buy the BPM they state")
    for s in skipped:
        print(f"  skip {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
