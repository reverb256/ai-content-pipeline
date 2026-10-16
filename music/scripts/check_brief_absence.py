#!/usr/bin/env python3
"""check_brief_absence — FAIL when a brief claims a repo path is ABSENT from this checkout.

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

WHAT IT DOES
------------
For every `music/briefs/**/*.md` it looks for WORKTREE absence markers in the same line as a
path-like token:

    "is not in this checkout" / "is not in this working tree"
    "is absent from this working tree" / "is absent from this checkout"
    "does not exist anywhere on this machine" / "no such file" / "zero hits"

and resolves the token against the worktree. If the path EXISTS, the claim is stale and the
run FAILs. The marker's OBJECT decides scope, and that is the whole design:

  * WORKTREE markers (checked): the claim is about this checkout, so the worktree settles it.
  * REMOTE markers (skipped): "absent from `origin/main`", "not on `origin/...`",
    "not in HEAD". A path can be present here and absent upstream, and that is a divergence
    to reconcile, not a stale sentence (card t_8a715681 was exactly that).
  * A HISTORY paragraph is skipped: one carrying `SUPERSEDED`, "was true when",
    "measurement time", "when this brief was written", or a clock/date stamp. Sections §12+
    of these briefs are pass records — they quote what was true at a past instant, and
    flagging them would be noise. Same distinction `check_brief_drift.py` draws for an
    anchored count: a stamp makes it a fact, an unanchored present tense makes it a claim.

Exit codes: 0 = every checked claim still holds, 1 = at least one stale claim, 2 = usage.

Usage:
  /usr/bin/python3 music/scripts/check_brief_absence.py [--repo DIR] [--quiet]
  /usr/bin/python3 music/scripts/check_brief_absence.py --briefs music/briefs/activist.md
  /usr/bin/python3 music/scripts/check_brief_absence.py --rev f28792a7 --briefs music/briefs/activist.md
  /usr/bin/python3 music/scripts/check_brief_absence.py --selftest

cited: t_752f02a8 (this incident), t_8a715681 (the reconciliation that made the claim stale),
t_b7dd5655 (check_brief_drift.py, whose shape this follows).
"""

from __future__ import annotations

import argparse
import datetime
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WORKTREE_MARKERS = (
    "is not in this checkout",
    "is not in this working tree",
    "is absent from this working tree",
    "is absent from this checkout",
    "does not exist anywhere on this machine",
    "does not exist in this checkout",
    "no such file",
    "zero hits",
)

REMOTE_MARKERS = (
    "absent from `origin/",
    "not on `origin/",
    "not in HEAD",
    "absent from origin/",
    "not on origin/",
)

HISTORY_MARKERS = (
    "SUPERSEDED",
    "was true when",
    "measurement time",
    "when this brief was written",
    "when it was written",
)

# A paragraph that names the revision it describes is a history record, the same distinction
# `check_brief_drift.py` and `check_brief_line_refs.py` draw with their ANCHORED regex. Kept
# narrow — "revision <hex>" and "at `<hex>`" — so that a mere provenance mention of a commit
# elsewhere in the paragraph (`added by \`ba28f55\``) does NOT make a present-tense claim
# skippable. Measured: the wider "any hex token" rule skipped the pre-correction §8 paragraph
# this check exists to catch.
REVISION_RE = re.compile(r"\brevision\b[^.]{0,24}\b[0-9a-f]{7,40}\b|\bat `[0-9a-f]{7,40}`")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")

# A token that names a repo file: contains a slash, or carries a source suffix.
PATH_RE = re.compile(r"`([A-Za-z0-9_./-]+)`")
SUFFIXES = (".py", ".md", ".yaml", ".yml", ".json", ".sh", ".txt", ".wav", ".mp4", ".pdf")


def looks_like_path(token: str) -> bool:
    if token.startswith(("http://", "https://", "-")):
        return False
    if "/" in token and not token.startswith(("origin/", "mining/", "localhost/")):
        return True
    return any(token.endswith(s) for s in SUFFIXES) and "/" not in token


def index_worktree(repo: Path) -> tuple[set[str], dict[str, str]]:
    """Return (relative paths, basename -> relative path) for every file under repo."""
    rels: set[str] = set()
    basenames: dict[str, str] = {}
    for path in repo.rglob("*"):
        if not path.is_file() or ".git/" in str(path):
            continue
        rel = path.relative_to(repo).as_posix()
        rels.add(rel)
        basenames.setdefault(path.name, rel)
    return rels, basenames


def paragraphs(text: str):
    """Yield (line_number_of_first_line, paragraph_text)."""
    block: list[str] = []
    start = 1
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not block:
                start = i
            block.append(line)
        else:
            if block:
                yield start, "\n".join(block)
                block = []
    if block:
        yield start, "\n".join(block)


def is_history(par: str) -> bool:
    if any(m in par for m in HISTORY_MARKERS):
        return True
    if REVISION_RE.search(par):
        return True
    return bool(DATE_RE.search(par)) and bool(CLOCK_RE.search(par))


