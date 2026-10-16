#!/usr/bin/env python3
"""check_code_census — recompute the blueprint census the lane's OWN .py prose states.

WHY THIS EXISTS
---------------
INCIDENT (2026-10-16, card t_a54fb00d). Three figures in this lane's own code each described the
blueprint census as it stood when the line was written, and each aged silently across two census
moves (`music/lyrics/blueprints/` went 3 -> 6 -> 7 files while the registry held 14 genres):

  music/planner/planner.py:297  load_blueprint docstring `(3 of 15 genres do).` at `3967dea`
  music/planner/planner.py:309  the `11 genres that have no blueprint yet` at `dda0d32`
  music/tests/test_planner.py:62 `Only 3 of 14 genres have a blueprint, so 11 …` at `dda0d32`

Nothing read them. `music/scripts/check_brief_drift.py` recomputes this census live, but it reads
`music/briefs/**/*.md` only, so a `#` comment or a docstring was outside every check's surface, and
`check_brief_figures.py` cannot see a count that carries no unit and no filename. Three figures,
three different denominators (15, 14, a bare 11) — and one of them, the `15`, matches no tracked
revision at all, so no check could ever have recomputed it.

The FAILURE -> TEST rule for this lane: a fix without a check lets the failure come back. This is
that check.

WHAT IT READS — and what it deliberately does not
-------------------------------------------------
For every `music/**/*.py` under the repo it reads PROSE ONLY:

  * a `#` comment — its text is a claim about the code it sits in.
  * a module / class / function DOCSTRING — prose a reader is meant to trust.

A bare string literal is NOT prose: it is DATA. The fixtures in `check_brief_drift.py` are
deliberately stale census strings that drive another checker's assertions, and reading them as
claims would make this check fire on the very file that exists to catch staleness. A docstring is
identified by `ast` (the first statement of a module/class/function), so a string inside a list
stays data.

Each unit is then tested for the census shapes this lane writes, with two escape hatches:

  * a count inside double quotes is a QUOTATION, not the file's own claim — skipped (same rule and
    same rationale as `check_brief_drift.in_quotes`).
  * a count on a line that names a revision or stamps a clock time is HISTORY, not a claim about
    now — skipped by `ANCHORED`, the same escape hatch, imported rather than re-invented.

The shapes and the ANCHORED rule are IMPORTED from `check_brief_drift.py`, so the brief surface and
the code surface cannot disagree about either. This module does not modify that one and does not
widen its rule; it adds the one shape that exists only in code prose (`NO_BLUEPRINT`, the
"the N genres that have no blueprint yet" shape at planner.py:309).

RUN
---
  /usr/bin/python3 music/scripts/check_code_census.py [--repo DIR] [--rev REV] [--quiet-skips]
  /usr/bin/python3 music/scripts/check_code_census.py --selftest

Exit 0 when every unanchored, unquoted census claim matches the live census; 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# The shapes, the number parser and the ANCHORED rule: reused, never re-invented.
from check_brief_drift import (  # noqa: E402
    ANCHORED, BLUEPRINT_LESS, N_BLUEPRINTS, NUM_OF_GENRES, OF_GENRES, _NUMTOK, in_quotes, num,
)

# The one shape this file adds: planner.py:309's "the N genres that have no blueprint yet".
# It carries no `of M` pair, so no check_brief_drift shape covers it. A `blueprints/{a,b}.yaml`
# brace list is deliberately NOT read here: that is a brief shape, and a code docstring that
# shows one as an example would be a false positive.
NO_BLUEPRINT = re.compile(
    rf"(?:the\s+)?({_NUMTOK})\s+genres?\s+(?:that|which)\s+"
    rf"(?:have|has|lack|carry)\s+no\s+(?:lyric\s+)?blueprint", re.I)


class CensusUnavailable(Exception):
    """The live census cannot be recomputed here — an environment problem, not a finding."""


# ---------------------------------------------------------------------------
# prose extraction (pure enough to test: text in, units out)
# ---------------------------------------------------------------------------

def docstring_units(source: str) -> tuple[list[tuple[int, str]], str]:
    """[(lineno, text)] for every module/class/function docstring. Data strings excluded."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [], f"does not parse ({exc.__class__.__name__}: {exc.msg})"
    units: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None) or []
        if not body or not isinstance(body[0], ast.Expr):
            continue
        first = body[0].value
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            units.append((first.lineno, first.value))
    return units, ""


