#!/usr/bin/env python3
"""check_brief_line_refs — verify the LINE citations a music brief makes, and their edges.

WHY THIS EXISTS
---------------
A brief in this lane IS the evidence artifact for a genre: a reader who wants to check a
claim is told exactly where to look ("`music/genres.yaml` lines 47–54") and is expected to
open that range. `music/scripts/check_brief_figures.py` recomputes the figures that carry a
unit (bytes / chars / lines), but a bare line citation carries NO unit token, so nothing
checked one — and a range whose first line is BLANK sends the reader to the wrong line.

INCIDENT (2026-10-16, card t_f8b2fa7f, the duplicate-card pass for `jungle-dnb`)
---------------------------------------------------------------------------------
`music/briefs/jungle-dnb.md` §1 and §13 cited the registry defaults block as
"`music/genres.yaml` **lines 19–25**". Measured in the worktree:

    $ grep -n "^version:\\|^defaults:\\|^  jungle-dnb:" music/genres.yaml
    18:version: 1          <- line 19 is BLANK
    20:defaults:
    47:  jungle-dnb:

The `defaults:` block is lines **20–25**; line 19 is empty, so the citation opens on a blank
line. The SAME off-by-one is present in `music/briefs/chiptune-8bit.md` §1 and
`music/briefs/anime-opening.md` §1 — and anime-opening's own duplicate pass had already
"corrected" the range to 20–25 in its comparison table while leaving it wrong in the body, so
a hand fix did not hold. That is the same shape as the two figure incidents
`check_brief_figures.py` records: one wrong claim, copied between briefs, surviving a manual
pass because nothing measured it.

SECOND INCIDENT (2026-10-16, card t_e86c2110, the citation sweep for the two remaining files)
----------------------------------------------------------------------------------------------
The check stopped finishing. Its link-gap pattern nested a repeat inside a repeat over two
overlapping character classes — the classic `(a+)+` shape — so it backtracked exponentially on
any gap that fails to match: 8 spaces then `#` measured 0.002 s, 12 measured 0.27 s, 16 measured
35 s, and `music/briefs/elemental-water.md` carries a fenced transcript whose trailing comment
sits 23 spaces out. One brief took >45 s, the repo-wide run >200 s. The pattern is now a single
unrolled alternation that accepts the same language (brute-forced over every string up to length
6) and `--selftest` asserts the gap from that incident stays linear.

THIRD INCIDENT (2026-10-16, card t_8d6c40ac, the false-attribution report)
-------------------------------------------------------------------------
`music/briefs/chiptune-8bit.md` quotes this check's OWN past output inside a fenced transcript —
`FAIL check_brief_line_refs rc=1: 1 of 107 cited line range(s) does not hold —
music/briefs/elemental-fire.md:605` — under the prose "The checks cited above were run at revision
`c296db6` (2026-10-16, before this pass's commit) … Verbatim results:". Rule 3 looked for the
anchor on the QUOTING line; it sits on the prose above the fence, so backtick-stripping left the
quoted `path:605` indistinguishable from a pointer: the check FAILed the brief that REPORTED the
defect, told it to "correct … the citing brief" (i.e. another genre's line numbering), and — since
the target brief was being rewritten by a concurrent worker at that minute — failed only
sometimes. `repro_incident.py` (workspace of t_8d6c40ac) reproduces the shape on a fixture:
pre-fix rc=1 on the quoting brief, post-fix rc=0 while the same blank line cited bare still
FAILs.

WHAT IT DOES
------------
For every `music/briefs/**/*.md` it finds line citations and measures each one against the
referent file in the worktree:

  * `<path>:A` and `<path>:A-B`          — point / range with an inline path
  * `<path> lines A–B` (or `line A`)     — path named earlier on the line
  * `lines A–B` / `line A`               — inherits the nearest path earlier on the line
  * `, A–B` (a comma continuation)       — inherits, as the prose reads it

A citation FAILS when:
  1. the range or point lies outside the referent file's line count;
  2. the FIRST line of the range is blank (the reader lands on nothing);
  3. the LAST line of the range is blank; or
  4. a point citation lands on a blank line.

Rules (kept deliberately narrow, so the check is signal and not noise)
---------------------------------------------------------------------
1. A referent the repo cannot resolve uniquely is SKIPPED, never guessed: a basename that
   occurs more than once in the repo (`gate_sync_ready.py` exists both at `music/` and
   `music/gates/`) is reported as ambiguous and left alone — the brief must name the full
   path. Revision-qualified refs (`origin/main:music/suno-gen.py:184`) and paths outside the
   repo (`/opt/sunolocal/...`) are skipped for the same reason.
2. Only the WORKING TREE is read. A line citation is a claim about the file a reader will
   open; a stale citation of a moved block is exactly what this catches.
3. A citation ANCHORED to a revision or a clock time on the same line (`at `456d525``,
   "measured on …", `HH:MM`, "when written") is a historical fact and is SKIPPED — the same
   rule `music/scripts/check_brief_drift.py` applies to counts. An unanchored citation is a
   claim about now.
4. Backticks are stripped before parsing; a path is linked to a claim only when the gap
   between them is a link syntax (whitespace, "(", ",", "lines"/"line"), not arbitrary prose.
5. Rule 3 at BLOCK level: a citation inside a fenced block whose INTRODUCING PROSE is anchored
   to a revision or a clock time is a quoted transcript, and is SKIPPED under the `quoted at a
   rev` bucket. The anchor usually sits on the prose above the fence, not on the quoting line,
   so the same-line test of rule 3 cannot see it. A fence whose introduction carries no anchor
   is still measured line by line — that half is asserted by `--selftest`.
6. Rule 5 at BLOCK GRAMMAR level (card t_2f9b441c): the anchor is not always in the
   introducing paragraph. A fence whose BODY carries a checker result line — `PASS check_<name>`,
   `FAIL check_<name>`, `SELFTEST PASS check_<name>`, or a `# rc=N` exit annotation — is a
   TRANSCRIPT of a past run, and the indented lines that follow a result line are that checker's
   OWN PRINTED FINDINGS, not claims the brief makes about the referent today. Citations on those
   lines are SKIPPED under `quoted at a rev`. The block boundary is the checker-result line plus
   its continuation: a `$ ` command or a `# rc=N` line ends the block (a new run starts), and a
   bare `PASS`/`FAIL` without a `check_` name is NOT a result (it is a code sample, still
   measured). A fence with neither an anchored introduction nor a checker result in its body is
   measured line by line — that half is asserted by `--selftest`.

SIBLING CHECKS (deliberately not duplicated here)
------------------------------------------------
  * `music/scripts/check_brief_figures.py` — figures that carry a UNIT next to a named file.
  * `music/scripts/check_brief_drift.py` — live counts (commit divergence, blueprint census).
  * `music/scripts/check_brief_paths.py` — do cited paths resolve.
  * `music/scripts/check_brief_bpm_solutions.py` — does a styleWeight buy the BPM it claims.
  * `music/scripts/check_prompt_style_counts.py` — does a template's declared style length hold.
  * `music/scripts/check_stage_scripts.py` — do stage-referenced scripts exist in this tree.

Usage:
  /usr/bin/python3 music/scripts/check_brief_line_refs.py [--repo DIR] [--briefs PATH]...
  /usr/bin/python3 music/scripts/check_brief_line_refs.py --selftest

Exit codes: 0 = PASS, 1 = a citation does not hold, 2 = usage / no briefs matched.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BRIEF_GLOB = "music/briefs/**/*.md"
PATH_TOK = r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|yaml|yml|py|json|sh|txt|jsonl)"
PATH_RE = re.compile(PATH_TOK)
RANGE_RE = re.compile(r"(\d+)\s*[–—-]\s*(\d+)")
POINT_RE = re.compile(r"(?P<f>" + PATH_TOK + r"):(?P<n>\d+)")
# The gap vocabulary: whitespace, the punctuation a brief writes between a path and its claim,
# and the words that introduce a line claim. ONE unrolled alternation, deliberately — the obvious
# form, `(?:[\s(),;:\[\]*(?:lines?|around|~|≈)?[\s(),;:]*)*`, nests a repeat inside a repeat over
# two overlapping classes (the `(a+)+` shape) and backtracks exponentially when a gap fails to
# match. Measured 2026-10-16 (card t_e86c2110): a gap of 8 spaces then `#` took 0.002 s, 12 took
# 0.27 s, 16 took 35 s. `music/briefs/elemental-water.md` carries a fenced transcript whose
# trailing comment is 23 spaces out, so the whole check stopped finishing (>45 s on that one
# brief, >200 s on the repo). Both forms accept the SAME language: the old one is
# `(C1* (?:lines?|around|~|≈)? C2*)*` with C1 and C2 both subsets of `[\s(),;:\[]`, i.e.
# `(?:C|lines?|around|~|≈)*` — verified by brute force over every string up to length 6.
# `--selftest` now asserts the incident gap stays fast.
LINK_RE = re.compile(r"^(?:[\s(),;:\[]|lines?|around|~|≈)*$")
# A citation ANCHORED to a revision or a clock time is a historical fact, not a claim about the
# file a reader opens today — exactly the rule `music/scripts/check_brief_drift.py` uses for
# counts (its `ANCHORED`, lines 90–96). Skipped, not guessed at.
ANCHORED = re.compile(
    r"`[0-9a-f]{7,40}`|when written|at write time|at filing|"
    r"\b\d{1,2}:\d{2}\b|\bmeasured (?:at|on)\b", re.I)
# Rule 5, card t_8d6c40ac: a fenced block introduced by anchored prose is a TRANSCRIPT of a past
# run. The `path:LINE` inside it is what the run PRINTED, not a pointer a reader is meant to open
# today — and the anchor sits on the prose above the fence, where rule 3's same-line test cannot
# see it. Deliberately narrow: the block is skipped only when its introduction carries an anchor.
# Rule 6, card t_2f9b441c: the anchor is not always in the introduction. A fence whose BODY
# carries a checker result line is a transcript too, and the indented lines that follow a result
# line are that checker's own printed findings. A bare `PASS`/`FAIL` with no `check_` name is a
# code sample, not a result — it stays measured (asserted by `--selftest`).
_RESULT = re.compile(r"^\s*(?:SELFTEST\s+)?(?:PASS|FAIL)\s+check_\w")
_CMD = re.compile(r"^\s*\$ ")
_RC = re.compile(r"^\s*#\s*rc=\d+")
_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_FENCE_INTRO_GAP = 2        # blank lines tolerated between the introducing prose and the fence
_FENCE_INTRO_LINES = 6      # lines of introducing prose collected above the fence
_LINK_GAP = 60          # max chars between a path and the claim it introduces
_HEREDOC_GUARD = 3      # a path must be within this many tokens of the claim's line


class Tree:
    """The worktree this check reads."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo

    def label(self) -> str:
        return f"worktree {self.repo}"

    def briefs(self) -> list[str]:
        return sorted(str(p.relative_to(self.repo))
                      for p in self.repo.glob(BRIEF_GLOB) if p.is_file())

    def read(self, rel: str) -> str | None:
        p = self.repo / rel
        if not p.is_file():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return None

    def resolve(self, tok: str) -> tuple[str | None, str]:
        """Return (repo-relative path, why-not) for a cited path token.

        A token with a directory component is trusted as written (repo-root- or
        `music/`-relative). A bare basename is resolved only when it is unique in the
        repo: this lane carries same-named files in two places (`gate_sync_ready.py`
        at both `music/` and `music/gates/`), so a bare basename is a real ambiguity
        and must be skipped, never guessed at.
        """
        if tok.startswith("/"):
            return None, "path outside the repo"
        if "/" in tok:
            cands = [p for p in (self.repo / tok, self.repo / "music" / tok) if p.is_file()]
            if len(cands) == 1:
                return str(cands[0].relative_to(self.repo)), ""
            if len(cands) > 1:
                return None, "ambiguous path (" + ", ".join(sorted(
                    str(c.relative_to(self.repo)) for c in cands)) + ")"
            return None, "no such file in the worktree"
        hits = sorted(p for p in self.repo.rglob(Path(tok).name) if p.is_file())
        if len(hits) == 1:
            return str(hits[0].relative_to(self.repo)), ""
        if len(hits) > 1:
            return None, ("ambiguous basename (" + ", ".join(
                str(h.relative_to(self.repo)) for h in hits) + "); name the full path")
        return None, "no such file in the worktree"


