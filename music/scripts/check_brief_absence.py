#!/usr/bin/env python3
"""check_brief_absence — FAIL when a brief makes a LIVE claim that a repo path is ABSENT
from this checkout while the path exists.

WHY THIS EXISTS
---------------
INCIDENT (2026-10-16, card t_752f02a8, `music/briefs/activist.md` §8)

The brief recorded, correctly when it was written:

    `suno-gen.py` is **not in this checkout** — `find /home/j_kro -name 'suno-gen.py'`
    returns zero hits — but it is on `origin/main` ...

Then the diverged checkout was reconciled (card t_8a715681, commit `ab33ad1` at 14:23) and
`music/suno-gen.py` (42652 B) landed in the tree. The sentence stayed in a committed brief
for hours, still asserting an absence a reader could disprove with one `ls`. Nothing in the
standing checks could see it: `check_brief_figures.py` wants a figure with a UNIT beside a
named file, `check_brief_drift.py` wants a divergence or census count, and this is neither —
it is a present-tense claim about whether a file exists.

MERGE (2026-10-16, card t_4612d213) — this file is the single survivor
---------------------------------------------------------------------
Two checks for this class landed seven minutes apart, both on `main`:

    check_brief_absences.py (plural)  15:59, card t_9dfa74d9, 6 673 B, `--repo` only
    check_brief_absence.py (singular) 16:06, card t_752f02a8, 12 702 B, --repo/--briefs/--rev/--selftest

Neither was a superset, and they returned CONTRADICTORY verdicts on a correct brief: on
`activist.md` the plural check reported five hits that are all false positives (measured
2026-10-16T16:1x CDT), because it judged a single LINE while the claims it hit were
paragraph-anchored records, quoted check output and a stated rule. The plural check is
deleted in the same commit as this merge, so no caller can pick the wrong one.

PROCESS LESSON (the root cause of the duplication)
--------------------------------------------------
The second check was written without listing the directory first. Before adding a check,
run `ls music/scripts/` and read the names. Both files were `check_brief_absence*`.

WHAT COUNTS AS A CLAIM — seven rules, each measured against this lane's briefs
------------------------------------------------------------------------------
R1. PREDICATE. The union of the two checks' markers, matched after markdown emphasis is
    stripped (so `is **not in this checkout**` — the incident's own markup — matches):
    "is/are [genuinely] absent|missing", "does not exist", "do not exist", "not present",
    "no such file", "zero hits", "not in this checkout|working tree|tree|repo",
    "not on this machine".
R2. PRESENT TENSE. A past-tense or attributed predicate is a record, not a claim
    ("was ABSENT when this brief was written", "recorded this file ABSENT",
    "was reported absent"). Measured: `anime-ending.md:56`, `anime-opening.md:69`,
    `jungle-dnb.md:926`.
R3. NOT A QUOTATION. A predicate inside a fenced code block, inside a quoted span, or on a
    line matching `<path>:<n>  claims ... is absent` is somebody's output, not a claim.
    Measured: `activist.md:1021` (this check's own fail-before output, fenced at §14.3),
    `elemental-fire.md:910` (a quoted old claim in a correction row), `elemental-water.md:963`.
R4. NOT A RULE. A sentence that STATES the rule ("no brief may claim a repo path is ABSENT
    from this checkout while the path exists") is skipped. Measured: `activist.md:1034`.
R5. NOT A PASS RECORD. Any paragraph under a pass-record heading is a record. This lane's
    briefs end with appended pass sections; their headings are the stamp for everything under
    them: "verification pass", "surviving-card pass", "duplicate-card", "aged live counts",
    "citation-sweep", "code-prose census", "pass record". The singular check's own docstring
    already drew this line ("Sections §12+ of these briefs are pass records"); this rule makes
    it structural instead of numeric, because the numbering is NOT consistent between briefs
    (elemental-water's §14 is "Provenance", its pass is §16).
R6. NOT A HISTORY PARAGRAPH (paragraph-level, not line-level). A paragraph carrying
    `SUPERSEDED`, "was true when", "measurement time", "when this brief was written", or a
    date+clock / measured-at revision anchor is quoting a past instant. This is the rule the
    plural check lacked: it judged `activist.md:864` line by line and so missed that the
    paragraph is a record (`SUPERSEDED (§14)` and the measured date sit two lines below the
    sentence it hit). A card id is deliberately NOT a stamp — measured 2026-10-16: treating it
    as one dropped two real claims (see the comment on HISTORY_PHRASES).
R7. BINDING — the predicate must govern the path. A predicate binds to the nearest path NAMED
    BEFORE it on the same line. That is how these sentences actually read: "`suno-gen.py` is
    **not in this checkout**", "… but that file is not in this checkout" (owner: the path named
    just before it). Paths that do NOT exist still take the binding, so a long row cannot lend
    its absence claim to a path it merely cites earlier.
    Measured false positives this rule kills:
      * `elemental-water.md:779` — "`butler` and `~/.hermes/vault/itch_io_key` are still absent
        (§10); `music/assets/pack.py` exists". The absence governs the vault key; pack.py is
        named after it and is asserted present.
      * `jungle-dnb.md:765` — "one with it `absent`, both measured with
        `music/rubrics/measure.py`". `absent` governs `style_weight`.
      * `elemental-earth.md:737` — a stage-plan row that claims `music/mix/master.py` (which
        really is absent, measured: no `music/mix/` dir) is absent, while citing
        `music/gates/gate_loudness.py` earlier in the same row. The binding is master.py, so
        the existing gate file is not flagged.
      * `jungle-dnb.md:903` — a handoff row claiming the playbook does not exist, which also
        names `lanes.yaml` / `autonomy.yaml` as files that CITE it. Those two exist and must
        not be flagged; only the playbook is.
    It must KEEP the genuine claims, including table rows where the path and its verdict sit in
    different cells: `jungle-dnb.md:359` before its correction was
    "| B — Suno CDP … | `music/suno-gen.py` | **NO — the file does not exist in this tree.**".
    A row that also asserts the token's path is PRESENT/exists is a correction record and is
    skipped.
    KNOWN LIMIT (measured, not hidden): binding is same-line, and only backwards. A claim whose
    path and predicate are split across a wrapped line break, or phrased forwards
    ("absent from this checkout: `X`"), is NOT caught. No live brief uses either shape
    (14 briefs, 41 absence predicate(s), measured 2026-10-16).

An object that is REMOTE ("absent from `origin/main`", "not in HEAD") is a revision-scope
claim, not a worktree claim: a path can be present here and absent upstream, and that is a
divergence to reconcile, not a stale sentence (card t_8a715681 was exactly that). Remote
objects are skipped — checked against the predicate's own object, not against any `origin`
mention elsewhere on the line.

Exit codes: 0 = no stale claim, 1 = at least one, 2 = usage.

Usage:
  /usr/bin/python3 music/scripts/check_brief_absence.py [--repo DIR] [--quiet]
  /usr/bin/python3 music/scripts/check_brief_absence.py --briefs music/briefs/activist.md
  /usr/bin/python3 music/scripts/check_brief_absence.py --rev f28792a7 --briefs music/briefs/activist.md
  /usr/bin/python3 music/scripts/check_brief_absence.py --explain   # why each candidate was dropped
  /usr/bin/python3 music/scripts/check_brief_absence.py --selftest

cited: t_752f02a8 (the incident and the singular check), t_9dfa74d9 (the plural check, now
folded in and deleted), t_4612d213 (this merge), t_8a715681 (the reconciliation that made the
claim stale), t_b7dd5655 (`check_brief_drift.py`, whose shape this follows).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --------------------------------------------------------------------------------------------
# R1 — predicates. Matched against the emphasis-stripped line, never the raw line.
# Each pattern is (regex, whether the match's first word makes it past tense).
# --------------------------------------------------------------------------------------------
PREDICATE_RES = (
    re.compile(r"\b(is|are|was|were|has been|have been|had been)\s+(?:\w+\s+){0,2}(?:absent|missing)\b"),
    re.compile(r"\b(?:does|do|did|doesn't|don't|didn't)\s+not\s+exist\b"),
    re.compile(r"\bnot\s+present\b"),
    re.compile(r"\bno\s+such\s+file\b"),
    re.compile(r"\bzero\s+hits\b"),
    re.compile(r"\bnot\s+in\s+this\s+(?:checkout|working tree|worktree|tree|repo)\b"),
    re.compile(r"\bnot\s+(?:on|in)\s+this\s+machine\b"),
)

PAST_LEAD_RE = re.compile(r"^(was|were|had|has|have)\b")

# R2 — an attributed predicate ("recorded this file ABSENT") is a record of a past statement.
ATTRIBUTION_RE = re.compile(
    r"\b(reported|recorded|formerly|previously|earlier|no longer|cited as|used to|once)\b"
)

# R3 — a quoted predicate is somebody's output, not a claim.
QUOTED_SPAN_RE = re.compile(r'"[^"\n]*"|“[^”\n]*”')
FENCE_RE = re.compile(r"^\s*(```|~~~)")
QUOTED_OUTPUT_RE = re.compile(r"\bclaims\b[^.\n]{0,80}\bis\s+absent\b|\bis\s+absent\b[^.\n]{0,40}\bit\s+exists\b")

# R4 — a sentence that states the rule is not a claim.
NORMATIVE_RE = re.compile(
    r"\bno\s+\w+\s+(?:may|must|can|should|will)\b"
    r"|\b(?:may|must|can|should|do|does)\s+not\s+(?:claim|assert|state|say)\b"
    r"|\b(?:is|are)\s+not\s+(?:allowed|permitted)\b"
)

# R5 — pass-record headings. Narrow on purpose: a heading that marks a *pass* stamps
# everything under it as a record. "Provenance", "Handoffs" and "Open items" are deliberately
# NOT here — those are live lists in this lane, and the rules above judge them.
RECORD_HEADING_RE = re.compile(
    r"\b(verification pass|surviving-card pass|duplicate-card|aged live counts"
    r"|citation-sweep|code-prose census|pass record)\b",
    re.IGNORECASE,
)

# R6 — paragraph-level history stamps. NOTE: a card id is deliberately NOT a stamp. Measured
# 2026-10-16 (t_4612d213): treating a card id as a paragraph stamp dropped two real claims —
# `elemental-water.md:390` and `elemental-air/above-the-weather/brief.md:404` at revision
# 3766fa3 both sit in paragraphs that name a card, and both were genuinely stale. A pass
# record's stamp is its heading (R5) and its clock, not any card it mentions.
HISTORY_PHRASES = (
    "superseded", "was true when", "measurement time", "when this brief was written",
    "when it was written", "supersession", "at the time of", "earlier pass",
)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")
REVISION_RE = re.compile(r"\brevision\s+`?[0-9a-f]{7,40}`?|\bat\s+`[0-9a-f]{7,40}`")

# R7 — an object scoped to a revision is not a worktree claim.
REMOTE_OBJECT_RE = re.compile(r"\b(origin|upstream|remote)\b|`?\bHEAD\b`?")
PRESENCE_RE = re.compile(r"\b(present|exists|on disk|landed|is tracked|byte-identical)\b",
                         re.IGNORECASE)

ROOT_DIRS = ("music", "brain", "campaigns", "scripts", "performance")
SUFFIXES = (".py", ".md", ".yaml", ".yml", ".json", ".sh", ".txt", ".wav", ".mp4", ".pdf")
PLACEHOLDER_RE = re.compile(r"[<>{}$*?\[\]]")

BACKTICK_RE = re.compile(r"`([^`\n]+)`")
BARE_ROOT_RE = re.compile(r"(?<![\w/$.~-])((?:" + "|".join(ROOT_DIRS) + r")/[A-Za-z0-9_./\-]+)")
EMPHASIS = ("*", "`", "_")


def strip_emphasis(text: str) -> tuple[str, list[int]]:
    """Lowercase, drop markdown emphasis, collapse whitespace — keeping an index map back.

    Measured 2026-10-16 (t_752f02a8): the first version matched markers against the raw line
    and therefore MISSED the very sentence it was written for — the incident text is
    `is **not in this checkout**`, with the phrase split by bold markers. The index map keeps
    token, predicate and clause positions in one coordinate system so the clause rule (R7)
    can compare them.
    """
    kept: list[tuple[str, int]] = []
    for i, ch in enumerate(text):
        if ch in EMPHASIS:
            continue
        if ch.isspace():
            if kept and kept[-1][0] == " ":
                continue
            kept.append((" ", i))
        else:
            kept.append((ch.lower(), i))
    while kept and kept[0][0] == " ":
        kept.pop(0)
    while kept and kept[-1][0] == " ":
        kept.pop()
    return "".join(ch for ch, _ in kept), [i for _, i in kept]


def looks_like_token(tok: str) -> bool:
    if not tok or PLACEHOLDER_RE.search(tok) or " " in tok:
        return False
    # Only repo-relative paths are in scope: reject URLs, remote refs, cluster names, home
    # paths and absolute paths. Measured 2026-10-16 (t_4612d213): an absolute API path
    # (`/api/v1/stems`) must not be allowed to steal a predicate's binding from the repo path
    # that follows it (`elemental-air/above-the-weather/brief.md:404`).
    if tok.startswith(("http", "origin/", "mining/", "localhost/", "~", "/")):
        return False
    if "/" in tok:
        return True
    return tok.endswith(SUFFIXES)


def clean_token(raw: str) -> str:
    return raw.strip().rstrip(".,;:)`'\"")


def path_tokens(line: str, rels: set[str], basenames: dict[str, str]
                ) -> list[tuple[str, str | None, int]]:
    """(text as written, resolved relative path or None, raw offset) for every path-shaped token.

    Unresolved tokens are returned too: R7 binds a predicate to the nearest path NAMED before it,
    and a path that does not exist still takes the binding (`elemental-earth.md:737` claims
    `music/mix/master.py` is absent — the only reason the earlier `gate_loudness.py` in the same
    row is not flagged).
    """
    found: list[tuple[str, str | None, int]] = []
    for pattern, group in ((BACKTICK_RE, 1), (BARE_ROOT_RE, 1)):
        for m in pattern.finditer(line):
            tok = clean_token(m.group(group))
            if not looks_like_token(tok):
                continue
            if tok in rels:
                found.append((tok, tok, m.start(group)))
            elif "/" not in tok and tok in basenames:
                found.append((tok, basenames[tok], m.start(group)))
            else:
                found.append((tok, None, m.start(group)))
    seen: set[tuple[str, int]] = set()
    unique = []
    for item in found:
        if (item[0], item[2]) in seen:
            continue
        seen.add((item[0], item[2]))
        unique.append(item)
    return sorted(unique, key=lambda item: item[2])


def norm_offset(raw_to_norm: dict[int, int], raw_pos: int) -> int:
    return raw_to_norm.get(raw_pos, -1)


def history_stamps(paragraph: str) -> str | None:
    low = paragraph.lower()
    for phrase in HISTORY_PHRASES:
        if phrase in low:
            return phrase
    if DATE_RE.search(paragraph) and CLOCK_RE.search(paragraph):
        return "date+clock"
    if REVISION_RE.search(paragraph):
        return "revision anchor"
    return None


def record_region(lines: list[str]) -> tuple[list[bool], list[str]]:
    """R5 — mark each line as inside a pass-record section, and name that section's heading."""
    inside: list[bool] = []
    titles: list[str] = []
    stack: list[tuple[int, bool, str]] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            is_record = bool(RECORD_HEADING_RE.search(stripped))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, is_record, stripped))
            inside.append(True)
            titles.append("")
            continue
        record = [t for _, is_rec, t in stack if is_rec]
        inside.append(bool(record))
        titles.append(record[-1] if record else "")
    return inside, titles


