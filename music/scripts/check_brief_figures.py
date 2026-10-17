#!/usr/bin/env python3
"""check_brief_figures — recompute the evidence figures a brief cites, and check their UNIT.

WHY THIS EXISTS
---------------
A brief in this lane IS the evidence artifact for a genre: every figure in it must be
a real command output. Nothing recomputed those figures, so a wrong number could sit
in a committed brief indefinitely. Nothing checked their UNIT at all.

INCIDENT (2026-10-16, card t_47491ec0, recorded by the duplicate t_4187b092)
----------------------------------------------------------------------------
`music/briefs/commentary-beds.md` cites the prompt template as "4133 B" twice (§1
registry table, §10 provenance). Measured: `music/prompts/commentary-beds.md` is
4159 bytes / 4133 characters. 4133 is the CHARACTER count — the unit label is wrong
by 26 bytes. A convention error, so a reader trusting "B" gets the wrong artifact size.

INCIDENT (2026-10-16, card t_96821eed, recorded by the duplicate t_abaa7e2d)
---------------------------------------------------------------------------
`music/briefs/anime-opening.md` §1 said the style block "measures 754 chars". Measured
at `ade6e87`: `awk '/^```text/{f=1;next} /^```/{if(f)exit} f' music/prompts/anime-opening.md
| tr -d '\\n' | wc -c` prints 754 — but `wc -c` counts BYTES. The block is 752
characters; it holds one 3-byte em dash, so 752 + 2 = 754 bytes. Corrected in place to
"754 bytes / 752 characters".

Same root cause both times — `wc -c` prints bytes and this lane's prose calls its output
"chars" — and the two errors point in OPPOSITE directions (chars labelled B; bytes
labelled chars), so it is a missing unit check, not one copy slip. A check that only
tests "does the number appear somewhere" passes both. This check is strict about units.
A third instance of the same class was live when this check was written: the chiptune-8bit
brief's §8.4 figure (844 chars) was withdrawn by card t_05b640f6.

WHAT IT DOES
------------
For every `music/briefs/**/*.md`, it finds figures written as an integer plus a unit
token (`chars`, `characters`, `bytes`, `B`, `lines`) and recomputes each one whose
referent THIS REPO can prove. Referents it can prove:

  * a named file's size (bytes) or length (characters, lines);
  * the first ```` ```text ```` block of a named file — the lane's own style-field
    measurement, taken with the same rule as `music/prompts/validate_templates.py:67`
    (fenced block, `.strip()`);
  * a named file at a named revision, when the line names one.

Out of scope by design: figures only cluster state can prove (kubectl output, journal
lines, images quoted in a brief). Those are counted and reported as skipped.

LIVE REFERENTS — a figure against a live file must be anchored, or dropped
-------------------------------------------------------------------------
INCIDENT (2026-10-16, card t_f7889dd6, found while closing t_6599927d)

Seven briefs cited `brain/playbooks/music-lane-architecture.md`'s size as a LIVE figure —
six at "34,328 B", `chill-lounge.md` also "596 lines" — and the class pre-dated any single
commit: at HEAD~2 the doc already measured 35 169 B / 605 lines against the same claim. So
every edit to the doc turned this check red lane-wide, and nothing could see the stale claim
until after the edit had landed. `check_brief_drift.py` already draws the right line for a
count — "an anchored historical count is a fact, an unanchored one is a claim" (its rule 3) —
but the figure class had no such escape hatch. The doc states the rule itself, in its own
§14: "Cite this file's sections, not its byte size or line count: it is live, so those
figures age" — and nothing enforced it.

Two admissible shapes, both recorded here:

  * DROP the figure and cite the doc's own §s. A path plus a section number cannot age.
    `705043f` (card `t_0fbdfa34`) rewrote 23 sites this way.
  * ANCHOR it to the revision it is true at — `at `6b24a52`: 34 328 B` — which this check
    re-verifies against that revision's blob. `music/briefs/jungle-dnb.md:1369` is the live
    example: `6b24a52`'s doc measures exactly 596 lines / 34 328 B.

A figure against a LIVE referent with no anchor on its line now FAILS, whether or not its
value matches the worktree today: a live copy that is correct this minute still goes stale on
the next edit, and that is the defect. A CLOCK-anchored figure is a dated record this repo
cannot recompute, so it is SKIPPED and printed as such, never guessed at — the same line
`check_brief_drift.py` rule 3 draws.

Rules (kept deliberately narrow, so the check is signal and not noise)
---------------------------------------------------------------------
1. A figure is recomputed only when its artifact is named EARLIER ON THE SAME LINE
   ("`<path>` — 4448 B", "`<path>` (4159 bytes, resolves)"). A path named after the
   figure, or on another line, is left alone.
2. A path token may be repo-root relative (`music/prompts/x.md`) or `music/` relative
   (`prompts/x.md`) — both shapes are used in this lane.
3. The referent is the FIRST ```` ```text ```` block when the claim's own clause speaks
   of a style block / style field / caption; otherwise the whole file. When a line claims
   several style-field sizes, the Nth claim maps to the Nth ```` ```text ```` block.
4. `A/B unit` (tight) is a claim (A) against a capacity (B) — only A is checked.
   `A / B unit` (spaced) is two claims, mapped in order.
5. A numeric that is part of an identifier (`YuE2-3B`) is not a figure.
6. Counting conventions are admitted as a FAMILY, because the lane uses both: bytes or
   characters, including or excluding a trailing newline. A claim fails when the value
   matches NEITHER its own unit's family (value not reproducible) OR when it matches the
   OTHER unit's family (UNIT MISLABEL — the two incidents above).
7. A LIVE referent (`LIVE_REFERENTS` below: a file whose own content declares it live) may
   not carry an unanchored figure — see LIVE REFERENTS above. An anchored figure is history:
   it is re-verified when the anchor is a revision, and skipped when it is a clock stamp.

Exit codes: 0 = every recomputed figure matches, 1 = at least one mismatch, 2 = usage error.

Usage:
  /usr/bin/python3 music/scripts/check_brief_figures.py [--repo DIR] [--rev REV]
                                                        [--briefs PATH]... [--quiet-skips]

  --rev REV     check the briefs AND their referents as of REV (via `git show`), so a
                pre-correction revision can be tested:
                  /usr/bin/python3 music/scripts/check_brief_figures.py \\
                      --rev ade6e87 --briefs music/briefs/anime-opening.md
  --briefs PATH only check these briefs (repeatable; repo-relative).
  --selftest    inject the incident into a throwaway repo and prove the check fails.

Related checks (deliberately not duplicated here)
-------------------------------------------------
  * `music/scripts/check_prompt_style_counts.py` — the TEMPLATE side of this budget: a
    `## Style field` heading's own `N/1000 chars` claim against its block. It states that
    it checks no briefs; this script is the brief side.
  * `music/scripts/check_stage_scripts.py`, `music/scripts/check_brief_paths.py` — do the
    cited paths exist / resolve. This one checks the FIGURES.

Run with /usr/bin/python3: the shell's bare python3 in a worker shell is the Hermes
bundled interpreter. (This script needs no PyYAML — see t_d3b9e218 — but a uniform
interpreter keeps the lane's checks reproducible.)

cited: t_55379aba (this check), t_47491ec0/t_4187b092 (incident 1), t_96821eed/t_abaa7e2d
(incident 2), t_05b640f6 (incident 3), t_b16b9046 (same gap shape: no gate matrix runner),
t_f7889dd6 (the live-referent class and rule 7), t_0fbdfa34/705043f (the brief-side fix).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

BRIEF_GLOB = "music/briefs/**/*.md"

# A figure: an integer (optionally thousands-separated with a space, NBSP, thin space or
# comma) plus a unit. The lookbehind keeps numbers that are part of an identifier out
# (`YuE2-3B`, `acestep-5Hz-lm-4B`), and `\b` keeps `B` in `BPM` out.
_NUM = r"\d+(?:[ \u00a0\u202f,]\d{3})*"
_UNIT = r"chars?|characters?|bytes?|B|lines?"
CLAIM_RE = re.compile(rf"(?<![A-Za-z0-9_.\-])({_NUM})\s*({_UNIT})\b")
# `585/1000 chars` (tight): 585 is the measure, 1000 the capacity.
PAIR_TIGHT_RE = re.compile(rf"(?<![A-Za-z0-9_.\-])({_NUM})\s*/\s*({_NUM})\s*({_UNIT})\b")
# `420 / 422 chars` (spaced): two measures, one unit, in order.
PAIR_SPACED_RE = re.compile(rf"(?<![A-Za-z0-9_.\-])({_NUM})\s+/\s+({_NUM})\s*({_UNIT})\b")
# A revision token: `ade6e87`, `4bb1ea6` — a brief may measure an artifact at an older commit.
REV_RE = re.compile(r"`([0-9a-f]{7,40})`")

# Referents whose OWN content declares them live: they change whenever this lane is edited.
# `brain/playbooks/music-lane-architecture.md` §14 says it in its own words — "Cite this
# file's sections, not its byte size or line count: it is live, so those figures age" — and
# nothing enforced it, so seven briefs froze the doc and this check went red lane-wide on
# every doc edit (card t_f7889dd6; the briefs were fixed at `705043f` by card `t_0fbdfa34`).
LIVE_REFERENTS = frozenset({"brain/playbooks/music-lane-architecture.md"})

# An ANCHOR turns a figure from a claim about now into history: a clock or date stamp on the
# same line, or a revision token — and the revision must RESOLVE, because an anchor nobody can
# verify is not an anchor. The convention is `check_brief_drift.py` rule 3's, adopted rather
# than invented, so this lane draws the line between claim and history in one way only.
_CLOCK_RE = re.compile(r"(?:\b20\d\d-\d\d-\d\d\b|\b\d{1,2}:\d{2}\b|\bCDT\b|\bCST\b"
                       r"|\bUTC\b|as of\b|when written\b)", re.IGNORECASE)

# Path tokens: backticked, or bare with a known repo prefix.
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
_BARE_RE = re.compile(r"(?<![\w/.-])((?:music|brain|performance|scripts)/[A-Za-z0-9_./-]+"
                      r"\.[A-Za-z0-9]{1,6})")

# The claim's own clause speaks of a style field / block / caption -> the referent is the
# file's first ```text block, not the whole file.
_BLOCK_WORDS = ("style block", "style field", "style caption", "text block", "```text",
                "caption")
_BLOCK_CTX = 90          # chars of preceding line text searched for a block word
_PAIR_WINDOW = 60        # max chars between the artifact token and its figure


def _plain(tok: str) -> str:
    return tok.strip().strip("`").rstrip(".,;:)")

# --------------------------------------------------------------------------
# source trees: the working tree, or a git revision
# --------------------------------------------------------------------------


class Tree:
    """Read-only view of the lane repo: the worktree, or a revision of it."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo

    def read_bytes(self, rel: str) -> bytes | None:
        path = self.repo / rel
        if not path.is_file():
            return None
        return path.read_bytes()

    def exists(self, rel: str) -> bool:
        return (self.repo / rel).is_file()

    def briefs(self) -> list[str]:
        return sorted(
            str(p.relative_to(self.repo))
            for p in self.repo.glob(BRIEF_GLOB)
            if p.is_file()
        )

    def label(self) -> str:
        return f"worktree {self.repo}"