def comment_units(source: str) -> tuple[list[tuple[int, str]], str]:
    """[(lineno, text)] for every `#` comment."""
    units: list[tuple[int, str]] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                units.append((tok.start[0], tok.string.lstrip("#").rstrip()))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        return units, f"comment tokenize stopped early ({exc.__class__.__name__})"
    return units, ""


def prose_units(source: str) -> tuple[list[tuple[int, str]], list[str]]:
    """[(lineno, text)] for every comment and docstring, plus notes about what was skipped."""
    notes: list[str] = []
    docs, doc_err = docstring_units(source)
    if doc_err:
        notes.append(doc_err)
    comments, com_err = comment_units(source)
    if com_err:
        notes.append(com_err)
    return sorted(comments + docs), notes


# ---------------------------------------------------------------------------
# the checker itself (pure: one unit's text in, findings out)
# ---------------------------------------------------------------------------

def scan_unit(unit: str, live: dict, where: str, base: int = 1) -> tuple[list[str], int]:
    """(findings, checked) for one prose unit. `where` is a file path; `base` its first line.

    Two granularities, both copied from the brief-side check rather than invented here:

    * ANCHORED is applied PER LINE: one historical sentence in a twenty-line docstring must not
      switch the check off for the other nineteen. An anchored line is blanked, not dropped, so a
      claim that WRAPS onto it stops matching while its neighbours keep theirs.
    * an `of`-pair is read only on a line that itself says `blueprint` — a docstring that mentions
      blueprints in one paragraph and counts a DIFFERENT census (8 of the 14 templates are
      instrumental) in another must not be read as a blueprint claim. The shapes whose pattern
      already contains the word (NO_BLUEPRINT, BLUEPRINT_LESS, N_BLUEPRINTS, OF_GENRES) are
      self-gating and may span lines.
    """
    findings: list[str] = []
    checked = 0
    masked_lines = ["" if ANCHORED.search(ln) else ln for ln in (unit.splitlines() or [unit])]
    masked = "\n".join(masked_lines)
    if "blueprint" not in masked.lower():
        return findings, checked
    quoted = in_quotes(False, masked, 0)
    offsets: list[int] = []
    pos = 0
    for ln in masked_lines:
        offsets.append(pos)
        pos += len(ln) + 1

    def label(start: int) -> str:
        return f"{where}:{base + masked[:start].count(chr(10))}"

    def stale(msg: str, start: int) -> None:
        findings.append(f"{label(start)}  {msg}  [STALE CENSUS]")

    def pair(a: str, b: str, start: int) -> None:
        nonlocal checked
        checked += 1
        if num(a) != live["blueprints"] or num(b) != live["genres"]:
            stale(f'claimed "{a} of {b} genres"  measured {live["blueprints"]} of the '
                  f'{live["genres"]} (music/lyrics/blueprints/*.yaml)', start)

    def census_count(phrase: str, got: str, want: int, measured: str, start: int) -> None:
        nonlocal checked
        checked += 1
        if num(got) != want:
            stale(f'claimed "{phrase}"  measured {measured}', start)

    # The `of`-pairs, one line at a time: the line must carry the word itself.
    #
    # NUM_OF_GENRES only — the `of M genres` shape. check_brief_drift's S4 (`only 3 of the 14
    # exist`, no `genres` word after the pair) is deliberately NOT read here: in brief prose the
    # subject is unambiguous, but in a docstring a line can mention blueprints in one clause and
    # count a DIFFERENT census in another, and S4 would fire on that second census. Measured while
    # writing this file: a docstring line saying "... (8 of the 14 templates are instrumental) ..."
    # was flagged as a blueprint census by S4. In this lane's CODE the pair always names `genres`.
    for idx, line in enumerate(masked_lines):
        if "blueprint" not in line.lower():
            continue
        for hit in NUM_OF_GENRES.finditer(line):
            start = offsets[idx] + hit.start()
            if in_quotes(quoted, masked, start):
                continue
            pair(hit.group(1), hit.group(2), start)
    for hit in OF_GENRES.finditer(masked):
        if in_quotes(quoted, masked, hit.start()):
            continue
        census_count(hit.group(0), hit.group(1), live["blueprints"],
                     f'{live["blueprints"]} (music/lyrics/blueprints/*.yaml)', hit.start())
    for pattern in (BLUEPRINT_LESS, NO_BLUEPRINT):
        for hit in pattern.finditer(masked):
            if in_quotes(quoted, masked, hit.start()):
                continue
            census_count(hit.group(0), hit.group(1), live["genres"] - live["blueprints"],
                         f'{live["genres"] - live["blueprints"]} ({live["genres"]} registered '
                         f'genres - {live["blueprints"]} in music/lyrics/blueprints/)',
                         hit.start())
    for hit in N_BLUEPRINTS.finditer(masked):
        if in_quotes(quoted, masked, hit.start()):
            continue
        census_count(hit.group(0), hit.group(1), live["blueprints"],
                     f'{live["blueprints"]} (music/lyrics/blueprints/*.yaml)', hit.start())
    return findings, checked