def _linked(path_end: int, claim_start: int, line: str) -> bool:
    """True when only a link syntax separates a path token from its claim."""
    return 0 <= claim_start - path_end <= _LINK_GAP and bool(
        LINK_RE.match(line[path_end:claim_start]))


def citations(line: str) -> list[tuple[str | None, int, int | None, str]]:
    """Return [(path token or None, first, last or None, syntax)] for one brief line.

    `syntax` names the shape, so a failure message can quote what the brief wrote.
    """
    flat = line.replace("`", "")
    paths = [(m.start(), m.end(), m.group(0)) for m in PATH_RE.finditer(flat)]
    found: list[tuple[str | None, int, int | None, str]] = []
    taken: list[tuple[int, int]] = []

    for m in POINT_RE.finditer(flat):
        f, n = m.group("f"), int(m.group("n"))
        found.append((f, n, None, f"{f}:{n}"))
        taken.append((m.start("f"), m.end()))

    for m in RANGE_RE.finditer(flat):
        a, b, start = int(m.group(1)), int(m.group(2)), m.start()
        if any(s <= start < e for s, e in taken):
            continue
        owner = None
        for ps, pe, tok in paths:
            if pe <= start and _linked(pe, start, flat):
                owner = tok                      # nearest preceding linked path
        if owner is None:
            # `, A–B` continues the previous path's list; a lone `A–B` does not.
            if not re.match(r"^\s*,\s*$", flat[max(0, start - 3):start]):
                continue
            for ps, pe, tok in paths:
                if pe <= start:
                    owner = tok
        found.append((owner, a, b, f"lines {a}–{b}"))
        taken.append((start, m.end()))

    for m in re.finditer(r"\blines?\s+(\d+)\b", flat):
        n, start = int(m.group(1)), m.start()
        if any(s <= start < e for s, e in taken):
            continue
        if re.match(r"\s*[–—-]\s*\d", flat[m.end():m.end() + 6]):
            continue                     # this is a range, already handled
        owner = None
        for ps, pe, tok in paths:
            if pe <= start and _linked(pe, start, flat):
                owner = tok
        if owner is None:
            continue
        found.append((owner, n, None, f"line {n}"))
        taken.append((start, m.end()))

    return found