class RevTree(Tree):
    """Same interface, reading blobs out of a commit instead of the worktree."""

    def __init__(self, repo: Path, rev: str) -> None:
        super().__init__(repo)
        self.rev = rev
        out = self._git("ls-tree", "-r", "--name-only", rev)
        if not out.strip():
            raise SystemExit(f"FATAL: {rev} is not a revision in {repo}")
        self._files = set(out.splitlines())

    def _git(self, *args: str) -> str:
        res = subprocess.run(["git", "-C", str(self.repo), *args],
                             capture_output=True, text=True, check=False)
        if res.returncode != 0 and args[0] != "ls-tree":
            raise SystemExit(f"FATAL: git {' '.join(args)} failed: {res.stderr.strip()}")
        return res.stdout

    def read_bytes(self, rel: str) -> bytes | None:
        if rel not in self._files:
            return None
        res = subprocess.run(["git", "-C", str(self.repo), "show", f"{self.rev}:{rel}"],
                             capture_output=True, check=False)
        return res.stdout if res.returncode == 0 else None

    def exists(self, rel: str) -> bool:
        return rel in self._files

    def briefs(self) -> list[str]:
        return sorted(f for f in self._files
                      if f.startswith("music/briefs/") and f.endswith(".md"))

    def label(self) -> str:
        return f"revision {self.rev}"


