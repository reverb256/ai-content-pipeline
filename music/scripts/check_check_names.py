#!/usr/bin/env python3
"""check_check_names -- a `check_<x>` and a `check_<x>s` in the same tree is one check.

WHY THIS EXISTS (incident 2026-10-16, cards t_9dfa74d9, t_752f02a8, t_4612d213)
--------------------------------------------------------------------------------
Seven minutes apart, both on `main`, neither aware of the other:

    music/scripts/check_brief_absences.py   15:59   t_9dfa74d9   2611770
    music/scripts/check_brief_absence.py    16:06   t_752f02a8   3766fa3

They returned contradictory verdicts on a correct brief: five of the plural
check's hits on `activist.md` were false positives, so any pass that ran it
blocked on prose. The plural was deleted by t_4612d213 (commit `cd8ec30`).

The root cause was not carelessness. Nothing in the lane looks at
`music/scripts/` as a SET. The survivor's docstring carries the lesson -- "ls
music/scripts/ before adding a check" -- but a lesson is not a check: no runner
or config referenced either script, and the lane's check matrix is a
concurrent-edit hotspot, so nothing failed until a merge collided. This is the
check that the lesson asked for.

WHAT IT CATCHES
---------------
Two files under `music/scripts/` whose stems differ only by a trailing `s`
(the shape of the pair above). Stems only: this is a NAME collision, not a
semantic one. Two checks for one CLASS needs judgement -- `check_brief_paths`
and `check_brief_figures` are both brief checks and are not a collision -- and a
guard that tried to decide that would be noisy. A near-duplicate name, however,
is mechanical and is the failure this lane just paid for.

SCOPE
-----
`music/scripts/*.py` only, stems only. The plural file this guards against is
the SAME class as the one that landed: a `check_<subject>` whose sibling is
`check_<subject>s`. A collision on any other suffix is out of scope by design.

PROVENANCE
----------
The set this check audits is the TRACKED set (`git ls-files`), not the working
tree. The plural file is on disk right now as an untracked remnant of the
incident (it was deleted by `cd8ec30`); it is not what ships, and a guard that
fails on untracked scratch would block every edit in this directory. The set
that would have caught the incident is the tracked set: both files were
tracked when they collided.

Usage:
  /usr/bin/python3 music/scripts/check_check_names.py [--repo DIR] [--selftest]
  /usr/bin/python3 music/scripts/check_check_names.py --json

Exit codes: 0 = no singular/plural pair, 1 = at least one collision, 2 = usage.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# The directory this check audits. `check_<subject>.py` is the convention; the
# collision it guards is a sibling `check_<subject>s.py` seven minutes later.
SCRIPTS_DIR = "music/scripts"
PY_SUFFIX = ".py"


def tracked_scripts(repo: Path) -> list[str]:
    """Every `music/scripts/check_*.py` the repo TRACKS, as repo-relative paths.

    The tracked set, not the working tree: the incident's plural file is on
    disk as an untracked remnant and is not what ships, so a guard that failed
    on it would block every edit in this directory instead of catching the
    class. Both colliding files were tracked when they collided.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-files", f"{SCRIPTS_DIR}/"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return []
    return sorted(line for line in proc.stdout.splitlines() if line.endswith(PY_SUFFIX))


def stem(path: str) -> str:
    """`music/scripts/check_brief_absence.py` -> `check_brief_absence`."""
    return Path(path).stem


def colliding_pairs(paths: list[str]) -> list[tuple[str, str]]:
    """Every (singular, plural) pair whose stems differ only by a trailing `s`.

    Deterministic and small: compare each stem against every other stem, and
    report a pair only when one is the other plus `s`. Both orders are
    reported once (singular first), so a reader sees the collision and not its
    mirror.
    """
    stems = {stem(p): p for p in paths}
    out: list[tuple[str, str]] = []
    for singular, spath in sorted(stems.items()):
        plural = singular + "s"
        if plural in stems and spath != stems[plural]:
            out.append((spath, stems[plural]))
    return out


def audit(repo: Path) -> tuple[list[str], list[str]]:
    """(problems, paths) for the tracked set under `SCRIPTS_DIR`.

    Pure: the only input is the repo root, so `--selftest` exercises the same
    code path the live tree goes through (no fixture directory to drift from
    the real one).
    """
    paths = tracked_scripts(repo)
    pairs = colliding_pairs(paths)
    problems: list[str] = []
    for singular_path, plural_path in pairs:
        problems.append(
            f"{singular_path} and {plural_path} are two checks for one class: "
            f"their names differ only by a trailing `s`. One of them is the "
            f"survivor of card t_4612d213 (commit `cd8ec30`) -- delete the "
            f"other rather than shipping both, or the next pass that runs them "
            f"gets contradictory verdicts on a correct brief (the incident this "
            f"guard exists for: t_9dfa74d9 / t_752f02a8).")
    return problems, paths


