#!/usr/bin/env python3
"""check_soul_declarations — a SOUL must not declare a module the host cannot open.

Why this exists
---------------
Measured 2026-10-16 (card t_e2375c5a, host nexus, closing the t_75aacf8b cleanup).
The `music-producer` SOUL "Domain" table named five module paths. A worker who trusts
that table looks for the module, gets "No such file or directory", and reports dead air
as fact. The card's own measurement was *also* wrong in the other direction: it called
all five absent "in no checkout", but three of them (`music/mix/`, `music/lanes/`,
`music/publish/`) exist on zephyr's clone (`/home/j_kro/Projects/ai-content-pipeline`,
branch main) and are simply not on nexus. A bare existence test therefore cannot be the
rule — the rule is "present here, or marked as living somewhere else". The same pass
found the second half of the defect class: the SOUL told a worker to run
`hermes kanban --board music`, and `$HERMES_KANBAN_TASK` does not exist in a worker
shell (`agent/delegation_context.py` strips the five KANBAN_ENV_KEYS; the CLI is fenced).
This is the same "declaration vs disk" class as `~/bin/verify-fleet.sh` check 11
(profile workdir) and `music/scripts/check_stage_scripts.py` (stage scripts).

Rules enforced
--------------
1. FAIL if a `music/...` path token in the "## Domain" section resolves nowhere under
   `--repo` and no line of the SOUL marks that token as living elsewhere (zephyr /
   planned / absent / not tracked).
2. FAIL if any line OUTSIDE the SOUL's "Shell environment" section mentions
   HERMES_KANBAN_TASK. That name is empty in every shell the terminal tool spawns, so a
   line pointing a reader at it is false. The dedicated section is where the caveat is
   allowed to name it.
3. FAIL if the SOUL names the `hermes kanban` CLI but never names
   `kanban-worker-context.sh`, the helper that derives the identity from the vars that
   DO survive in a shell.
4. NOTE (never a failure) when a row annotated "elsewhere" actually resolves here: the
   annotation has aged, and the reader should re-measure it.

Usage:
  python3 music/scripts/check_soul_declarations.py [--soul PATH] [--repo DIR]

Exit codes: 0 = every declaration resolves or is annotated, 1 = at least one violates,
2 = usage error. SKIP (exit 0) when the SOUL does not exist on this host — the profile
is nexus-only, so this check is a no-op on other hosts rather than a false alarm.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_SOUL = "/home/j_kro/.hermes/profiles/music-producer/SOUL.md"
DEFAULT_REPO = "/home/j_kro/ai-content-pipeline"
HELPER = "kanban-worker-context.sh"
# A token is "declared elsewhere" when some line that names it also carries one of
# these. Keep the list short and literal; a vague marker is a marker that lies.
MARKERS = ("zephyr", "planned", "absent", "not on this host", "not tracked")
HEADING_RE = re.compile(r"^#{2,4}\s")
TOKEN_RE = re.compile(r"`([^`]+)`")


def section(lines: list[str], needle: str) -> tuple[int, int] | None:
    """Return (start, end) of the heading section whose title contains `needle`."""
    for i, line in enumerate(lines):
        if HEADING_RE.match(line) and needle.lower() in line.lower():
            for j in range(i + 1, len(lines)):
                if HEADING_RE.match(lines[j]):
                    return i, j
            return i, len(lines)
    return None


def tokens_in(text: str) -> list[str]:
    return [t.strip() for t in TOKEN_RE.findall(text) if t.strip().startswith("music/")]


def main() -> int:
    ap = argparse.ArgumentParser(description="SOUL declaration vs disk")
    ap.add_argument("--soul", default=DEFAULT_SOUL)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    args = ap.parse_args()

    soul = Path(args.soul)
    if not soul.is_file():
        print(f"SKIP check_soul_declarations: no SOUL at {soul} on this host")
        return 0
    repo = Path(args.repo)
    lines = soul.read_text(encoding="utf-8").splitlines()
    fails: list[str] = []
    notes: list[str] = []

    # Rule 1 — Domain rows.
    dom = section(lines, "## Domain")
    if dom is None:
        fails.append("SOUL has no '## Domain' section to check")
        dom_tokens: list[str] = []
    else:
        start, end = dom
        dom_tokens = sorted({t for t in tokens_in("\n".join(lines[start:end]))})
        rows = 0
        for tok in dom_tokens:
            here = (repo / tok).exists()
            annotated = any(
                tok in line and any(m in line.lower() for m in MARKERS) for line in lines
            )
            if here:
                rows += 1
                if annotated:
                    notes.append(f"{tok} resolves here although the SOUL marks it elsewhere")
            elif annotated:
                rows += 1
                notes.append(f"{tok} absent here, annotated (not on this checkout)")
            else:
                fails.append(f"{tok} is absent under {repo} and carries no marker")

    # Rule 2 — no shell-false reference to the task env var outside the caveat section.
    caveat = section(lines, "Shell environment")
    guarded = set(range(caveat[0], caveat[1])) if caveat else set()
    for i, line in enumerate(lines):
        if "HERMES_KANBAN_TASK" in line and i not in guarded:
            fails.append(
                f"line {i + 1} references HERMES_KANBAN_TASK outside the "
                f"'Shell environment' section: {line.strip()[:80]}"
            )

    # Rule 3 — naming the fenced CLI without naming the helper that works.
    blob = "\n".join(lines)
    if "hermes kanban" in blob and HELPER not in blob:
        fails.append(f"SOUL names the `hermes kanban` CLI but never names {HELPER}")

    for n in notes:
        print(f"  NOTE {n}")
    if fails:
        print(f"FAIL check_soul_declarations: {len(fails)} violation(s)")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(
        f"PASS check_soul_declarations: {len(dom_tokens)} Domain rows resolve or are "
        f"annotated; shell-env rule holds ({soul})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
