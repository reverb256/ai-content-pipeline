#!/usr/bin/env python3
"""check_brief_paths — a sibling-checkout citation in a brief must resolve.

Why this exists
---------------
Measured 2026-10-16 (card t_67fc5307, the duplicate-card pass on
`music/briefs/epic-orchestral-boss.md`): that brief cited the engine payload as
`mining-k8s/helm/charts/music-pipeline/files/music/prompts/epic-orchestral-boss.md`
and asserted `cmp` proved it byte-identical to the lane repo's template. The path is
correct only RELATIVE TO $HOME, because `mining-k8s` is a second checkout
(`/home/j_kro/mining-k8s`), not a directory inside the lane repo. Resolved from the
lane repo root the file looks missing (`cmp` -> "No such file or directory"), which is
a false alarm for every stage that reuses the citation. The pass fixed the brief by
naming the root; this script is the regression check for that class, the way
`music/scripts/check_stage_scripts.py` guards the `music/suno-gen.py` misreading.

Rules enforced
--------------
1. FAIL if a cited `mining-k8s/...` path resolves nowhere under $HOME (a broken or
   stale citation).
2. WARN (does not fail) when a brief cites `mining-k8s/...` without ever naming the
   checkout root (`/home/j_kro/mining-k8s` or `$HOME/mining-k8s`); the citation is
   ambiguous to anyone whose cwd is the lane repo.

Deliberately NOT checked: other roots (`music/...`, `brain/...`, `campaigns/...`).
Briefs legitimately cite artifacts that must not exist yet — the absent lyric
blueprints and the unbuilt `music/assets/`, `music/publish/` trees — so a blanket
"must resolve" rule would be mostly false alarms. Absence of `music/suno-gen.py`
and `music/sunolocal/` from this checkout is owned by check_stage_scripts.py, and
the dangling `brain/playbooks/` + `brain/research/` class is filed as t_b0a4db92.

Usage:
  python3 music/scripts/check_brief_paths.py [--repo DIR] [--home DIR]

Exit codes: 0 = every sibling-checkout citation resolves, 1 = at least one does not,
2 = usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SIBLING = "mining-k8s"
CITE_RE = re.compile(rf"{SIBLING}/[A-Za-z0-9_.\-/]+")
ROOT_MARKERS = (f"/home/j_kro/{SIBLING}", f"$HOME/{SIBLING}")


def clean(tok: str) -> str:
    return tok.rstrip(".,;:)`'\"")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--home", default="/home/j_kro")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    home = Path(args.home).resolve()
    briefs = sorted(repo.glob("music/briefs/**/*.md"))
    if not briefs:
        print(f"FAIL check_brief_paths: no briefs under {repo}/music/briefs")
        return 1

    missing: dict[str, list[str]] = {}
    ambiguous: list[str] = []
    checked = 0
    for brief in briefs:
        text = brief.read_text(errors="replace")
        rel = str(brief.relative_to(repo))
        toks = sorted({clean(t) for t in CITE_RE.findall(text)})
        if not toks:
            continue
        checked += len(toks)
        if not any(m in text for m in ROOT_MARKERS):
            ambiguous.append(rel)
        for tok in toks:
            if not (home / tok).exists():
                missing.setdefault(tok, []).append(rel)

    if missing:
        print(f"FAIL check_brief_paths: {len(missing)} cited sibling-checkout path(s) "
              f"resolve nowhere under {home}")
        for tok, files in sorted(missing.items()):
            print(f"  {tok}")
            print(f"    cited by: {', '.join(sorted(files))}")
        print(f"  Fix: correct the citation, or drop it and cite the real path.")
        return 1

    print(f"PASS check_brief_paths: {checked} `{SIBLING}/...` citation(s) across "
          f"{len(briefs)} brief(s) resolve under {home}")
    for rel in ambiguous:
        print(f"  WARN {rel}: cites `{SIBLING}/` without naming the checkout root "
              f"(`{ROOT_MARKERS[0]}` or `{ROOT_MARKERS[1]}`)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