def _fence_marker(line: str) -> tuple[str, int] | None:
    """(marker char, run length) when `line` is a markdown code fence, else None."""
    m = _FENCE.match(line)
    return (m.group(1)[0], len(m.group(1))) if m else None


def fence_intro(lines: list[str], idx: int) -> tuple[int, str]:
    """The prose paragraph introducing the fence at 0-based `idx`: (1-based first line, prose).

    Scans up over at most `_FENCE_INTRO_GAP` blank lines, then collects at most
    `_FENCE_INTRO_LINES` contiguous non-blank lines. Marks the paragraph that a markdown reader
    reads as the fence's introduction ("… Verbatim results:"), which is where the revision
    anchor of card t_8d6c40ac sits. `(0, "")` means: no introduction close enough to read, so
    the fence is not a transcript under rule 5.
    """
    j = idx - 1
    for _ in range(_FENCE_INTRO_GAP + 1):
        if j < 0 or lines[j].strip():
            break
        j -= 1
    end = j
    while j >= 0 and lines[j].strip() and end - j < _FENCE_INTRO_LINES:
        j -= 1
    if end < 0 or not lines[end].strip():
        return 0, ""
    return j + 2, "\n".join(lines[j + 1:end + 1])


def check_brief(tree: Tree, rel: str) -> tuple[list[str], int, int, list[str]]:
    """Return (failures, checked, skipped, skip notes)."""
    text = tree.read(rel)
    if text is None:
        return ([f"  {rel}:1  MISSING from {tree.label()}"], 0, 0, [])
    failures: list[str] = []
    checked = skipped = 0
    notes: list[str] = []
    cache: dict[str, list[str]] = {}
    raw = text.splitlines()
    in_fence = False
    fence_open: tuple[str, int] | None = None    # (marker char, run length) of the open fence
    quoted_at = 0            # 1-based line of the anchored prose that introduces the open fence
    in_result = False        # inside a checker's printed findings (rule 6)

    def src(path: str) -> list[str]:
        if path not in cache:
            cache[path] = (tree.read(path) or "").splitlines()
        return cache[path]

    for lineno, line in enumerate(raw, 1):
        mark = _fence_marker(line)
        if mark is not None:
            if not in_fence:
                in_fence, fence_open = True, mark
                intro_ln, prose = fence_intro(raw, lineno - 1)
                quoted_at = intro_ln if prose and ANCHORED.search(prose) else 0
                in_result = False
                continue
            if fence_open and mark[0] == fence_open[0] and mark[1] >= fence_open[1]:
                in_fence, fence_open, quoted_at = False, None, 0
                in_result = False
                continue
            # a shorter or different marker inside the fence is markdown CONTENT — keep reading
        if in_fence and (_CMD.match(line) or _RC.match(line)):
            in_result = False
            continue
        if in_fence and _RESULT.match(line):
            in_result = True
            # do NOT `continue`: a result line can itself carry a `path:LINE` finding
            # (`FAIL check_brief_line_refs … music/registry.yaml:2`), and that citation is
            # the checker's own output too — it falls through to the skip below.
        anchored = bool(ANCHORED.search(line))
        for tok, a, b, syntax in citations(line):
            if anchored or quoted_at or in_result:
                skipped += 1
                if anchored:
                    notes.append(f"  {rel}:{lineno}  skipped `{syntax}` — anchored to a revision "
                                 f"or a clock time (a historical fact, not a claim about now)")
                elif in_result:
                    notes.append(f"  {rel}:{lineno}  skipped `{syntax}` — quoted at a rev: inside "
                                 f"a checker's printed findings in a transcript fence (rule 6, "
                                 f"card t_2f9b441c), not a claim about the file a reader opens "
                                 f"today")
                else:
                    notes.append(f"  {rel}:{lineno}  skipped `{syntax}` — quoted at a rev: inside "
                                 f"a fence whose introducing prose (line {quoted_at}) is anchored "
                                 f"to a revision or a clock time (a transcript of a past run, not "
                                 f"a claim about now)")
                continue
            if tok is None:
                skipped += 1
                continue
            path, why = tree.resolve(tok)
            if path is None:
                skipped += 1
                notes.append(f"  {rel}:{lineno}  skipped `{tok}` — {why}")
                continue
            lines = src(path)
            checked += 1
            here = f"{rel}:{lineno}"
            if a < 1 or a > len(lines) or (b is not None and (b < a or b > len(lines))):
                span = f"{a}–{b}" if b is not None else f"{a}"
                failures.append(
                    f"  {here}  `{path}` {syntax}  OUT OF BOUNDS — the file has "
                    f"{len(lines)} lines, the citation asks for {span}")
                continue
            if not lines[a - 1].strip():
                failures.append(
                    f"  {here}  `{path}` {syntax}  BLANK OPEN — line {a} is empty; the block "
                    f"the claim names starts at line {a + 1} "
                    f"({lines[a].strip()[:40]!r})")
                continue
            if b is not None and not lines[b - 1].strip():
                failures.append(
                    f"  {here}  `{path}` {syntax}  BLANK CLOSE — line {b} is empty; "
                    f"the block ends at line {b - 1} ({lines[b - 2].strip()[:40]!r})")
    return failures, checked, skipped, notes