# ---------------------------------------------------------------------------
# live values (the same loader path check_brief_drift.live_census uses)
# ---------------------------------------------------------------------------

def live_census(repo: Path) -> tuple[int, int, set[str]]:
    """(genres registered, lyric blueprints that exist, their genre names).

    Raises `CensusUnavailable` rather than letting the loader's traceback out: this check is meant
    to run inside `verify-fleet.sh` section 13i, which extracts `music/` from HEAD, and a partial
    extract (no `music/visuals/*.md`, which `genres.yaml` resolves its `visual_style` paths against)
    makes the registry refuse to load. A stack trace there reads as a lane regression; it is not
    one, and the message must say so.
    """
    sys.path.insert(0, str(repo / "music"))
    import registry  # noqa: PLC0415  (needs sys.path set first)
    try:
        genres = len(registry.load_registry()["genres"])
    except Exception as exc:  # noqa: BLE001  (any loader failure is "cannot recompute", not a finding)
        first = str(exc).splitlines()[0][:160] if str(exc) else exc.__class__.__name__
        raise CensusUnavailable(
            f"cannot recompute the census at {repo}: the registry did not load "
            f"({exc.__class__.__name__}: {first}) — this check needs the full music/ tree, "
            f"including music/visuals/*.md, which genres.yaml resolves against") from exc
    names = {p.stem for p in (repo / "music" / "lyrics" / "blueprints").glob("*.yaml")}
    return genres, len(names), names


def source_files(repo: Path, rev: str | None) -> list[str]:
    """Relative paths of the lane's python files, worktree or at `rev`."""
    if rev:
        res = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", rev],
                             capture_output=True, text=True, check=False)
        if res.returncode != 0:
            sys.exit(f"FATAL: cannot list {rev} in {repo}: {res.stderr.strip()}")
        return sorted(p for p in res.stdout.splitlines()
                      if p.startswith("music/") and p.endswith(".py"))
    return sorted(str(p.relative_to(repo))
                  for p in (repo / "music").rglob("*.py") if "__pycache__" not in p.parts)


def read(repo: Path, rel: str, rev: str | None) -> str:
    if not rev:
        return (repo / rel).read_text(encoding="utf-8")
    res = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"],
                         capture_output=True, text=True, check=False)
    return res.stdout if res.returncode == 0 else ""


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

LIVE = {"genres": 14, "blueprints": 7}


