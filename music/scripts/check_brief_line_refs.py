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


def check_brief(tree: Tree, rel: str) -> tuple[list[str], int, int, list[str]]:
    """Return (failures, checked, skipped, skip notes)."""
    text = tree.read(rel)
    if text is None:
        return ([f"  {rel}:1  MISSING from {tree.label()}"], 0, 0, [])
    failures: list[str] = []
    checked = skipped = 0
    notes: list[str] = []
    cache: dict[str, list[str]] = {}

    def src(path: str) -> list[str]:
        if path not in cache:
            cache[path] = (tree.read(path) or "").splitlines()
        return cache[path]

    for lineno, line in enumerate(text.splitlines(), 1):
        anchored = bool(ANCHORED.search(line))
        for tok, a, b, syntax in citations(line):
            if anchored:
                skipped += 1
                notes.append(f"  {rel}:{lineno}  skipped `{syntax}` — anchored to a revision "
                             f"or a clock time (a historical fact, not a claim about now)")
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

    caught = [ln.strip() for ln in out_bad.splitlines() if "BLANK OPEN" in ln]
    skipped_amb = "ambiguous referent" in out_amb
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
          and gap_linear)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_brief_line_refs: "
          f"correct-range rc={rc_good} (want 0), off-by-one rc={rc_bad} (want 1), "
          f"caught={len(caught)} (want 1), ambiguous-basename rc={rc_amb} (want 0, skipped), "
          f"aligned-comment gap {gap_ms:.3f} ms / 12-space {small_ms:.3f} ms "
          f"(want <50 each, not links: {not gap_is_link and not small_is_link})")
    for ln in caught:
        print(f"  (caught) {ln}")
    return 0 if ok else 1


def skip_summary(notes: list[str]) -> str:
    """Group skip notes into a one-line count per reason category."""
    buckets: dict[str, int] = {}
    for n in notes:
        reason = n.split("— ", 1)[-1]
        if reason.startswith("ambiguous"):
            cat = "ambiguous referent"
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