def selftest() -> int:
    """Prove both directions: the off-by-one range fails, the correct range passes.

    Fixture: a referent whose block starts one line after a blank line, cited once with the
    leading blank (the jungle-dnb incident) and once exactly. A third brief cites the same
    block through an ambiguous basename — that must be SKIPPED, not guessed at.
    """
    import contextlib
    import io
    import tempfile
    import time

    # Card t_8d6c40ac: a brief that QUOTES a `path:LINE` inside a fence introduced by rev-anchored
    # prose. This is the shape of `music/briefs/chiptune-8bit.md` (it quotes this check's own past
    # output, naming `music/briefs/elemental-fire.md:605`, under "… run at revision `c296db6` …
    # Verbatim results:"). The quoted citation targets the BLANK line 2 of the referent, so pre-fix
    # it was FAILed as a claim of the quoting brief's own. Must be SKIPPED.
    quoted = ("Verbatim checker results, run at revision `c296db6` (card t_8d6c40ac):\n"
              "\n"
              "```\n"
              "FAIL check_brief_line_refs rc=1: 1 of 107 cited line range(s) does not hold"
              " — music/registry.yaml:2 (106 OK)\n"
              "```\n")
    # The SAME blank line cited bare (no fence, no anchor) is still a claim about now: MUST FAIL.
    bare = "Open `music/registry.yaml`:2 for the block.\n"
    # The block rule keys on the ANCHOR, not on the fence: an unanchored fence is still measured.
    unanchored = ("A quoted run; no revision and no clock time is named above this fence.\n"
                  "\n"
                  "```\n"
                  "the checker said music/registry.yaml:2 was empty\n"
                  "```\n")
    # Card t_2f9b441c: the anchor is not always in the introduction. A fence whose BODY carries a
    # checker result line is a transcript too — the shape of `music/briefs/jungle-dnb.md` §18,
    # which quotes `check_code_census.py --rev HEAD` printed findings (the `FAIL check_code_census`
    # line, its indented `path:LINE` findings, and the `# rc=1` annotation) under an intro that
    # names no revision. The quoted `music/tests/test_planner.py:62` targets the BLANK line 2 of
    # the referent, so pre-fix it was FAILed as a claim of the quoting brief's own. Must be SKIPPED.
    grammar = ("A census pass; the fence's introduction names no revision.\n"
               "\n"
               "```text\n"
               "$ /usr/bin/python3 music/scripts/check_code_census.py --rev HEAD\n"
               "FAIL check_code_census: 1 stale census claim(s) in revision HEAD\n"
               "  music/tests/test_planner.py:62  claimed \"3 of 14 genres\"  measured 7\n"
               "# rc=1\n"
               "```\n")
    # The same blank line quoted inside a fence with NO checker result in its body is still
    # measured: a bare `PASS`/`FAIL` with no `check_` name is a code sample, not a transcript.
    code_sample = ("A fence that prints a bare result word, no checker name.\n"
                   "\n"
                   "```\n"
                   "PASS: music/registry.yaml:2 is the block to read\n"
                   "```\n")

    # The same blank line quoted inside a fence with NO checker result in its body is still
    # measured: a bare `PASS`/`FAIL` with no `check_` name is a code sample, not a transcript.
    code_sample = ("A fence that prints a bare result word, no checker name.\\n"
                   "\\n"
                   "```\\n"
                   "PASS: music/registry.yaml:2 is the block to read\\n"
                   "```\\n")

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "music/briefs").mkdir(parents=True)
        (repo / "music/deep").mkdir(parents=True)
        (repo / "music/other").mkdir(parents=True)
        (repo / "music/registry.yaml").write_text(
            "version: 1\n\ndefaults:\n  export: studio\n  stems: true\n", encoding="utf-8")
        (repo / "music/deep/thing.yaml").write_text("a: 1\n", encoding="utf-8")
        (repo / "music/other/thing.yaml").write_text("a: 1\n", encoding="utf-8")

        def brief(body: str) -> tuple[int, str]:
            (repo / "music/briefs/t.md").write_text(body, encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["--repo", str(repo), "--briefs", "music/briefs/t.md"])
            return rc, buf.getvalue()

        rc_good, _ = brief("Block (`music/registry.yaml` lines 3–5): export/stems.\n")
        rc_bad, out_bad = brief("Block (`music/registry.yaml` lines 2–5): export/stems.\n")
        rc_amb, out_amb = brief("See `thing.yaml` lines 1–1 for the setting.\n")
        rc_quote, out_quote = brief(quoted)
        rc_bare, out_bare = brief(bare)
        rc_unanchored, out_unanchored = brief(unanchored)
        # Card t_2f9b441c: a fence whose BODY carries a checker result line is a transcript too,
        # even when its introduction names no revision. The quoted citation targets the BLANK
        # line 2 of the referent, so pre-fix it was FAILed as a claim of the quoting brief.
        rc_grammar, out_grammar = brief(grammar)
        # The same blank line quoted inside a fence with NO checker result in its body is still
        # measured: a bare `PASS`/`FAIL` with no `check_` name is a code sample, not a transcript.
        rc_code, out_code = brief(code_sample)

    caught = [ln.strip() for ln in out_bad.splitlines() if "BLANK OPEN" in ln]
    skipped_amb = "ambiguous referent" in out_amb
    # Card t_8d6c40ac, both halves: the rev-anchored fence's quoted citation is SKIPPED and counted
    # in its own bucket, while the same blank line cited bare — and the same blank line quoted
    # inside an UNANCHORED fence — is still measured and still FAILs.
    caught_bare = [ln.strip() for ln in out_bare.splitlines() if "BLANK OPEN" in ln]
    caught_unanchored = [ln.strip() for ln in out_unanchored.splitlines() if "BLANK OPEN" in ln]
    quote_skipped = "quoted at a rev x1" in out_quote and "BLANK OPEN" not in out_quote
    # Card t_2f9b441c, both halves: the grammar fence's quoted citation is SKIPPED and counted in
    # its own bucket, while the same blank line quoted inside a fence with NO checker result in
    # its body is still measured and still FAILs.
    caught_grammar = [ln.strip() for ln in out_grammar.splitlines() if "BLANK OPEN" in ln]
    caught_code = [ln.strip() for ln in out_code.splitlines() if "BLANK OPEN" in ln]
    grammar_skipped = "quoted at a rev x1" in out_grammar and "BLANK OPEN" not in out_grammar
    # Regression, card t_e86c2110 (2026-10-16): the link-gap pattern used to nest a repeat inside a
    # repeat, so a gap that fails to match backtracked exponentially. `music/briefs/elemental-water.md`
    # aligns a trailing comment 23 spaces out inside a fenced transcript, and that made the whole
    # check stop finishing (>45 s on the one brief, >200 s on the repo). The gap must be REJECTED,
    # and rejected fast — the nested form this replaced needed 35 s on the 16-space case alone.
    t0 = time.perf_counter()
    gap_is_link = bool(LINK_RE.match(" " * 23 + "# "))
    gap_ms = (time.perf_counter() - t0) * 1000
    # The 12-space case is the fast-failing half of the same regression: the nested form needed
    # 0.27 s here, so a reintroduction fails this bound at once instead of hanging the suite.
    t0 = time.perf_counter()
    small_is_link = bool(LINK_RE.match(" " * 12 + "# "))
    small_ms = (time.perf_counter() - t0) * 1000
    gap_linear = not gap_is_link and gap_ms < 50 and not small_is_link and small_ms < 50
    ok = (rc_good == 0 and rc_bad == 1 and len(caught) == 1 and rc_amb == 0 and skipped_amb
          and rc_quote == 0 and quote_skipped
          and rc_bare == 1 and len(caught_bare) == 1
          and rc_unanchored == 1 and len(caught_unanchored) == 1
          # Card t_2f9b441c: a fence whose body carries a checker result line is a transcript too,
          # even when its intro names no revision; a bare `PASS`/`FAIL` with no `check_` name is a
          # code sample and is still measured.
          and rc_grammar == 0 and grammar_skipped
          and rc_code == 1 and len(caught_code) == 1
          and gap_linear)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_brief_line_refs: "
          f"correct-range rc={rc_good} (want 0), off-by-one rc={rc_bad} (want 1), "
          f"caught={len(caught)} (want 1), ambiguous-basename rc={rc_amb} (want 0, skipped), "
          f"aligned-comment gap {gap_ms:.3f} ms / 12-space {small_ms:.3f} ms "
          f"(want <50 each, not links: {not gap_is_link and not small_is_link})")
    print(f"  quoted-at-a-rev (card t_8d6c40ac): fence rc={rc_quote} (want 0, skipped: "
          f"{quote_skipped}), bare same-line rc={rc_bare} (want 1, caught={len(caught_bare)}), "
          f"unanchored fence rc={rc_unanchored} (want 1, caught={len(caught_unanchored)})")
    print(f"  quoted-at-a-rev grammar (card t_2f9b441c): grammar fence rc={rc_grammar} (want 0, "
          f"skipped: {grammar_skipped}), bare-result code sample rc={rc_code} (want 1, "
          f"caught={len(caught_code)})")
    for ln in caught:
        print(f"  (caught) {ln}")
    for ln in caught_bare:
        print(f"  (bare) {ln}")
    return 0 if ok else 1


