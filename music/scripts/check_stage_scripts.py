#!/usr/bin/env python3
"""Check that every script path named by a music stage exists in this checkout.

WHY THIS EXISTS (incident 2026-10-16, cards t_9f7d6889 / t_d706d0a3, and earlier
t_2541fd9c): the brief for `sentimental-piano` recorded D4 as "no file named
suno-gen* exists under /home/j_kro". It was wrong. `music/suno-gen.py` exists on
`origin/main` (added by ba28f55); the LOCAL checkout simply does not carry it. The
same misreading was made and corrected once before, in the `trance` brief.

A reader who checks only the working tree cannot tell "the repo has no such file"
from "this checkout is behind". That distinction decides the fix: merge
`origin/main` into the branch, or delete the reference from `music/stages.yaml`.
This check prints the distinction and fails until the tree and the stage map agree.
Cited: t_8a715681 (diverged checkout), t_5a93164a (stage advance refused in workers).

Run:  /usr/bin/python3 music/scripts/check_stage_scripts.py [--stages PATH] [--repo PATH]
Exit: 0 when every referenced path exists; 1 when any is missing.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Path-shaped tokens inside a stage prompt: word chars plus / . - _ , ending in a
# script suffix. Only .py/.sh are checked - those are the ones a stage EXECUTES.
TOKEN_RE = r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh)"
ADVANCE = "bash scripts/automation/advance-stage.sh"  # allowlisted: exists in-repo


def _run(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    ).stdout


def all_refs(repo: Path) -> list[str]:
    refs = _run(repo, "for-each-ref", "--format=%(refname:short)").splitlines()
    refs += [r for r in ("origin/main",) if r not in refs]
    return [r for r in refs if r and r != "HEAD"]


def refs_carrying(repo: Path, rel: str) -> list[str]:
    """Return the refs whose tree contains `rel` (empty list when none do)."""
    if not _run(repo, "log", "--all", "--oneline", "--diff-filter=A", "--", rel).strip():
        return []
    hits: list[str] = []
    for ref in all_refs(repo):
        if rel in _run(repo, "ls-tree", "-r", "--name-only", ref).splitlines():
            hits.append(ref)
    return hits


def referenced_paths(stages_file: Path) -> dict[str, set[str]]:
    """Map each referenced script path to the stages that name it."""
    import re
    found: dict[str, set[str]] = {}
    stage = "?"
    for line in stages_file.read_text().splitlines():
        if line.strip().startswith("- stage:"):
            stage = line.split("- stage:")[1].strip().strip('"') or "?"
        if "prompt:" not in line and "script" not in line:
            continue
        for tok in re.findall(TOKEN_RE, line):
            tok = tok.lstrip("./")
            if tok == ADVANCE:
                continue
            found.setdefault(tok, set()).add(stage)
    return found


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Check that stage-referenced scripts exist.")
    ap.add_argument("--repo", default=str(here.parents[2]))
    ap.add_argument("--stages", default=None)
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    stages = Path(args.stages) if args.stages else repo / "music" / "stages.yaml"
    if not stages.is_file():
        print(f"FAIL check_stage_scripts: no stage map at {stages}")
        return 1

    referenced = referenced_paths(stages)
    missing = {p: w for p, w in sorted(referenced.items()) if not (repo / p).exists()}
    if not missing:
        print(f"PASS check_stage_scripts: {len(referenced)} referenced script path(s) "
              f"all present in {repo}")
        return 0

    print(f"FAIL check_stage_scripts: {len(missing)} of {len(referenced)} referenced "
          f"path(s) absent from the working tree of {repo}")
    for path, where in missing.items():
        carried = refs_carrying(repo, path)
        print(f"  {path}   (named by: {', '.join(sorted(where))})")
        if carried:
            print(f"    CHECKOUT DIVERGENCE - this repo DOES carry the file, on: "
                  f"{', '.join(carried)}")
            print("    Fix: merge those refs into the checked-out branch. "
                  "Do NOT delete the reference.")
        else:
            print("    ABSENT - no ref in this repo carries it. "
                  "Fix the stage map, or add the script.")
    print("  cited: t_8a715681 (diverged checkout), t_5a93164a (stage advance refused)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