def normalize(line: str) -> str:
    """Lowercase and strip markdown emphasis, so `is **not in this checkout**` matches.

    Measured 2026-10-16 (t_752f02a8): the first version of this check matched markers against
    the raw line and therefore MISSED the very sentence it was written for — the incident text
    is `is **not in this checkout**`, with the phrase split by bold markers. The selftest now
    uses that exact sentence, markup and all.
    """
    stripped = line.replace("*", "").replace("`", "").replace("_", "")
    return re.sub(r"\s+", " ", stripped).strip().lower()


def scan(text: str, rels: set[str], basenames: dict[str, str]):
    """Return a list of (line_no, claimed_token, resolved_relpath, line)."""
    hits = []
    for start, par in paragraphs(text):
        if is_history(par):
            continue
        for offset, line in enumerate(par.splitlines()):
            flat = normalize(line)
            if any(m in flat for m in REMOTE_MARKERS):
                continue
            if not any(m in flat for m in WORKTREE_MARKERS):
                continue
            for token in PATH_RE.findall(line):
                if not looks_like_path(token):
                    continue
                if token in rels:
                    hits.append((start + offset, token, token, line.strip()))
                elif "/" not in token and token in basenames:
                    hits.append((start + offset, token, basenames[token], line.strip()))
    # One line can name the same path twice (a table cell quotes it in both columns);
    # report the claim once, not once per mention.
    seen: set[tuple[int, str]] = set()
    unique = []
    for line_no, token, resolved, line in hits:
        if (line_no, token) in seen:
            continue
        seen.add((line_no, token))
        unique.append((line_no, token, resolved, line))
    return unique


def load_brief(path: Path, rev: str | None, repo: Path) -> str:
    if rev is None:
        return path.read_text()
    rel = path.relative_to(repo).as_posix()
    proc = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=repo,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"check_brief_absence: cannot read {rel} at {rev}: "
                         f"{proc.stderr.strip()}")
    return proc.stdout


def selftest() -> int:
    """Prove the check fails on this incident and stays quiet on the two skip classes."""
    tmp = Path(tempfile.mkdtemp(prefix="check-brief-absence-"))
    try:
        (tmp / "music/scripts").mkdir(parents=True)
        # The checkpoint that later landed (the incident's whole point).
        (tmp / "music/scripts/suno-gen.py").write_text("# present now\n")
        mine = tmp / "music/briefs/mine.md"
        mine.parent.mkdir(parents=True)
        mine.write_text(
            "# stale (the incident's exact sentence, bold markup and all)\n\n"
            "`suno-gen.py` is **not in this checkout** — `find /home_j_kro -name "
            "'suno-gen.py'` returns\nzero hits — but it is on `origin/main` "
            "(`git cat-file -e origin/main:music/suno-gen.py` →\npresent).\n\n"
            "# history (must be skipped: SUPERSEDED)\n\n"
            "`suno-gen.py` is not in this checkout. **SUPERSEDED (§14):** it landed at 14:23.\n\n"
            "# remote (must be skipped: the object is origin/main)\n\n"
            "`suno-gen.py` is absent from `origin/main`.\n\n"
            "# genuinely absent (must pass)\n\n"
            "`music/scripts/never-authored.py` does not exist anywhere on this machine.\n"
        )
        rels, basenames = index_worktree(tmp)
        hits = scan(mine.read_text(), rels, basenames)
        want = 1
        ok = len(hits) == want and hits[0][1] == "suno-gen.py"
        print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_brief_absence: "
              f"stale-claims flagged={len(hits)} (want {want}), "
              f"history paragraph skipped=True, remote-object claim skipped=True, "
              f"absent-path claim not flagged=True")
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
    total_claims = 0
    offenders = []
    for brief in briefs:
        text = load_brief(brief, args.rev, repo)
        hits = scan(text, rels, basenames)
        total_claims += len(re.findall("|".join(re.escape(m) for m in WORKTREE_MARKERS),
                                       text, flags=re.I))
        for line_no, token, resolved, line in hits:
            offenders.append(
                f"  {brief.relative_to(repo).as_posix()}:{line_no}  claims "
                f"{token!r} is absent; it exists at {resolved!r}\n      {line[:100]}")

    if offenders:
        print(f"FAIL check_brief_absence: {len(offenders)} stale absence claim(s) in "
              f"{len(briefs)} brief(s)")
        for o in offenders:
            print(o)
        print("  Fix: correct the sentence in the citing brief, or anchor it to the revision "
              "it was measured at (an anchored claim is history and is skipped).")
        return 1

    if args.rev is None and not args.quiet:
        print(f"PASS check_brief_absence: no brief claims a repo path is absent while it "
              f"exists in {repo}  ({len(briefs)} brief(s) scanned, "
              f"{total_claims} worktree-absence marker(s))")
    elif args.rev is not None:
        print(f"PASS check_brief_absence: no stale absence claim in revision {args.rev} "
              f"({len(briefs)} brief(s) scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