def selftest() -> int:
    """One case per shape, plus the two escape hatches and the two look-alike censuses."""
    cases = [
        ("a current `of` pair",
         "blueprints/<genre>.yaml when it exists (7 of 14 genres do).\n", 0, 1),
        ("a stale `of` pair (planner.py:297)",
         "blueprints/<genre>.yaml when it exists (3 of 15 genres do).\n", 1, 1),
        ("a current pair, `of the`",
         "and only 7 of the 14 genres have a lyric blueprint\n", 0, 1),
        ("a stale pair, `of the`",
         "and only 6 of the 14 genres have a lyric blueprint\n", 1, 1),
        ("a current no-blueprint count",
         "the only tempo signal available for the 7 genres that have no blueprint yet\n", 0, 1),
        ("a stale no-blueprint count (planner.py:309)",
         "the only tempo signal available for the 11 genres that have no blueprint yet\n", 1, 1),
        ("a current reversed sense", "only 7 genres with a lyric blueprint\n", 0, 1),
        ("a stale reversed sense", "only 3 genres with a lyric blueprint\n", 1, 1),
        ("a stale bare count", "14 registered genres minus 3 blueprints only\n", 1, 1),
        ("the KEY census is not this census",
         "key is null for the 11 genres whose caption states none\n", 0, 0),
        ("the TEMPLATE census is not this census",
         "13 of the 14 templates have exactly one style field\n", 0, 0),
        ("a quoted census is a quotation (epic-orchestral-boss.md's shape)",
         'the docstring "(3 of 15 genres do)" is stale, not a behaviour\n', 0, 0),
        ("an anchored census is history, by clock",
         "6 of the 14 genres carried a blueprint measured at 2026-10-16 15:31 CDT\n", 0, 0),
        ("an anchored census is history, by revision",
         "6 of the 14 genres at `8f0fd9a`\n", 0, 0),
        ("an anchored LINE does not switch off its neighbours",
         "12 of the 14 genres at `8f0fd9a`\nand only 3 of the 14 genres have a lyric blueprint\n",
         1, 1),
        ("S4 with no `genres` word is a brief shape, not read here",
         "when music/lyrics/blueprints/<genre>.yaml is absent, and only 3 of the 14 exist\n", 0, 0),
    ]
    failures: list[str] = []
    for name, unit, want_findings, want_checked in cases:
        found, checked = scan_unit(unit, LIVE, name)
        if len(found) != want_findings or checked != want_checked:
            failures.append(f"{name}: findings={len(found)} (want {want_findings}), "
                            f"checked={checked} (want {want_checked})")
        for f in found:
            if want_findings == 0:
                failures.append(f"  false positive in {name}: {f}")
    # The prose extractor: a docstring is prose, a bare literal is data, comments are prose.
    src = ('"""Module prose: 3 of 15 genres do."""\n'
           "import os\n"
           "FIXTURES = ['only 3 of the 14 genres have a lyric blueprint']\n"
           "# a comment: 6 of the 14 genres\n"
           "def f():\n"
           '    """Doc prose: 3 blueprints only."""\n'
           "    return os\n")
    units, notes = prose_units(src)
    texts = " || ".join(t for _, t in units)
    if notes:
        failures.append(f"prose_units reported {notes} on a clean fixture")
    for want in ("Module prose", "a comment: 6 of the 14 genres", "Doc prose"):
        if want not in texts:
            failures.append(f"prose_units missed {want!r}")
    if "only 3 of the 14 genres" in texts:
        failures.append("prose_units read a bare string literal as prose (it is data)")
    print(f"SELFTEST {'PASS' if not failures else 'FAIL'} check_code_census: {len(cases)} "
          f"census case(s) plus one prose-extraction case")
    for f in failures:
        print("  " + f)
    return 0 if not failures else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="recompute the blueprint census the lane's own .py prose states")
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--rev", default=None, help="read the .py files at this revision, not the tree")
    ap.add_argument("--quiet-skips", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    try:
        genres, blueprints, names = live_census(repo)
    except CensusUnavailable as exc:
        print(f"FAIL check_code_census: {exc}")
        print("  Fix: point --repo at a full checkout of the lane (or at a clean extract that "
              "includes music/visuals/*.md). This is an environment failure, not a stale figure.")
        return 1
    live = {"genres": genres, "blueprints": blueprints, "blueprint_names": names}
    rels = source_files(repo, args.rev)
    if not rels:
        print(f"FAIL check_code_census: no .py files matched under {repo}/music")
        return 1

    findings: list[str] = []
    notes: list[str] = []
    checked = 0
    for rel in rels:
        src = read(repo, rel, args.rev)
        units, unit_notes = prose_units(src)
        for note in unit_notes:
            notes.append(f"{rel} {note}")
        for lineno, text in units:
            found, seen = scan_unit(text, live, rel, lineno)
            findings.extend(found)
            checked += seen

    where = f"revision {args.rev}" if args.rev else f"worktree {repo}"
    if findings:
        print(f"FAIL check_code_census: {len(findings)} stale census claim(s) in {where}")
        for f in findings:
            print("  " + f)
        print(f"  {checked} claim(s) checked across {len(rels)} .py file(s); live: {genres} "
              f"registered genres, {blueprints} in music/lyrics/blueprints/")
        print("  Fix: correct the figure in the comment or docstring, or anchor it to a revision "
              "on the same line (`sha`, `HH:MM`) — an anchored census is history, an unanchored "
              "one is a claim about now (card t_a54fb00d).")
        return 1
    if notes and not args.quiet_skips:
        print(f"NOTE check_code_census: {len(notes)} file(s) not fully read — reported, "
              f"never guessed:")
        for n in notes:
            print("  " + n)
    print(f"PASS check_code_census: {checked} live census claim(s) across {len(rels)} .py "
          f"file(s) match {where} ({genres} registered genres, {blueprints} blueprints)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
