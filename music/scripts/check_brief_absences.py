#!/usr/bin/env python3
"""check_brief_absences — a brief that says a repo path is absent must still be right.

Why this exists
---------------
Measured 2026-10-16 (card t_9dfa74d9, the surviving-card pass on
`music/briefs/anime-ending.md`): that brief's §1 table read
`music/lyrics/blueprints/anime-ending.yaml` — **ABSENT**, its §6 read
`campaigns/virtual-reflections/` does **not** exist anywhere on nexus, and its §9 carried a
"Dangling reference" block for `brain/playbooks/music-lane-architecture.md`. All three paths
existed by the time the pass ran: a sibling card had added the blueprint at 14:03, the album
record landed in `campaigns/virtual-reflections/`, and both `brain/` files were on disk and in
`HEAD`. Nothing failed. The class is invisible to the checks that exist:

  - `check_brief_figures.py` recomputes numbers, and explicitly skips a claim whose referent
    the repo cannot prove.
  - `check_brief_paths.py` states that it deliberately does NOT check `music/`, `brain/`,
    `campaigns/` roots — "briefs legitimately cite artifacts that must not exist yet, so a
    blanket 'must resolve' rule would be mostly false alarms".

The second half of that argument is right and this check keeps it: a cited path that does not
exist is NOT a finding here. Only the opposite is — the brief asserts absence and the path is
there. That direction has no legitimate reading.

Rules enforced
--------------
1. FAIL when a line of a brief asserts absence (`absent`, `does not exist`, `do not exist`,
   `not present`, `no such file`) of a repo-relative path under `music/`, `brain/`,
   `campaigns/`, `scripts/` or `performance/`, and that path exists in the repo.
2. A line that names a date, a clock time, a card id (`t_xxxxxxxx`) or a commit hash is
   HISTORY, not a claim about now, and is skipped — the same convention
   `check_brief_drift.py` uses for aged counts. So "It was ABSENT when this brief was written
   (2026-10-16 13:06)" passes, and "`music/packages/` does not exist" fails the day the
   directory is created.
3. A token that is a glob, a placeholder (`<genre>`, `**`, `*`) or a trailing-slash directory
   name is still checked when it names a real path; a token that cannot be a path is skipped.

Deliberately NOT checked: paths the repo cannot resolve (cluster state, `~/` paths, another
checkout). This check judges only what exists in the worktree.

Usage:
  python3 music/scripts/check_brief_absences.py [--repo DIR]

Exit codes: 0 = no absence claim is stale, 1 = at least one is, 2 = usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOTS = ("music", "brain", "campaigns", "scripts", "performance")

ABSENT_RE = re.compile(
    r"\b(absent|does not exist|do not exist|doesn't exist|don't exist|not present"
    r"|no such file|is missing|are missing)\b",
    re.IGNORECASE,
)

# A repo-relative path token: root + at least one more segment. No whitespace, no backtick.
PATH_RE = re.compile(
    r"(?<![\w/$.~-])((?:" + "|".join(ROOTS) + r")/[A-Za-z0-9_.\-/]+)"
)

# Anchors that make a line history rather than a claim about the present.
ANCHOR_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}"          # a date
    r"|\d{1,2}:\d{2}"              # a clock time
    r"|\bt_[0-9a-f]{8}\b"          # a kanban card id
    r"|\b[0-9a-f]{7,40}\b"         # a commit / hash
    r")"
)

# A claim scoped to git rather than to the worktree ("absent from origin/main",
# "not tracked", "still untracked") is about a revision, and this check does not
# judge revisions. `music/suno-gen.py` is the standing example: on disk, untracked.
GIT_RE = re.compile(
    r"(origin/main|origin\b|\bHEAD\b|\bgit\b|tracked|untracked|\bcommit\b|\bbranch\b"
    r"|pushed|staged)",
    re.IGNORECASE,
)

# Tokens that cannot be a literal path.
PLACEHOLDER_RE = re.compile(r"[<>{}$*?\[\]]")


def is_file_token(raw: str) -> bool:
    """A path token that names a file, not a directory.

    Directory tokens are skipped on purpose: a line that says
    "`music/lyrics/blueprints/` — no anisong file exists" names the directory while the
    claim is about one file inside it, and the directory is not the thing claimed absent.
    Requiring a file token keeps this check precise instead of loud.
    """
    leaf = raw.rstrip("/").rpartition("/")[2]
    return "." in leaf and not raw.endswith("/")


def clean(tok: str) -> str:
    return tok.rstrip(".,;:)`'\"")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    briefs = sorted(repo.glob("music/briefs/**/*.md"))
    if not briefs:
        print(f"FAIL check_brief_absences: no briefs under {repo}/music/briefs")
        return 1

    hits: list[tuple[str, int, str, str]] = []
    claims = 0
    skipped_anchored = 0
    skipped_git = 0
    skipped_dir = 0
    scanned = 0

    for brief in briefs:
        rel = str(brief.relative_to(repo))
        for no, line in enumerate(brief.read_text(errors="replace").splitlines(), 1):
            if not ABSENT_RE.search(line):
                continue
            scanned += 1
            if ANCHOR_RE.search(line):
                skipped_anchored += 1
                continue
            if GIT_RE.search(line):
                skipped_git += 1
                continue
            for raw in {clean(t) for t in PATH_RE.findall(line)}:
                if PLACEHOLDER_RE.search(raw):
                    continue
                if not is_file_token(raw):
                    skipped_dir += 1
                    continue
                claims += 1
                target = repo / raw
                if target.exists():
                    hits.append((rel, no, raw, "file" if target.is_file() else "dir"))

    if hits:
        print(f"FAIL check_brief_absences: {len(hits)} absence claim(s) name a repo path "
              f"that EXISTS in {repo}")
        for rel, no, raw, kind in hits:
            print(f"  {rel}:{no}  claims absent, but {kind} exists: {raw}")
        print("  Fix: correct the claim in the citing brief. Do NOT delete the path to match "
              "a stale brief.")
        return 1

    print(f"PASS check_brief_absences: {claims} file-absence claim(s) over {scanned} "
          f"candidate line(s) across {len(briefs)} brief(s) match the worktree "
          f"({skipped_anchored} anchored to a date/time/card/commit, {skipped_git} scoped to "
          f"git rather than the worktree, {skipped_dir} directory token(s) — all skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