# --------------------------------------------------------------------------
# measurement
# --------------------------------------------------------------------------


class Measures:
    """Every counting convention this lane actually uses, per referent.

    chars: characters.  bytes: utf-8 octets.  lines: line count.
    The trailing newline is included and excluded as separate variants, because the
    lane's briefs use both (chiptune-8bit §8.4 counts 568 = 567 + newline; the
    style-field extractor `validate_templates.py` strips).
    """

    def __init__(self, what: str, raw: bytes) -> None:
        self.what = what
        self.raw = raw
        self.binary = False
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            # A binary artifact (mp4, png): size is provable, length is not.
            text = None
            self.binary = True
        self.chars: set[int] = set()
        self.bytes: set[int] = set()
        self.lines: set[int] = set()
        b = {len(raw)}
        if raw.endswith(b"\n"):
            b.add(len(raw) - 1)
        if raw.strip():
            b.add(len(raw.strip()))
        self.bytes |= b
        if text is None:
            return
        c = {len(text)}
        if text.endswith("\n"):
            c.add(len(text) - 1)
        if text.strip():
            c.add(len(text.strip()))
        self.chars |= c
        self.lines |= {text.count("\n") + (0 if text.endswith("\n") else 1),
                       len(text.splitlines())}

    def _fam(self, unit: str) -> set[int]:
        u = unit.lower()
        if u in ("b", "byte", "bytes"):
            return self.bytes
        if u in ("line", "lines"):
            return self.lines
        return self.chars

    def verdict(self, value: int, unit: str) -> str:
        """'ok' | 'unit' (value is the OTHER unit's count) | 'value' (reproducible by neither)."""
        if self.binary and unit.lower() in ("chars", "char", "characters", "character"):
            return "value" if value not in self.bytes else "ok"
        if value in self._fam(unit):
            return "ok"
        other = "bytes" if unit.lower() not in ("b", "byte", "bytes") else "chars"
        if value in self._fam(other):
            return "unit"
        return "value"

    def measured_for(self, unit: str) -> str:
        if self.binary:
            return f"{sorted(self.bytes)[-1]} bytes (binary; no character count)"
        if unit.lower() in ("b", "byte", "bytes"):
            return f"{max(self.bytes)} bytes / {max(self.chars)} characters"
        if unit.lower() in ("line", "lines"):
            return f"{max(self.lines)} lines"
        return f"{max(self.chars)} characters / {max(self.bytes)} bytes"


