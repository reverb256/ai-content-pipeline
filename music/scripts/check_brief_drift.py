#!/usr/bin/env python3
"""check_brief_drift — recompute the LIVE repo counts a brief cites, so they cannot age silently.

WHY THIS EXISTS
---------------
INCIDENT (2026-10-16, card t_b7dd5655, the duplicate of t_ace3bfb1 — `music/briefs/activist.md`)

Three figures in that brief were each a real measurement from a real run and were each WRONG by
the time the twin card read them, because they describe live repo state that keeps moving:

  1. header/§11: "**15 commits behind `origin/main`, 7 ahead**" — measured again at the same
     checkout: 15 behind / **29** ahead. Other workers landed ~22 commits in the shared tree
     between the write and the verification.
  2. §6: "the flat 100 fallback that the **seven** blueprint-less genres get" — there are
     **eleven**: 14 registered genres minus the 3 files in `music/lyrics/blueprints/`.
  3. header/§2: "Live re-score today: **7.00**" — the oracle re-score measured **7.20** the same
     day (`trend_signal` fell back to 5.0 instead of 3.0). Not covered here: that one is a
     network-dependent run, filed under `check_brief_figures.py`'s scope note instead.

`check_brief_figures.py` cannot see any of these. It recomputes figures that carry a UNIT
(`chars`, `bytes`, `B`, `lines`) next to a named file. "7 ahead" and "seven blueprint-less
genres" carry no unit and no file, so they were skipped, and a stale count sat in a committed
brief. This check covers exactly that hole: counts this repo can prove, with no artifact token
needed.

WHAT IT DOES
------------
For every `music/briefs/**/*.md` it finds two families of count:

  * DIVERGENCE — "N commits behind `origin/main`, M ahead" (either number may be a digit or an
    English number word). Recomputed with
    `git rev-list --left-right --count origin/main...HEAD` → `<behind> <ahead>`.
  * BLUEPRINT CENSUS — "<n> blueprint-less genres" and "<n> of the <m> genres" / "only <n>
    genres with a lyric blueprint". Recomputed from `music/genres.yaml` (the registry loader)
    and the number of `music/lyrics/blueprints/*.yaml` files.

Rules, kept narrow so the check is signal and not noise
-------------------------------------------------------
1. A claim is checked only when the marker words are present ("behind"/"ahead"; "blueprint").
2. Number words are accepted (`three`, `seven`, `eleven`, …) because this lane writes both.
3. A brief may state the counts for a PAST revision if it says so on the same line ("at
   `9ebf6af`", "when written"). Those are skipped: an anchored historical count is a fact, an
   unanchored one is a claim about now.
4. `--rev REV` reads the briefs as of REV, so a pre-correction revision can be tested.

Exit codes: 0 = every checked count matches, 1 = at least one mismatch, 2 = usage error.

Usage:
  /usr/bin/python3 music/scripts/check_brief_drift.py [--repo DIR] [--rev REV] [--quiet-skips]
  /usr/bin/python3 music/scripts/check_brief_drift.py --briefs music/briefs/activist.md
  /usr/bin/python3 music/scripts/check_brief_drift.py --selftest

Related checks (deliberately not duplicated here)
-------------------------------------------------
  * `music/scripts/check_brief_figures.py` — figures WITH a unit and a named artifact.
  * `music/scripts/check_brief_paths.py` — do cited paths resolve.
  * `music/scripts/check_stage_scripts.py` — do stage-referenced scripts exist here.

cited: t_b7dd5655 (this incident), t_ace3bfb1 (the brief), t_8a715681 (the divergence itself),
t_55379aba (the sibling figures check, whose shape this follows).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

BRIEF_GLOB = "music/briefs/**/*.md"

_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
          "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
          "fourteen": 14, "fifteen": 15, "sixteen": 16}
_NUMPAT = r"(?:\d+|" + "|".join(_WORDS) + r")"


def num(token: str) -> int:
    token = token.strip().lower()
    return _WORDS[token] if token in _WORDS else int(token)


# "15 commits behind `origin/main`, 7 ahead"  /  "**6 ahead, 15 behind**"
DIVERGE_AHEAD = re.compile(rf"({_NUMPAT})\s*(?:commits?\s+)?behind[^\n]{{0,80}}?({_NUMPAT})\s*ahead",
                           re.I)
DIVERGE_BACK = re.compile(rf"({_NUMPAT})\s*ahead[^\n]{{0,80}}?({_NUMPAT})\s*(?:commits?\s+)?behind",
                          re.I)
# the two numbers the pair must equal; git prints "<behind>\t<ahead>"
# An ANCHORED claim is a historical fact, not a claim about now: the line names the revision
# or stamps the clock time it was measured at. Unanchored "N behind / M ahead" is a claim
# about the present and must hold against the present tree.
ANCHORED = re.compile(
    r"`[0-9a-f]{7,40}`|when written|at write time|at filing|"
    r"\b\d{1,2}:\d{2}\b|\bmeasured (?:at|on)\b", re.I)

BLUEPRINT_LESS = re.compile(rf"({_NUMPAT})\s+blueprint-(?:less|free)\s+genres", re.I)
OF_GENRES = re.compile(rf"only\s+({_NUMPAT})\s+genres?\s+with\s+a\s+lyric\s+blueprint", re.I)
NUM_OF_GENRES = re.compile(rf"({_NUMPAT})\s+of\s+(?:the\s+)?({_NUMPAT})\s+genres", re.I)


# ---------------------------------------------------------------------------
# live values
# ---------------------------------------------------------------------------

def live_divergence(repo: Path, branch: str = "origin/main") -> tuple[int, int] | None:
    res = subprocess.run(["git", "-C", str(repo), "rev-list", "--left-right", "--count",
                          f"{branch}...HEAD"], capture_output=True, text=True, check=False)
    if res.returncode != 0:
        return None
    behind, ahead = res.stdout.split()
    return int(behind), int(ahead)


def live_census(repo: Path) -> tuple[int, int]:
    """(genres registered, lyric blueprints that exist)."""
    sys.path.insert(0, str(repo / "music"))
    import registry  # noqa: PLC0415  (needs sys.path set first)
    genres = len(registry.load_registry()["genres"])
    bps = len(list((repo / "music" / "lyrics" / "blueprints").glob("*.yaml")))
    return genres, bps


# ---------------------------------------------------------------------------
# the checker itself (pure, so --selftest can drive it)
# ---------------------------------------------------------------------------

def check_text(label: str, text: str, live: dict) -> tuple[list[str], int]:
    """Return (findings, checked_count). `live` = {"behind","ahead","genres","blueprints"}.

    Fenced blocks are skipped: a brief's ``` block is quoted tool output (evidence), not a
    claim about the present. This pass's own §12 quotes this checker's FAIL output, and
    without the rule the checker would flag its own quotation — the same "noisy check"
    failure the OF_GENRES note below records.
    """
    findings: list[str] = []
    checked = 0
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in (DIVERGE_AHEAD, DIVERGE_BACK):
            for a, b in m.findall(line):
                if ANCHORED.search(line):
                    continue
                checked += 1
                behind, ahead = (num(a), num(b)) if m is DIVERGE_AHEAD else (num(b), num(a))
                if live.get("behind") is None:
                    continue
                if (behind, ahead) != (live["behind"], live["ahead"]):
                    findings.append(
                        f"{label}:{lineno}  claimed \"{a} behind / {b} ahead\"  "
                        f"measured {live['behind']} behind / {live['ahead']} ahead of "
                        f"origin/main  [STALE DIVERGENCE]")
        for m in (BLUEPRINT_LESS, OF_GENRES):
            for got in m.findall(line):
                checked += 1
                if m is OF_GENRES:
                    # "one of only three genres with a lyric blueprint" counts the genres
                    # that HAVE one, not the ones that lack it. Opposite direction, so it
                    # gets its own comparison — mixing the two is what made an earlier
                    # draft of this check flag a correct sentence.
                    actual = live["blueprints"]
                    if num(got) != actual:
                        findings.append(
                            f"{label}:{lineno}  claimed \"only {got} genres with a lyric "
                            f"blueprint\"  measured {actual} "
                            f"(music/lyrics/blueprints/*.yaml)  [STALE CENSUS]")
                    continue
                actual = live["genres"] - live["blueprints"]
                if num(got) != actual:
                    findings.append(
                        f"{label}:{lineno}  claimed \"{got}\" blueprint-less genres  "
                        f"measured {actual} ({live['genres']} registered genres - "
                        f"{live['blueprints']} in music/lyrics/blueprints/)  [STALE CENSUS]")
        for a, b in NUM_OF_GENRES.findall(line):
            if "blueprint" not in line.lower():
                continue
            checked += 1
            if num(a) != live["blueprints"] or num(b) != live["genres"]:
                findings.append(
                    f"{label}:{lineno}  claimed \"{a} of the {b} genres\"  measured "
                    f"{live['blueprints']} of the {live['genres']}  [STALE CENSUS]")
    return findings, checked


def briefs_worktree(repo: Path) -> list[str]:
    return sorted(str(p.relative_to(repo)) for p in repo.glob(BRIEF_GLOB) if p.is_file())


def briefs_rev(repo: Path, rev: str) -> list[str]:
    res = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", rev],
                         capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise SystemExit(f"FATAL: {rev} is not a revision in {repo}")
    return sorted(f for f in res.stdout.splitlines()
                  if f.startswith("music/briefs/") and f.endswith(".md"))


def read(repo: Path, rel: str, rev: str | None) -> str:
    if rev:
        res = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"],
                             capture_output=True, text=True, check=False)
        return res.stdout if res.returncode == 0 else ""
    return (repo / rel).read_text(encoding="utf-8")


def selftest() -> int:
    live = {"behind": 15, "ahead": 29, "genres": 14, "blueprints": 3}
    good = ("the checkout is 15 commits behind `origin/main`, 29 ahead\n"
            "the flat 100 fallback that the eleven blueprint-less genres get\n"
            "Activist is one of only three genres with a lyric blueprint\n"
            "and only 3 of the 14 exist\n")
    bad = ("the checkout is 15 commits behind `origin/main`, 7 ahead\n"
           "the flat 100 fallback that the seven blueprint-less genres get\n"
           "only 9 genres with a lyric blueprint\n")
    anchored = ("this checkout is 15 behind / 7 ahead of `origin/main` when written\n"
                "the repo was at `9ebf6af`, 15 commits behind `origin/main`, 7 ahead\n")
    f_bad, c_bad = check_text("bad", bad, live)
    f_good, c_good = check_text("good", good, live)
    f_anch, c_anch = check_text("anchored", anchored, live)
    ok = not f_good and c_good == 3 and len(f_bad) == 3 and c_anch == 0 and not f_anch
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_brief_drift: "
          f"current-claims flagged={len(f_good)} (want 0), checked={c_good} (want 3), "
          f"stale-claims flagged={len(f_bad)} (want 3), anchored skipped={not f_anch}")
    for f in f_good:
        print("  (false positive)", f)
    for f in f_bad:
        print("  (caught)", f)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="recompute the live repo counts a brief cites")
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--rev", default=None, help="check the briefs as of this revision")
    ap.add_argument("--branch", default="origin/main")
    ap.add_argument("--briefs", action="append", default=None, help="only these briefs")
    ap.add_argument("--quiet-skips", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    div = live_divergence(repo, args.branch)
    genres, bps = live_census(repo)
    live = {"behind": div[0] if div else None, "ahead": div[1] if div else None,
            "genres": genres, "blueprints": bps}

    rels = args.briefs or (briefs_rev(repo, args.rev) if args.rev else briefs_worktree(repo))
    findings: list[str] = []
    checked = 0
    for rel in rels:
        f, c = check_text(rel, read(repo, rel, args.rev), live)
        findings.extend(f)
        checked += c

    where = f"revision {args.rev}" if args.rev else f"worktree {repo}"
    if findings:
        print(f"FAIL check_brief_drift: {len(findings)} stale count(s) in {where}")
        for f in findings:
            print("  " + f)
        print(f"  {checked} count(s) checked; live: {live['behind']} behind / {live['ahead']} "
              f"ahead of {args.branch}, {live['genres']} genres, {live['blueprints']} blueprints")
        print("  Fix: correct the count in the citing brief, or anchor it to a revision on the "
              "same line (a historical count is a fact; an unanchored one is a claim about now).")
        return 1
    print(f"PASS check_brief_drift: {checked} live count(s) across {len(rels)} brief(s) match "
          f"{where} ({live['behind']} behind / {live['ahead']} ahead, {live['genres']} genres, "
          f"{live['blueprints']} blueprints)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