def skip_summary(notes: list[str]) -> str:
    """Group skip notes into a one-line count per reason category."""
    buckets: dict[str, int] = {}
    for n in notes:
        reason = n.split("— ", 1)[-1]
        if reason.startswith("ambiguous"):
            cat = "ambiguous referent"
        elif reason.startswith("quoted at a rev"):
            cat = "quoted at a rev"
        elif "anchored to a revision" in reason:
            cat = "anchored to a rev/time"
        elif "outside the repo" in reason:
            cat = "path outside the repo"
        else:
            cat = "not in the worktree"
        buckets[cat] = buckets.get(cat, 0) + 1
    return ", ".join(f"{cat} x{n}" for cat, n in sorted(buckets.items()))


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Check the line citations a music brief makes.")
    ap.add_argument("--repo", default=str(here.parents[2]))
    ap.add_argument("--briefs", action="append", default=[], help="only these briefs")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the check fails on the incident shape and passes on a good one")
    ap.add_argument("--quiet-skips", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    tree = Tree(repo)
    briefs = tree.briefs()
    if args.briefs:
        want = {b.lstrip("./") for b in args.briefs}
        briefs = [b for b in briefs if b in want or any(b.endswith(w) for w in want)]
    if not briefs:
        print(f"FAIL check_brief_line_refs: no briefs matched under {tree.label()}")
        return 2

    failures: list[str] = []
    checked = skipped = 0
    notes: list[str] = []
    for rel in briefs:
        f, n, s, nt = check_brief(tree, rel)
        failures += f
        checked += n
        skipped += s
        notes += nt

    if failures:
        bad_briefs = sorted({f.strip().split(":")[0] for f in failures})
        print(f"FAIL check_brief_line_refs: {len(failures)} of {checked} cited line range(s) "
              f"in {len(briefs)} brief(s) do not hold in {tree.label()}")
        print("\n".join(failures))
        if not args.quiet_skips:
            print(f"  {checked - len(failures)} citation(s) OK; {skipped} skipped "
                  f"({skip_summary(notes)}) — a referent the check cannot resolve uniquely "
                  f"is never guessed at")
        print("  Cited: " + ", ".join(f"`{b}`" for b in bad_briefs)
              + " — each range must be corrected in the citing brief, and a brief that records "
                "its own sha256 must record the supersession in the same commit.")
        return 1

    print(f"PASS check_brief_line_refs: {checked} cited line range(s) across {len(briefs)} "
          f"brief(s) resolve and hold in {tree.label()}")
    if not args.quiet_skips and skipped:
        print(f"  {skipped} citation(s) skipped ({skip_summary(notes)}); the check never "
              f"guesses a referent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