def git_blob(repo: Path, rev: str, rel: str) -> bytes | None:
    """The bytes of `rel` at revision `rev` (None when the path is not in that tree)."""
    res = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"],
                         capture_output=True, check=False)
    return res.stdout if res.returncode == 0 else None


def text_blocks(raw: bytes) -> list[bytes]:
    """Every ```` ```text ```` fenced region of a file, in order, as the file carries it —
    each region INCLUDING the newline that closes its last line, so both the brief's
    convention ("567 chars / 568 bytes") and the extractor's
    (`music/prompts/validate_templates.py:67`, `.strip()` -> 567) are admissible
    measures of the same region."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return [(m.group(1) + "\n").encode()
            for m in re.finditer(r"```text\n(.*?)\n```", text, re.DOTALL)]


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------


def resolve_path(tree: Tree, tok: str) -> str | None:
    """Resolve a cited path token to a repo-relative file. Two shapes are in use:
    repo-root relative (`music/prompts/x.md`) and relative to `music/` (`prompts/x.md`)."""
    for cand in (tok, f"music/{tok}"):
        if tree.exists(cand):
            return cand
    return None


def line_referents(tree: Tree, line: str) -> list[tuple[int, int, str]]:
    """All (start, end, repo-rel path) artifact tokens named on this line, in order."""
    found: dict[int, tuple[int, int, str]] = {}
    # Backticked tokens that are themselves a path (the `prompts/x.md` shape needs this).
    for m in _BACKTICK_RE.finditer(line):
        inner = _plain(m.group(1))
        if " " in inner or "/" not in inner:
            continue
        rel = resolve_path(tree, inner)
        if rel:
            found[m.start(1)] = (m.start(1), m.start(1) + len(m.group(1)), rel)
    # Bare path-shaped tokens with a known repo prefix.
    for m in _BARE_RE.finditer(line):
        rel = resolve_path(tree, _plain(m.group(1)))
        if rel and not any(s <= m.start(1) < e for s, e, _ in found.values()):
            found[m.start(1)] = (m.start(1), m.end(1), rel)
    return [found[k] for k in sorted(found)]


def claims_on_line(line: str) -> list[dict]:
    """Every figure on the line, in order, with the capacity of a tight `A/B` pair dropped.

    Shapes handled: `4159 bytes`, `4 032 B`, `420 / 422 chars` (two measures),
    `585/1000 chars` (measure + capacity — 1000 is not a measurement).
    """
    used: list[tuple[int, int]] = []

    def taken(s: int, e: int) -> bool:
        return any(s < te and ts < e for ts, te in used)

    def claim(value: str, unit: str, span: tuple[int, int], text: str) -> dict:
        used.append(span)
        return {"start": span[0], "end": span[1],
                "value": int(re.sub(r"[^\d]", "", value)), "unit": unit, "text": text}

    out: list[dict] = []
    for m in PAIR_SPACED_RE.finditer(line):
        out.append(claim(m.group(1), m.group(3), m.span(1), m.group(0).strip()))
        out.append(claim(m.group(2), m.group(3), m.span(2), m.group(2) + " " + m.group(3)))
    for m in PAIR_TIGHT_RE.finditer(line):
        if taken(*m.span(1)):
            continue
        out.append(claim(m.group(1), m.group(3), m.span(1), m.group(0).strip()))
        used.append(m.span(2))                       # the capacity is not a figure
    for m in CLAIM_RE.finditer(line):
        if taken(*m.span()):
            continue
        out.append(claim(m.group(1), m.group(2), m.span(), m.group(0).strip()))
    return sorted(out, key=lambda c: c["start"])


def check_brief(tree: Tree, rel: str) -> tuple[list[str], int, int]:
    """Return (failure lines, recomputed count, skipped count)."""
    raw = tree.read_bytes(rel)
    if raw is None:
        return ([f"  {rel}:1  MISSING from {tree.label()}"], 0, 0)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ([f"  {rel}:1  not utf-8"], 0, 0)

    failures: list[str] = []
    recomputed = 0
    skipped = 0
    blocks_cache: dict[str, list[Measures]] = {}
    rev_at: dict[str, str | None] = {}

    def at_rev(rev: str) -> bool:
        """True when `rev` names a real commit (cached)."""
        if rev not in rev_at:
            res = subprocess.run(["git", "-C", str(tree.repo), "rev-parse", "--verify",
                                  "--quiet", f"{rev}^{{commit}}"],
                                 capture_output=True, text=True, check=False)
            rev_at[rev] = res.stdout.strip() if res.returncode == 0 else None
        return rev_at[rev] is not None

    for lineno, line in enumerate(text.splitlines(), 1):
        claims = claims_on_line(line)
        if not claims:
            continue
        refs = line_referents(tree, line)
        per_unit: dict[str, int] = {}
        for claim in claims:
            path = None
            path_end = 0
            for start, end, cand in refs:            # artifact must be named BEFORE the figure
                if start < claim["start"] and 0 <= claim["start"] - end <= _PAIR_WINDOW:
                    path, path_end = cand, end
            if path is None:
                skipped += 1
                continue
            # A revision named between the artifact and the figure measures the OLD blob
            # (`anime-ending.md` §337: "one commit before this pass (`4bb1ea6`) ... 16549 B").
            rev = None
            for m in REV_RE.finditer(line[:claim["start"]]):
                if m.end() >= path_end and at_rev(m.group(1)):
                    rev = m.group(1)
            # Rule 7 / LIVE REFERENTS: a live referent may not carry an unanchored figure.
            # Enforced BEFORE the value is recomputed, because the defect is the unanchored
            # claim, not the number — a live copy that matches today still ages on the very
            # next edit of the file it quotes.
            if path in LIVE_REFERENTS and rev is None:
                alt = next((m.group(1) for m in REV_RE.finditer(line)
                            if at_rev(m.group(1))), None)
                if alt is not None:
                    rev = alt          # a revision named anywhere on the line still measures it
                elif _CLOCK_RE.search(line):
                    skipped += 1       # a dated record: history this repo cannot recompute
                    continue
                else:
                    recomputed += 1
                    failures.append(
                        f'  {rel}:{lineno}  claimed "{claim["value"]:,} {claim["unit"]}"  '
                        f'referent {path}  [VOLATILE REFERENCE: {path} is live (§14) — its '
                        f'byte size and line count are not citable; drop the figure and cite '
                        f'its §s, or anchor it to the revision it is true at '
                        f'(`at <rev>: {claim["value"]:,} {claim["unit"]}`)]')
                    continue
            ctx = line[max(0, claim["start"] - _BLOCK_CTX):claim["start"]].lower()
            unit_key = "bytes" if claim["unit"].lower() in ("b", "byte", "bytes") else (
                "lines" if claim["unit"].lower() in ("line", "lines") else "chars")
            use_block = any(w in ctx for w in _BLOCK_WORDS)
            if use_block:
                cache_key = f"{rev or ''}:{path}"
                if cache_key not in blocks_cache:
                    data = tree.read_bytes(path) if rev is None else git_blob(tree.repo, rev, path)
                    blocks_cache[cache_key] = [
                        Measures(f"```text block #{i + 1} of {path}", blk)
                        for i, blk in enumerate(text_blocks(data or b""))
                    ]
                blocks = blocks_cache[cache_key]
                idx = per_unit.get(unit_key, 0)
                per_unit[unit_key] = idx + 1
                if not blocks or idx >= len(blocks):
                    skipped += 1
                    continue
                m = blocks[idx]
                referent = m.what
            else:
                data = tree.read_bytes(path) if rev is None else git_blob(tree.repo, rev, path)
                if data is None:
                    skipped += 1
                    continue
                m = Measures(path, data)
                referent = path + (f" @ {rev}" if rev else "")
            if m.binary and claim["unit"].lower() not in ("b", "byte", "bytes", "line", "lines"):
                skipped += 1        # a character count of a binary artifact is not provable
                continue
            recomputed += 1
            verdict = m.verdict(claim["value"], claim["unit"])
            if verdict == "ok":
                continue
            here = f"{rel}:{lineno}"
            claimed = f'{claim["value"]:,} {claim["unit"]}'
            measured = m.measured_for(claim["unit"])
            if verdict == "unit":
                note = (f'UNIT MISLABEL: {claim["value"]:,} is the '
                        f'{"character" if claim["unit"].lower() in ("b", "byte", "bytes") else "byte"} '
                        f'count of {referent}, not its '
                        f'{"byte" if claim["unit"].lower() in ("b", "byte", "bytes") else "character"} '
                        f'count')
            else:
                note = ("NOT REPRODUCIBLE: no counting convention of this referent yields "
                        f'{claim["value"]:,}')
            failures.append(f'  {here}  claimed "{claimed}"  measured {measured}'
                            f'  referent {referent}  [{note}]')
    return failures, recomputed, skipped


def selftest() -> int:
    """Prove the check can fail: inject every incident shape into a throwaway repo.

    A correct brief must exit 0; a brief whose whole-file claim carries the character
    count as "B" AND whose style-block claim carries the byte count as "chars" (the two
    incident directions) must exit 1 with two UNIT MISLABEL findings.

    The LIVE-REFERENT rule (card t_f7889dd6) is proved the same way. The probe doc is
    committed at v1 and then edited in the worktree to v2, so ONE value is simultaneously
    true at a revision and stale live — which is exactly the briefs' position when the doc
    moved under them: an unanchored claim must exit 1 with a VOLATILE REFERENCE finding,
    the same claim anchored to the revision it is true at must exit 0, and a clock-stamped
    claim must be skipped as history rather than guessed at.
    """
    import contextlib
    import io
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "music/prompts").mkdir(parents=True)
        (repo / "music/briefs").mkdir(parents=True)
        (repo / "brain/playbooks").mkdir(parents=True)
        prompt = ('# p\n\n## Style field (paste into Suno "Styles", 28/1000 chars)\n\n'
                  '```text\nwarm lo-fi bed — no melody\n```\n')
        (repo / "music/prompts/p.md").write_text(prompt, encoding="utf-8")
        block = "warm lo-fi bed — no melody"
        f_bytes, f_chars = len(prompt.encode()), len(prompt)
        b_bytes, b_chars = len(block.encode()), len(block)

        # The live doc: v1 committed, v2 in the worktree.
        doc = repo / "brain/playbooks/music-lane-architecture.md"
        doc_v1 = "# doc\n\nThe doc is live, so its figures age.\n"
        doc.write_text(doc_v1, encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=False, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=False, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-q", "-m", "v1"], check=False, capture_output=True)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=8", "HEAD"],
                              capture_output=True, text=True, check=False).stdout.strip()
        doc.write_text(doc_v1 + "Cite its sections, not its size.\n", encoding="utf-8")
        v1_bytes = len(doc_v1.encode())
        if not head or len(doc.read_bytes()) == v1_bytes:
            print("SELFTEST FAIL check_brief_figures: could not build the live-referent probe "
                  "(no revision, or v2 == v1)")
            return 1
        LIVE = "brain/playbooks/music-lane-architecture.md"

        def brief(body: str) -> tuple[int, str]:
            (repo / "music/briefs/t.md").write_text(body, encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["--repo", str(repo), "--briefs", "music/briefs/t.md"])
            return rc, buf.getvalue()

        rc_good, _ = brief(
            f"# brief\n\n| Prompt template | `music/prompts/p.md` ({f_bytes} B, resolves) |\n"
            f"Style: `` `music/prompts/p.md` `` — style block is {b_bytes} bytes / "
            f"{b_chars} characters\n")
        rc_bad, out_bad = brief(
            f"# brief\n\n| Prompt template | `music/prompts/p.md` ({f_chars} B, resolves) |\n"
            f"Style: `` `music/prompts/p.md` `` — style block is {b_bytes} chars\n")
        rc_live, out_live = brief(
            f"# brief\n\nThe architecture doc `{LIVE}` is {v1_bytes} B.\n")
        rc_anch, _ = brief(
            f"# brief\n\nThe architecture doc `{LIVE}` at `{head}` is {v1_bytes} B.\n")
        rc_clk, _ = brief(
            f"# brief\n\nThe architecture doc `{LIVE}` measured {v1_bytes} B at 15:31 CDT.\n")

    mislabels = out_bad.count("UNIT MISLABEL")
    volatiles = out_live.count("VOLATILE REFERENCE")
    ok = (rc_good == 0 and rc_bad == 1 and mislabels == 2
          and rc_live == 1 and volatiles == 1 and rc_anch == 0 and rc_clk == 0)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_brief_figures: "
          f"correct-claims rc={rc_good} (want 0), flipped-units rc={rc_bad} (want 1), "
          f"unit mislabels={mislabels} (want 2), live-unanchored rc={rc_live} (want 1) with "
          f"{volatiles} volatile finding(s) (want 1), live-rev-anchored rc={rc_anch} (want 0), "
          f"live-clock-anchored rc={rc_clk} (want 0, skipped as history)")
    for out, marker in ((out_bad, "MISLABEL"), (out_live, "VOLATILE")):
        caught = [ln.strip() for ln in out.splitlines() if marker in ln]
        if caught:
            print("  (caught) " + "\n  (caught) ".join(caught))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Recompute the figures a music brief cites.")
    ap.add_argument("--repo", default=str(here.parents[2]))
    ap.add_argument("--rev", default=None, help="check this revision's briefs and referents")
    ap.add_argument("--briefs", action="append", default=[], help="only these briefs")
    ap.add_argument("--selftest", action="store_true",
                    help="inject the incident into a throwaway repo and prove the check fails")
    ap.add_argument("--quiet-skips", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    try:
        tree: Tree = RevTree(repo, args.rev) if args.rev else Tree(repo)
    except SystemExit as exc:
        print(exc)
        return 2

    briefs = tree.briefs()
    if args.briefs:
        want = {b.lstrip("./") for b in args.briefs}
        briefs = [b for b in briefs if b in want or any(b.endswith(w) for w in want)]
    if not briefs:
        print(f"FAIL check_brief_figures: no briefs matched under {tree.label()}")
        return 2

    failures: list[str] = []
    recomputed = skipped = 0
    for rel in briefs:
        f, n, s = check_brief(tree, rel)
        failures += f
        recomputed += n
        skipped += s

    if failures:
        print(f"FAIL check_brief_figures: {len(failures)} of {recomputed} recomputed "
              f"figure(s) in {len(briefs)} brief(s) do not match {tree.label()}")
        print("\n".join(failures))
        if not args.quiet_skips:
            print(f"  {recomputed - len(failures)} recomputed figure(s) OK; {skipped} "
                  f"figure(s) skipped (referent the repo cannot prove: cluster state, "
                  f"or the artifact is named after the figure)")
        print("  cited: t_47491ec0/t_4187b092 (commentary-beds \"4133 B\"), "
              "t_96821eed/t_abaa7e2d (anime-opening \"754 chars\"), t_05b640f6 (chiptune 844)")
        print("  Fix: correct the figure in the citing brief. Do NOT edit an artifact to "
              "match a stale figure, and do NOT edit a brief that carries a recorded "
              "sha256 without recording the supersession in the same commit.")
        print("  A LIVE referent is the exception — do not correct its figure: drop the size "
              "and cite the file's own §s, or anchor it to the revision it is true at. A "
              "stamped line is history and is skipped; an unanchored present tense is a "
              "claim and fails (§14 of brain/playbooks/music-lane-architecture.md, rule 7).")
        return 1

    print(f"PASS check_brief_figures: {recomputed} recomputed figure(s) across "
          f"{len(briefs)} brief(s) match {tree.label()}"
          + ("" if args.quiet_skips else f" ({skipped} skipped: referent not repo-provable)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