def paragraphs(lines: list[str]):
    """Yield (start_index, end_index, text) over blank-line separated blocks (0-based)."""
    block: list[str] = []
    start = 0
    for i, line in enumerate(lines):
        if line.strip():
            if not block:
                start = i
            block.append(line)
        else:
            if block:
                yield start, i, "\n".join(block)
                block = []
    if block:
        yield start, len(lines), "\n".join(block)


def scan(text: str, rels: set[str], basenames: dict[str, str], trace: list[str] | None = None
         ) -> list[tuple[int, str, str, str, str]]:
    """Return findings: (line_no, token, resolved, matched predicate, scope reason).

    `trace`, when passed, collects one line per candidate (a line that names a resolving path
    AND carries an absence predicate) saying which rule decided it — the `--explain` aid.
    """
    lines = text.splitlines()
    in_record, record_title = record_region(lines)
    fenced = [False] * len(lines)
    depth = 0
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            depth = 0 if depth else 1
            fenced[i] = True
            continue
        fenced[i] = bool(depth)

    def note(line_no: int, toks, preds, decision: str) -> None:
        if trace is not None:
            names = [tok[0] for tok in toks]
            trace.append(f"  {line_no}: token(s)={names} "
                         f"predicate(s)={preds} -> {decision}")

    findings: list[tuple[int, str, str, str, str]] = []
    seen: set[tuple[int, str]] = set()
    for start, end, paragraph in paragraphs(lines):
        block = list(range(start, min(end, len(lines))))

        # Per-line candidate extraction (tokens + predicates that pass R2/R3/R7-object).
        candidates: dict[int, tuple[list[tuple[str, str | None, int]], list[tuple[int, int, str]], dict[int, int], str, str]] = {}
        for i in block:
            line = lines[i]
            if FENCE_RE.match(line):
                continue
            flat, norm_index = strip_emphasis(line)
            if not flat:
                continue
            toks = path_tokens(line, rels, basenames)
            if not toks:
                continue
            raw_to_norm = {raw: n for n, raw in enumerate(norm_index)}

            # R3 — quoted spans, mapped into the flattened coordinate system.
            quote_intervals = []
            for span in QUOTED_SPAN_RE.finditer(line):
                ns = norm_offset(raw_to_norm, span.start())
                ne = norm_offset(raw_to_norm, max(span.start(), span.end() - 1))
                if ns >= 0 and ne >= 0:
                    quote_intervals.append((ns, ne))

            survivors: list[tuple[int, int, str]] = []
            dropped: list[str] = []
            for pattern in PREDICATE_RES:
                for m in pattern.finditer(flat):
                    matched = m.group(0)
                    if PAST_LEAD_RE.match(matched):
                        dropped.append(f"{matched!r} past tense (R2)")
                        continue
                    if ATTRIBUTION_RE.search(flat[max(0, m.start() - 30):m.start()]):
                        dropped.append(f"{matched!r} attributed (R2)")
                        continue
                    if any(s <= m.start() <= e for s, e in quote_intervals):
                        dropped.append(f"{matched!r} quoted (R3)")
                        continue
                    if REMOTE_OBJECT_RE.search(flat[m.end():m.end() + 60]):
                        dropped.append(f"{matched!r} remote object (R7)")
                        continue
                    survivors.append((m.start(), m.end(), matched))
            if survivors or dropped:
                candidates[i] = (toks, survivors, raw_to_norm, flat, "; ".join(dropped))

        if not candidates:
            continue

        # Paragraph-level rules first: they decide a whole block at once.
        if any(fenced[i] for i in block):
            heading = next((in_record[i] for i in block), False)
            for i in candidates:
                note(i + 1, candidates[i][0], [s[2] for s in candidates[i][1]],
                     "skipped: fenced code block (R3)" + (" [also a record heading]" if heading else ""))
            continue
        if any(in_record[i] for i in block):
            for i in candidates:
                note(i + 1, candidates[i][0], [s[2] for s in candidates[i][1]],
                     f"skipped: pass-record section (R5) — {record_title[i].strip()[:60]}")
            continue
        stamp = history_stamps(paragraph)
        if stamp:
            for i in candidates:
                note(i + 1, candidates[i][0], [s[2] for s in candidates[i][1]],
                     f"skipped: history paragraph (R6) — stamp {stamp!r}")
            continue

        for i, (toks, survivors, raw_to_norm, flat, dropped) in candidates.items():
            if NORMATIVE_RE.search(flat):
                note(i + 1, toks, [s[2] for s in survivors], "skipped: states the rule (R4)")
                continue
            if QUOTED_OUTPUT_RE.search(flat):
                note(i + 1, toks, [s[2] for s in survivors],
                     "skipped: quoted check output (R3)")
                continue
            if not survivors:
                note(i + 1, toks, [], f"skipped: no surviving predicate (R2/R3/R7) — {dropped}")
                continue
            is_table = lines[i].lstrip().startswith("|")
            clauses = [(m.start(), m.end(), m.group(0)) for m in re.finditer(r"[^;,]+", flat)]
            rows = [(0, len(flat), flat)] if is_table else clauses
            entries = [(norm_offset(raw_to_norm, pos), written, resolved)
                       for written, resolved, pos in toks
                       if norm_offset(raw_to_norm, pos) >= 0]
            # R7 — a predicate binds to the nearest path NAMED BEFORE it on the line. This models
            # how the sentences actually read: "`suno-gen.py` is **not in this checkout**",
            # "… but that file is not in this checkout" (owner: the path named just before),
            # and it refuses to lend a claim to an earlier path that a later sentence only cites.
            bound: dict[int, str] = {}
            for s, _e, matched in survivors:
                owner = None
                for index, (npos, _written, _resolved) in enumerate(entries):
                    if npos <= s:
                        owner = index
                    else:
                        break
                if owner is None:
                    note(i + 1, [(w, p) for p, w, _r in entries], [matched],
                         f"skipped: predicate {matched!r} names no path before it (R7)")
                    continue
                bound.setdefault(owner, matched)
            for index, (npos, written, resolved) in enumerate(entries):
                if index not in bound or resolved is None:
                    continue
                scope = next((c for c in rows if c[0] <= npos <= c[1]), None)
                if scope is not None and PRESENCE_RE.search(scope[2]):
                    note(i + 1, [(written, npos)], [bound[index]],
                         f"skipped: scope also asserts the path present (R7) — {written!r}")
                    continue
                key = (i + 1, resolved)
                if key in seen:
                    continue
                seen.add(key)
                reason = "same table row" if is_table else "same line"
                findings.append((i + 1, written, resolved, bound[index], reason))
                note(i + 1, [(written, npos)], [bound[index]], "FINDING")
    return findings