def run(repo: Path, quiet: bool = False, json_out: bool = False) -> int:
    problems, paths = audit(repo)
    if json_out:
        import json
        print(json.dumps({
            "scripts": len(paths),
            "collisions": [{"singular": s, "plural": p}
                           for s, p in colliding_pairs(paths)],
            "problems": problems,
        }, indent=2))
        return 1 if problems else 0

    if problems:
        if not quiet:
            for p in problems:
                print(f"  - {p}")
        print(f"FAIL check_check_names: {len(paths)} script(s), "
              f"{len(problems)} singular/plural pair(s) -- two checks for one "
              f"class under near-duplicate names")
        return 1
    print(f"PASS check_check_names: {len(paths)} script(s), no singular/plural "
          f"pair")
    return 0


def selftest() -> int:
    """Prove the detector FAILS on the incident pair and PASSES on the live tree.

    The incident pair is the exact shape this guard exists for: a `check_<x>`
    and a `check_<x>s`. The quiet pair is the case that must NOT fire -- two
    checks for one SUBJECT that are not name-collisions, which this guard
    deliberately does not judge (card t_991dc5f0: semantic duplication needs
    judgement, not a regex).
    """
    checks: list[tuple[str, bool, str]] = []

    # 1. THE INCIDENT: the pair that cost a merge. Must fire.
    incident = [f"{SCRIPTS_DIR}/check_brief_absence.py",
                f"{SCRIPTS_DIR}/check_brief_absences.py"]
    got = colliding_pairs(incident)
    ok = (len(got) == 1 and got[0] == tuple(incident)
          and stem(incident[0]) + "s" == stem(incident[1]))
    checks.append(("incident check_brief_absence/check_brief_absences FIRES",
                   ok, f"pairs={got}"))

    # 2. The reverse order reports the same pair, singular first.
    got = colliding_pairs(list(reversed(incident)))
    checks.append(("reversed order -> same pair, singular first",
                   got == [tuple(incident)], f"pairs={got}"))

    # 3. A non-colliding pair of real checks must stay quiet.
    quiet = [f"{SCRIPTS_DIR}/check_brief_paths.py",
             f"{SCRIPTS_DIR}/check_brief_figures.py"]
    checks.append(("check_brief_paths / check_brief_figures stays quiet",
                   colliding_pairs(quiet) == [],
                   f"pairs={colliding_pairs(quiet)}"))

    # 4. Self-collision is not reported (a stem is never its own plural).
    self_pair = [f"{SCRIPTS_DIR}/check_check_names.py"]
    checks.append(("a lone script reports nothing",
                   colliding_pairs(self_pair) == [],
                   f"pairs={colliding_pairs(self_pair)}"))

    # 5. The live tracked tree: the plural was deleted by `cd8ec30`, so this
    #    guard must exit 0 here -- that is the acceptance test the card states.
    repo = Path(__file__).resolve().parents[2]
    live = tracked_scripts(repo)
    live_pairs = colliding_pairs(live)
    checks.append((f"live tracked tree ({len(live)} scripts) is clean",
                   live_pairs == [],
                   f"pairs={live_pairs}"))

    # 6. A plural that is the singular of ANOTHER check does not false-fire:
    #    `check_check_names` and `check_check_name` are not a pair here
    #    because only one exists; and a real triple reports one pair.
    triple = [f"{SCRIPTS_DIR}/check_brief_absence.py",
              f"{SCRIPTS_DIR}/check_brief_absences.py",
              f"{SCRIPTS_DIR}/check_brief_absence_s.py"]
    got = colliding_pairs(triple)
    checks.append(("triple reports the trailing-s pair once",
                   len(got) == 1 and got[0] == tuple(incident[:2]),
                   f"pairs={got}"))

    width = max(len(name) for name, _, _ in checks)
    bad = 0
    for name, ok, detail in checks:
        print(f"{name:<{width}}  {'PASS' if ok else 'FAIL'}   {detail}")
        bad += 0 if ok else 1
    if bad:
        print(f"\nFAIL check_check_names --selftest: {bad} case(s) "
              f"did not reproduce")
        return 1
    print(f"\nPASS check_check_names --selftest: {len(checks)} cases "
          f"(the incident pair fires, the quiet pair stays quiet, the live "
          f"tracked tree is clean)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="check_check_names -- no two `check_<x>` / `check_<x>s` in "
                    "music/scripts/")
    ap.add_argument("--repo", default=None,
                    help="repo root (default: two levels above this script)")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress the per-pair detail lines")
    ap.add_argument("--json", action="store_true",
                    help="emit a JSON record instead of the report line")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve() if args.repo else \
        Path(__file__).resolve().parents[2]
    return run(repo, quiet=args.quiet, json_out=args.json)


if __name__ == "__main__":
    sys.exit(main())
