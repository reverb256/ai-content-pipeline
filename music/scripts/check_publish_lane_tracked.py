#!/usr/bin/env python3
"""Check that the publish lane's deliverables are TRACKED here, not just on disk.

WHY THIS EXISTS (incident 2026-10-16, cards t_9682a610 / t_ce063b87 / t_14d438ea):
the itch.io + Gumroad adapters, `music/docs/GLASS-BREAK.md`, `music/analytics/` and
`music/lanes/` existed on exactly one ref, `origin/wip/atlas-backup-20261014` @
3882292, which is `origin/main` + one commit that adds 119 files. Two cards that
named those files were already `done`. Nothing on `main` backed their `done` state,
and a live writer was hand-extracting single files out of that ref into the working
tree — untracked, so a later `git clean` takes them away and the tree looks
delivered while git holds nothing.

Three states must not be confused, and a `ls` cannot tell them apart:

  tracked                  the file is in HEAD; the deliverable has a home.
  PRESENT BUT UNTRACKED    extracted from a ref by hand (the 14:28 state above).
  ABSENT (+ refs listing)  no home on this branch, but some ref does carry it:
                           a checkout that is behind, or a stranded WIP ref.

Run:  /usr/bin/python3 music/scripts/check_publish_lane_tracked.py [--repo PATH]
Exit: 0 when every deliverable is tracked in the checked-out branch; 1 otherwise.

Cited: t_9682a610 (this check), t_ce063b87 (publish adapters), t_14d438ea
(GLASS-BREAK checklist), t_8a715681 (the reconcile that carded the strand).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# path -> who names it. Keep this list to artifacts a card promised: a file that
# nobody promised belongs in a stage map or a runbook, not in a hard-coded list.
DELIVERABLES: dict[str, str] = {
    "music/publish/itchio.py": "t_ce063b87 publish adapter (butler)",
    "music/publish/gumroad.py": "t_ce063b87 publish adapter (Gumroad API)",
    "music/publish/playwright/__init__.py": "t_ce063b87/t_f247f8cd playwright package",
    "music/publish/playwright/_check_env.py": "t_f247f8cd playwright env probe",
    "music/publish/playwright/distrokid.py": "t_f247f8cd playwright adapter",
    "music/publish/playwright/fab.py": "t_f247f8cd playwright adapter",
    "music/publish/playwright/session.py": "t_f247f8cd shared session helper",
    "music/publish/playwright/splice.py": "t_f247f8cd playwright adapter",
    "music/publish/playwright/unity.py": "t_f247f8cd playwright adapter",
    "music/docs/GLASS-BREAK.md": "t_14d438ea provisioning checklist",
    "music/analytics/__init__.py": "lane ROI analytics lane",
    "music/analytics/__main__.py": "lane ROI analytics lane",
    "music/analytics/digest.py": "lane ROI analytics lane",
    "music/analytics/distrokid_mail_watch.py": "lane ROI analytics lane",
    "music/analytics/distrokid_parser.py": "lane ROI analytics lane",
    "music/analytics/oracle_updater.py": "lane ROI analytics lane",
    "music/analytics/roi_calculator.py": "lane ROI analytics lane",
    "music/analytics/track_record.py": "lane ROI analytics lane",
    "music/analytics/youtube_fetcher.py": "lane ROI analytics lane",
    "music/lanes/direct-license.py": "music-producer SOUL, lane module",
    "music/lanes/game-assets.py": "music-producer SOUL, lane module",
    "music/lanes/streaming.py": "music-producer SOUL, lane module",
    "music/lanes/sync.py": "music-producer SOUL, lane module",
}
# The ref this incident stranded. Used only to print provenance, never to assert.
STRAND_REF = "3882292"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    ).stdout


def tracked_paths(repo: Path) -> set[str]:
    return set(_git(repo, "ls-files").splitlines())


def refs_carrying(repo: Path, rel: str) -> list[str]:
    """Refs whose tree contains `rel` (empty when no ref in this repo does)."""
    refs = _git(repo, "for-each-ref", "--format=%(refname:short)").splitlines()
    hits = []
    for ref in refs:
        if not ref or ref == "HEAD":
            continue
        if rel in _git(repo, "ls-tree", "-r", "--name-only", ref).splitlines():
            hits.append(ref)
    return hits


def syntax_error(path: Path) -> str:
    """compile() without writing a .pyc, so the check never dirties the tree."""
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except (SyntaxError, UnicodeDecodeError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return ""


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(
        description="Every publish-lane deliverable must be tracked in this checkout.")
    ap.add_argument("--repo", default=str(here.parents[2]))
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"FAIL check_publish_lane_tracked: no git checkout at {repo}")
        return 1

    tracked = tracked_paths(repo)
    broken: list[tuple[str, str, str]] = []  # path, state, owner
    for rel, owner in sorted(DELIVERABLES.items()):
        state = ""
        if rel in tracked:
            # Only Python is compiled: GLASS-BREAK.md is prose and must not be parsed.
            err = syntax_error(repo / rel) if rel.endswith(".py") else ""
            if err:
                state = f"SYNTAX ERROR ({err})"
        elif (repo / rel).exists():
            state = "PRESENT BUT UNTRACKED"
        else:
            state = "ABSENT"
        if state:
            broken.append((rel, state, owner))

    drifted = []
    for rel in sorted(DELIVERABLES):
        if rel not in tracked:
            continue
        ref_blob = _git(repo, "rev-parse", f"{STRAND_REF}:{rel}").strip()
        if not ref_blob:
            continue  # ref not in this repo: nothing to compare, not a finding
        head_blob = _git(repo, "rev-parse", f"HEAD:{rel}").strip()
        if head_blob and head_blob != ref_blob:
            drifted.append(rel)

    if not broken:
        print(f"PASS check_publish_lane_tracked: {len(DELIVERABLES)} publish-lane "
              f"deliverable(s) tracked in {repo}")
        if drifted:
            print(f"  NOTE {len(drifted)} deliverable(s) differ from the copy {STRAND_REF} "
                  f"introduced (provenance changed, not a failure): {', '.join(drifted)}")
        return 0

    print(f"FAIL check_publish_lane_tracked: {len(broken)} of {len(DELIVERABLES)} "
          f"deliverable(s) have no home in the checked-out branch of {repo}")
    for rel, state, owner in broken:
        print(f"  {rel}   [{state}]  named by: {owner}")
        if state == "PRESENT BUT UNTRACKED":
            print("    Fix: `git add` it in the branch that owns it, or delete it — an "
                  "untracked deliverable is not delivered.")
            continue
        carried = refs_carrying(repo, rel)
        if carried:
            print(f"    STRANDED/UNMERGED - a ref in this repo does carry the file: "
                  f"{', '.join(carried)}")
            print("    Fix: merge that ref into the checked-out branch, or land the path "
                  "explicitly. Do NOT re-extract it by hand.")
        else:
            print("    ABSENT - no ref in this repo carries it. The deliverable was never "
                  "committed anywhere.")
    print(f"  cited: t_9682a610 ({STRAND_REF} strand), t_ce063b87, t_14d438ea")
    return 1


if __name__ == "__main__":
    sys.exit(main())