def index_worktree(repo: Path) -> tuple[set[str], dict[str, str]]:
    """(relative file paths, basename -> relative path) for every file under repo."""
    rels: set[str] = set()
    basenames: dict[str, str] = {}
    for path in repo.rglob("*"):
        if not path.is_file() or "/.git/" in str(path):
            continue
        rel = path.relative_to(repo).as_posix()
        rels.add(rel)
        basenames.setdefault(path.name, rel)
    return rels, basenames


def load_brief(path: Path, rev: str | None, repo: Path) -> str:
    if rev is None:
        return path.read_text()
    rel = path.relative_to(repo).as_posix()
    proc = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=repo,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"check_brief_absence: cannot read {rel} at {rev}: {proc.stderr.strip()}")
    return proc.stdout


def selftest() -> int:
    """Prove the check fires on the incident and stays quiet on every measured false positive.

    Each case is a named assertion with a count, so a future edit names the case it broke.
    """
    tmp = Path(tempfile.mkdtemp(prefix="check-brief-absence-"))
    ok = True
    try:
        (tmp / "music/scripts").mkdir(parents=True)
        (tmp / "music/scripts/suno-gen.py").write_text("# present now\n")
        (tmp / "music/assets").mkdir(parents=True)
        (tmp / "music/assets/pack.py").write_text("# present now\n")
        (tmp / "music/rubrics").mkdir(parents=True)
        (tmp / "music/rubrics/measure.py").write_text("# present now\n")
        (tmp / "music/briefs").mkdir(parents=True, exist_ok=True)
        rels, basenames = index_worktree(tmp)

        cases = [
            ("incident §8 sentence (must fire)", 1,
             "`suno-gen.py` is **not in this checkout** — `find /home_j_kro -name 'suno-gen.py'`\n"
             "returns zero hits — but it is on `origin/main`\n"
             "(`git cat-file -e origin/main:music/suno-gen.py` → present).\n"),
            ("R5/R6 §12 history paragraph, stamp on a later line (must not fire)", 0,
             "**Also true and left standing:** `music/suno-gen.py` is genuinely absent from this working\n"
             "tree (`find /home_j_kro -name suno-gen.py` → zero hits) and genuinely present on\n"
             "`origin/main` (last touched `ba28f55`, 2026-10-14). That is the divergence t_8a715681, not\n"
             "a wrong citation: do not delete the reference, merge the refs.\n"
             "**SUPERSEDED (§14):** the divergence was reconciled.\n"),
            ("R6 §12 amendment, clock on the next line (must not fire)", 0,
             "**8. §11 amendment.** `7e54e03` recorded, correctly at measurement time, that\n"
             "`brain/playbooks/music-lane-architecture.md` was not on this machine. At 13:59:25 another\n"
             "worker wrote it.\n"),
            ("R3 quoted check output inside a fence (must not fire)", 0,
             "```\n"
             "FAIL check_brief_absence: 1 stale absence claim in 1 brief\n"
             "  music/briefs/activist.md:371  claims 'suno-gen.py' is absent; it exists at 'music/suno-gen.py'\n"
             "```\n"),
            ("R4 rule sentence (must not fire)", 0,
             "`music/scripts/check_brief_absence.py` — no brief may claim a repo path is ABSENT from this\n"
             "checkout while the path exists.\n"),
            ("R7 line-level co-occurrence, absence governs another token (must not fire)", 0,
             "`butler` and `~/.hermes/vault/itch_io_key` are still absent (§10); `music/assets/pack.py`\n"
             "exists.\n"),
            ("R7 null referent (`with it absent` governs a field, not the path) (must not fire)", 0,
             "one render at `style_weight = 0.9`, one with it `absent`, both measured with\n"
             "`music/rubrics/measure.py`.\n"),
            ("R2 past-tense / attributed record (must not fire)", 0,
             "| Lyric blueprint | `music/scripts/suno-gen.py` — **PRESENT** (4422 B). It was ABSENT when\n"
             "this brief was written.\n"),
            ("R3 quoted check output as a bare line, not in a fence (must not fire)", 0,
             "  music/briefs/activist.md:371  claims 'suno-gen.py' is absent; it exists at "
             "'music/suno-gen.py'\n"),
            ("R7 a LATER path takes the binding; the earlier citation stays quiet (must not fire)", 0,
             "| master | producer | `gate_loudness --target streaming` for the lane, and the gate says\n"
             "so in its own docstring (`music/scripts/suno-gen.py:2`); the fix (`music/scripts/master.py`)\n"
             "is on `origin/main` and is not an ancestor of `HEAD`, so it is absent from this tree |\n"),
            ("R7 remote object (must not fire)", 0,
             "`suno-gen.py` is absent from `origin/main`.\n"),
            ("R7 genuine table row, token and verdict in separate cells (must fire)", 1,
             "| B — Suno CDP | `music/scripts/suno-gen.py` | **NO — the file does not exist in this tree.** |\n"),
            ("genuinely absent path (must not fire)", 0,
             "`music/scripts/never-authored.py` does not exist anywhere on this machine.\n"),
        ]

        for name, want, body in cases:
            case = tmp / "music/briefs/case.md"
            case.write_text(body)
            hits = scan(case.read_text(), rels, basenames)
            got = len(hits)
            mark = "ok" if got == want else "BROKEN"
            if got != want:
                ok = False
            detail = ", ".join(f"{h[1]}@{h[0]}" for h in hits)
            print(f"SELFTEST {mark}: want {want} flagged, got {got}"
                  f"{' (' + detail + ')' if detail else ''} — {name}")

        print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_brief_absence: "
              f"{len(cases)} case(s), incident fires, every measured false positive stays quiet")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="check_brief_absence — a brief may not claim a repo path is absent "
                    "while it exists in this checkout")
    parser.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    parser.add_argument("--briefs", nargs="*", default=None,
                        help="brief paths (default: every music/briefs/**/*.md)")
    parser.add_argument("--rev", default=None,
                        help="read the briefs as of this revision (git show REV:path)")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--explain", action="store_true",
                        help="print why each candidate line was flagged or skipped")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    if args.briefs:
        briefs = [Path(b) if Path(b).is_absolute() else repo / b for b in args.briefs]
    else:
        briefs = sorted((repo / "music/briefs").rglob("*.md"))
    if not briefs:
        print("check_brief_absence: no briefs found", file=sys.stderr)
        return 2

    rels, basenames = index_worktree(repo)
    offenders = []
    markers = 0
    for brief in briefs:
        text = load_brief(brief, args.rev, repo)
        trace: list[str] | None = [] if args.explain else None
        hits = scan(text, rels, basenames, trace)
        markers += len(PREDICATE_RES[0].findall(text))
        if trace:
            print(f"# {brief.relative_to(repo).as_posix()}")
            for entry in trace:
                print(entry)
        for line_no, token, resolved, pred, reason in hits:
            offenders.append(
                f"  {brief.relative_to(repo).as_posix()}:{line_no}  claims {token!r} is absent "
                f"({pred!r} in the {reason}); it exists at {resolved!r}")

    if offenders:
        print(f"FAIL check_brief_absence: {len(offenders)} stale absence claim(s) in "
              f"{len(briefs)} brief(s)")
        for o in offenders:
            print(o)
        print("  Fix: correct the sentence in the citing brief, or anchor it to the revision "
              "and clock it was measured at (a stamped paragraph is history and is skipped). "
              "Do NOT delete the path to match a stale brief.")
        return 1

    if args.rev is not None:
        print(f"PASS check_brief_absence: no stale absence claim in revision {args.rev} "
              f"({len(briefs)} brief(s) scanned)")
    elif not args.quiet:
        print(f"PASS check_brief_absence: no brief claims a repo path is absent while it "
              f"exists in {repo}  ({len(briefs)} brief(s) scanned, "
              f"{markers} absence predicate(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
