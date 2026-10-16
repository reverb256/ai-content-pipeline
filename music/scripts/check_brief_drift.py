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
For every `music/briefs/**/*.md` it finds two families of count.

DIVERGENCE — "N commits behind `origin/main`, M ahead" (either number may be a digit or an
English number word). Recomputed with `git rev-list --left-right --count origin/main...HEAD` →
`<behind> <ahead>`.

BLUEPRINT CENSUS — how many of the registered genres have a lyric blueprint. Recomputed from
`music/genres.yaml` (the registry loader) and the number of `music/lyrics/blueprints/*.yaml`
files. The lane writes that one fact SEVEN ways, so there are seven shapes (the first three were
here from the start; the last four were added by card t_c5a98379 after 63440da corrected 13 stale
instances the check had never seen — the shapes, with the pre-correction examples):

  S1  `<n> blueprint-less genres`                                  — `activist.md:302` "**eleven**"
  S2  `only <n> genres with a lyric blueprint`  (reversed sense: counts what HAS one)
  S3  `<n> of the <m> genres`                                      — `activist.md:303` "3 of the 14"
  S4  `<n> of <m>` with NO `genres` after the pair                 — "only 3 of the 14 exist",
                                                                     jungle-dnb.md:990 "4 of 14 blueprints"
  S5  the same pair split across two lines                         — `elemental-water.md:426-427`
  S6  a brace PATH list instead of a count                         — `blueprints/{activist,
                                                                     chill-lounge,trance}.yaml`
  S7  a bare `<n> blueprints` / `<n> lyric blueprints`             — `activist.md:582` "3 blueprints only"

S1-S3 are the original three classes. S4-S7 are the widening. Three notes on how the widening stays
signal and not noise:

  * A census count inside quotation marks is a QUOTATION, not a claim: the brief is reporting
    someone else's words (a docstring it read, the checker's own earlier FAIL line). Measured on
    `epic-orchestral-boss.md:373`, which quotes `planner.py`'s stale "(3 of 15 genres do)"
    docstring and says so in the same breath — flagging it would be the noisy-check failure this
    file's own §12 warns about. Skipped, and only the double-quoted span.
  * S7 is checked ONLY for a REPO claim. The same words also describe the DEPLOYED payload
    (`ConfigMap mining/music-pipeline-payload`, whose keys are `music__lyrics__blueprints__*`).
    That is cluster state, which this check cannot recompute from the repo — at 15:31 CDT on
    2026-10-16 the deployed ConfigMap held 38 keys and 6 of them blueprints while the repo held 7.
    A line that names the payload/cluster/pod is therefore SKIPPED and printed as a skip, never
    silently accepted and never guessed at. The context is the line plus its neighbours above and
    below, because these briefs hard-wrap: `activist.md`'s §8 bullet names the `ConfigMap
    mining/music-pipeline-payload` on one line and counts its blueprints twice more on the next
    two. The payload is not frozen either — measured 2026-10-16: 38 keys / 6 blueprints at 15:31
    CDT, 42 keys / 7 blueprints at 17:18 CDT — so no reading of it can be recomputed from the
    tree. Verifying it needs a cluster read, and the places that did one record it
    (t_0f7aed63's payload_configmap metadata; `--quiet-skips` silences the printed note).
  * S6 compares the NAMES too, not just their number: a brace expansion of the blueprints
    directory lists that directory, so the set must equal the live set.

Rules, kept narrow so the check is signal and not noise
-------------------------------------------------------
1. A claim is checked only when the marker words are present ("behind"/"ahead"; "blueprint").
2. Number words are accepted (`three`, `seven`, `eleven`, …) because this lane writes both, and
   so is emphasis around them (`**eleven**`, `*three*`, `` `6` ``) — the lane writes that too.
3. A brief may state the counts for a PAST revision if it says so on the same line ("at
   `9ebf6af`", "when written", "… 15:31 CDT"). Those are skipped: an anchored historical count is
   a fact, an unanchored one is a claim about now. This holds for EVERY class, the census classes
   included — the FAIL text below offers anchoring as the remedy for all of them, so the remedy
   has to work for all of them. (Card t_c5a98379 measured the gap: a census line carrying a clock
   stamp was checked unconditionally while the printed fix told its author to anchor it.)
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
t_55379aba (the sibling figures check, whose shape this follows), t_0f7aed63 (the 12 flagged
counts + the 13 the check could not see), t_c5a98379 (this widening), t_b976f49f (which measured
the unreachable-anchor gap and the `commentary-beds.md` brace list).
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

# S1's shape: the number may be wrapped in emphasis. `**eleven** blueprint-less genres` is a
# real line (activist.md:302) and the original `(\d+|eleven|…)` could not see it. `_EMPH` is
# inside the capture so both spellings produce the same token for `num()`.
_EMPH = r"[*_`]{0,2}"
_NUMTOK = rf"{_EMPH}(?:\d+|{'|'.join(_WORDS)})\b{_EMPH}"


def num(token: str) -> int:
    token = token.strip().strip("*_`").strip().lower()
    return _WORDS[token] if token in _WORDS else int(token)


# "15 commits behind `origin/main`, 7 ahead"  /  "**6 ahead, 15 behind**"
DIVERGE_AHEAD = re.compile(rf"({_NUMTOK})\s*(?:commits?\s+)?behind[^\n]{{0,80}}?({_NUMTOK})\s*ahead",
                           re.I)
DIVERGE_BACK = re.compile(rf"({_NUMTOK})\s*ahead[^\n]{{0,80}}?({_NUMTOK})\s*(?:commits?\s+)?behind",
                          re.I)
# the two numbers the pair must equal; git prints "<behind>\t<ahead>"
# An ANCHORED claim is a historical fact, not a claim about now: the line names the revision
# or stamps the clock time it was measured at. Unanchored "N behind / M ahead" is a claim
# about the present and must hold against the present tree. NOT widened by t_c5a98379, on
# purpose: it is the ONE escape hatch, and it stays exactly `ANCHORED`.
ANCHORED = re.compile(
    r"`[0-9a-f]{7,40}`|when written|at write time|at filing|"
    r"\b\d{1,2}:\d{2}\b|\bmeasured (?:at|on)\b", re.I)

# --- the census classes (S1-S3 original, S4-S7 added by t_c5a98379) ----------
BLUEPRINT_LESS = re.compile(rf"({_NUMTOK})\s+blueprint-(?:less|free)\s+genres", re.I)
OF_GENRES = re.compile(rf"only\s+({_NUMTOK})\s+genres?\s+with\s+a\s+lyric\s+blueprint", re.I)
NUM_OF_GENRES = re.compile(rf"({_NUMTOK})\s+of\s+(?:the\s+)?({_NUMTOK})\s+genres", re.I)
# S4: the same pair with no `genres` after it — "only 3 of the 14 exist" (activist.md:303),
# "4 of 14 blueprints" (jungle-dnb.md:990). The lookahead keeps it from double-reporting an
# S3 claim as one of its two numbers.
NUM_OF_PAIR = re.compile(rf"({_NUMTOK})\s+of\s+(?:the\s+)?({_NUMTOK})\b(?!\s*genres)", re.I)
# S7: a bare count of blueprints, no `genres` word anywhere — "3 blueprints only",
# "the three blueprints", "6 lyric blueprints". Two guards keep it honest: `(?![-_])` keeps
# "eleven blueprint-less" (S1) out of it, so one claim is reported once; `(?<![§#])` keeps a
# SECTION reference out of it ("§1 blueprint row", anime-ending.md:509 — a row label, not a count).
N_BLUEPRINTS = re.compile(rf"(?<![§#])({_NUMTOK})\s+(?:lyric\s+)?blueprints?\b(?![-_])", re.I)
# S6: a brace expansion of the blueprints directory — a file census written as a PATH, so it
# carries no count token at all. `blueprints/{activist,chill-lounge,trance}.yaml`.
BRACE_LIST = re.compile(r"blueprints?/\{([^}]+)\}")

CENSUS_PATTERNS = (BLUEPRINT_LESS, OF_GENRES, NUM_OF_GENRES, NUM_OF_PAIR, N_BLUEPRINTS,
                   BRACE_LIST)

# The DEPLOYED payload's key census is cluster state, not repo state (see the docstring, S7).
# A census claim on a line that names the cluster is a SKIP, printed, never a guess. Tested
# against the line AND its neighbours: the briefs hard-wrap, so the sentence naming the
# ConfigMap is often one line away from the count it introduces.
CLUSTER = re.compile(r"configmap|payload|music__|kubectl|\bpod\b|cronjob|in-cluster", re.I)


def in_quotes(state: bool, text: str, start: int) -> bool:
    """True when `text[start:]` sits inside a double-quoted span, given `state` at line start.

    A count inside quotation marks is a QUOTATION, not the brief's own claim: it is reporting
    someone else's words. Measured on `music/briefs/epic-orchestral-boss.md:373`, which quotes
    `planner.py`'s stale "(3 of 15 genres do)" docstring and says it is stale in the same
    sentence; and on `activist.md:904`, which quotes the sentence this check's own first draft
    wrongly flagged. Skipped — the noisy-check failure mode is the one this lane cannot afford.

    The state is threaded across lines on purpose: `activist.md:903` opens the quote that
    `:905` closes, so the line carrying the count holds no quote character at all and a
    per-line count sees nothing. Straight `"` and typographic `“ ”` both count.
    """
    now = state
    for ch in text[:start]:
        if ch == '"':
            now = not now
        elif ch == "\u201c":
            now = True
        elif ch == "\u201d":
            now = False
    return now


def quote_states(lines: list[str], fenced: list[bool]) -> list[bool]:
    """Whether each line STARTS inside an open quote. Fenced lines are not walked: a fence is
    quoted evidence with its own quoting, and the census scan never reads one."""
    states: list[bool] = []
    open_now = False
    for line, is_fenced in zip(lines, fenced):
        states.append(open_now)
        if is_fenced:
            continue
        for ch in line:
            if ch == '"':
                open_now = not open_now
            elif ch == "\u201c":
                open_now = True
            elif ch == "\u201d":
                open_now = False
    return states


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


def live_census(repo: Path) -> tuple[int, int, set[str]]:
    """(genres registered, lyric blueprints that exist, their genre names)."""
    sys.path.insert(0, str(repo / "music"))
    import registry  # noqa: PLC0415  (needs sys.path set first)
    genres = len(registry.load_registry()["genres"])
    names = {p.stem for p in (repo / "music" / "lyrics" / "blueprints").glob("*.yaml")}
    return genres, len(names), names


# ---------------------------------------------------------------------------
# the checker itself (pure, so --selftest can drive it)
# ---------------------------------------------------------------------------

def _fence_mask(lines: list[str]) -> list[bool]:
    """True for a line inside a ``` block.

    Fenced blocks are skipped: a brief's ``` block is quoted tool output (evidence), not a
    claim about the present. This pass's own §12 quotes this checker's FAIL output, and
    without the rule the checker would flag its own quotation — the same "noisy check"
    failure the OF_GENRES note below records.
    """
    mask: list[bool] = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            mask.append(True)
            continue
        mask.append(in_fence)
    return mask


def check_text(label: str, text: str, live: dict,
               skips: list[str] | None = None) -> tuple[list[str], int]:
    """Return (findings, checked_count). `live` = {"behind","ahead","genres","blueprints"}.

    `live["blueprint_names"]` is optional; S6 (the brace list) uses it when present and falls
    back to the count when it is not.

    `skips` collects the census claims on cluster lines (the deployed payload's key census).
    A caller that passes no list simply gets no skip report.
    """
    findings: list[str] = []
    checked = 0
    lines = text.splitlines()
    fenced = _fence_mask(lines)
    qstate = quote_states(lines, fenced)
    names: set[str] = live.get("blueprint_names") or set()

    def stale(lineno: int, msg: str) -> None:
        findings.append(f"{label}:{lineno}  {msg}  [STALE CENSUS]")

    def census_pair(a: str, b: str, lineno: int, note: str, phrase: str) -> None:
        """Compare an `<n> of <m>` census pair: n counts blueprints, m counts genres."""
        nonlocal checked
        checked += 1
        if num(a) != live["blueprints"] or num(b) != live["genres"]:
            stale(lineno, f'claimed "{phrase}"{note}  measured {live["blueprints"]} of the '
                          f'{live["genres"]}')

    previous = ""
    for idx, line in enumerate(lines):
        if fenced[idx]:
            previous = ""
            continue
        lineno = idx + 1

        # --- divergence: repo state always, so the cluster skip does not apply ---
        if not ANCHORED.search(line):
            for m in (DIVERGE_AHEAD, DIVERGE_BACK):
                for a, b in m.findall(line):
                    checked += 1
                    behind, ahead = (num(a), num(b)) if m is DIVERGE_AHEAD else (num(b), num(a))
                    if live.get("behind") is None:
                        continue
                    if (behind, ahead) != (live["behind"], live["ahead"]):
                        findings.append(
                            f"{label}:{lineno}  claimed \"{a} behind / {b} ahead\"  "
                            f"measured {live['behind']} behind / {live['ahead']} ahead of "
                            f"origin/main  [STALE DIVERGENCE]")

        # --- census ---
        # The context is the line, the line above and the line below: these briefs hard-wrap,
        # so the sentence naming the ConfigMap is often one line away from the count it
        # introduces (activist.md's §8 bullet names it, then counts on the next two lines).
        nxt = lines[idx + 1] if idx + 1 < len(lines) and not fenced[idx + 1] else ""
        ctx = f"{previous} {line} {nxt}"
        if CLUSTER.search(ctx):
            # Only a BLUEPRINT census is in scope at all: "8 of the 14 templates are
            # instrumental" is a different census with a different live value, and reporting it
            # as a skipped blueprint count would be noise on a line the check never examines.
            if "blueprint" in line.lower() and any(p.search(line) for p in CENSUS_PATTERNS):
                if skips is not None:
                    skips.append(f"{label}:{lineno}  {line.strip()[:150]}")
            previous = line
            continue
        if not ANCHORED.search(line):
            for m in (BLUEPRINT_LESS, OF_GENRES):
                for hit in m.finditer(line):
                    if in_quotes(qstate[idx], line, hit.start()):
                        continue
                    got = hit.group(1)
                    checked += 1
                    if m is OF_GENRES:
                        # "one of only three genres with a lyric blueprint" counts the genres
                        # that HAVE one, not the ones that lack it. Opposite direction, so it
                        # gets its own comparison — mixing the two is what made an earlier
                        # draft of this check flag a correct sentence.
                        actual = live["blueprints"]
                        if num(got) != actual:
                            stale(lineno, f'claimed "only {got} genres with a lyric blueprint"  '
                                          f'measured {actual} (music/lyrics/blueprints/*.yaml)')
                        continue
                    actual = live["genres"] - live["blueprints"]
                    if num(got) != actual:
                        stale(lineno, f'claimed "{got}" blueprint-less genres  measured {actual} '
                                      f'({live["genres"]} registered genres - '
                                      f'{live["blueprints"]} in music/lyrics/blueprints/)')
            for m in (NUM_OF_GENRES, NUM_OF_PAIR):
                for hit in m.finditer(line):
                    if "blueprint" not in line.lower() or in_quotes(qstate[idx], line,
                                                                     hit.start()):
                        continue
                    if m is NUM_OF_PAIR and hit.end() >= len(line.rstrip()) and idx + 1 < len(lines):
                        # The pair dangles at the end of the line — the shape S5 claim
                        # ("… and only 3 of 14" / "genres have a blueprint"). Skip it here ONLY
                        # when the window pass below will read the whole claim under the same
                        # guards; reporting it in both places would print one claim twice.
                        joined = line + " " + lines[idx + 1]
                        if (not fenced[idx + 1] and "blueprint" in joined.lower()
                                and not CLUSTER.search(joined) and not ANCHORED.search(joined)):
                            continue
                    # The quoted phrase is the line's own words: the classes that were already
                    # here keep their original wording, the new pair shapes print what they say.
                    phrase = (f"{hit.group(1)} of the {hit.group(2)} genres" if m is NUM_OF_GENRES
                              else hit.group(0))
                    census_pair(hit.group(1), hit.group(2), lineno, "", phrase)
            for hit in N_BLUEPRINTS.finditer(line):
                if in_quotes(qstate[idx], line, hit.start()):
                    continue
                got = hit.group(1)
                checked += 1
                if num(got) != live["blueprints"]:
                    stale(lineno, f'claimed "{got} blueprints"  measured {live["blueprints"]} '
                                  f'(music/lyrics/blueprints/*.yaml)')
            for hit in BRACE_LIST.finditer(line):
                if in_quotes(qstate[idx], line, hit.start()):
                    continue
                entries = [e.strip().strip("`") for e in hit.group(1).split(",") if e.strip()]
                checked += 1
                got = {e[:-5] if e.endswith(".yaml") else e for e in entries}
                if names:
                    if got != names:
                        missing = sorted(names - got)
                        extra = sorted(got - names)
                        why = []
                        if missing:
                            why.append("missing " + ", ".join(missing))
                        if extra:
                            why.append("not a blueprint: " + ", ".join(extra))
                        stale(lineno, f'brace list names {len(entries)} blueprint(s)  measured '
                                      f'{len(names)} ({"; ".join(why)})')
                elif len(entries) != live["blueprints"]:
                    stale(lineno, f'brace list names {len(entries)} blueprint(s)  measured '
                                  f'{live["blueprints"]} (music/lyrics/blueprints/*.yaml)')
        previous = line

    # --- S5: a census pair split across two lines. Both regexes are single-line, so the pair
    # is re-scanned over each adjacent unfenced pair and reported only when the match CROSSES
    # the boundary — a within-line match is already reported above, and reporting it twice
    # would be the noise this check cannot afford.
    for idx in range(len(lines) - 1):
        if fenced[idx] or fenced[idx + 1]:
            continue
        joined = lines[idx] + " " + lines[idx + 1]
        if "blueprint" not in joined.lower() or CLUSTER.search(joined):
            continue
        if ANCHORED.search(joined):
            continue
        boundary = len(lines[idx])
        for m in (NUM_OF_GENRES, NUM_OF_PAIR):
            for hit in m.finditer(joined):
                if not (hit.start() < boundary < hit.end()):
                    # entirely inside one line — already checked above
                    continue
                if in_quotes(qstate[idx], joined, hit.start()):
                    continue
                a, b = hit.group(1), hit.group(2)
                census_pair(a, b, idx + 1, f" (the pair is split across lines {idx}–{idx + 1})",
                            " ".join(hit.group(0).split()))
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
    """A case per shape (S1-S7), the two original divergence cases, and one per escape — the
    anchored rule, the fence, the quotation and the cluster skip. Every case is a real sentence
    from this lane's briefs, with only the number changed where the stale variant is wanted."""
    live = {"behind": 15, "ahead": 29, "genres": 14, "blueprints": 3,
            "blueprint_names": {"activist", "chill-lounge", "trance"}}
    cases: list[tuple[str, str, int, int, int]] = [
        # name, text, want findings, want checked, want skips
        ("divergence current",
         "the checkout is 15 commits behind `origin/main`, 29 ahead\n", 0, 1, 0),
        ("divergence stale",
         "the checkout is 15 commits behind `origin/main`, 7 ahead\n", 1, 1, 0),
        ("S1 emphasis-stale",
         "fallback that the **seven** blueprint-less genres take (`load_blueprint()` returns `{}`\n",
         1, 1, 0),
        ("S1 emphasis-current",
         "fallback that the **eleven** blueprint-less genres take\n", 0, 1, 0),
        ("S2 reversed sense current",
         "Activist is one of only three genres with a lyric blueprint\n", 0, 1, 0),
        ("S2 reversed sense stale",
         "only 9 genres with a lyric blueprint\n", 1, 1, 0),
        ("S3 `of the` pair current",
         "and only 3 of the 14 genres have a lyric blueprint\n", 0, 1, 0),
        ("S3 `of the` pair stale",
         "and only 6 of the 14 genres have a lyric blueprint\n", 1, 1, 0),
        ("S4 pair, no `genres` current",
         "when `music/lyrics/blueprints/<genre>.yaml` is absent, and only 3 of the 14 exist\n",
         0, 1, 0),
        ("S4 pair, no `genres` stale",
         "and only 2 of the 14 exist — no blueprint for this genre\n", 1, 1, 0),
        ("S5 pair split across lines current",
         "The planner falls back to `or 100` (`planner.py:470`), and **only 3 of 14\n"
         "   genres have a blueprint** (`activist`). So this genre plans at 100\n", 0, 1, 0),
        ("S5 pair split across lines stale",
         "The planner falls back to `or 100` (`planner.py:470`), and **only 9 of 14\n"
         "   genres have a blueprint** (`activist`). So this genre plans at 100\n", 1, 1, 0),
        ("S6 brace list current",
         "`blueprints/{activist,chill-lounge,trance}.yaml`. No chiptune lyric dir.\n",
         0, 1, 0),
        ("S6 brace list stale",
         "`music/lyrics/blueprints/{activist,chill-lounge}.yaml` — the three that exist\n",
         1, 1, 0),
        ("S7 bare count current",
         "template, `lyric_video.mp4` does not); 3 blueprints only; autonomy all `advisory`;\n",
         0, 1, 0),
        ("S7 bare count stale",
         "carries `music/genres.yaml`, the six blueprints, the 14 prompt templates\n", 1, 1, 0),
        ("anchored divergence skipped",
         "this checkout is 15 behind / 7 ahead of `origin/main` when written\n"
         "the repo was at `9ebf6af`, 15 commits behind `origin/main`, 7 ahead\n", 0, 0, 0),
        ("anchored census skipped (t_b976f49f gap)",
         "- **Blueprint census, re-measured 2026-10-16 15:31 CDT:** 6 of the 14 genres carry one\n",
         0, 0, 0),
        ("quoted census skipped (epic-orchestral-boss.md:373)",
         "`planner.py`'s docstring \"(3 of 15 genres do)\" is stale, not a behaviour\n", 0, 0, 0),
        ("quoted census skipped across a wrapped line (activist.md:903)",
         "Its own first draft flagged a correct sentence (\"one of\n"
         "only *three* genres with a lyric blueprint\" counts the genres that HAVE one\n", 0, 0, 0),
        ("cluster census skipped, not guessed (S7 note)",
         "the payload ConfigMap carries the three blueprints and `music__genres.yaml`\n", 0, 0, 1),
        ("cluster context reaches the hard-wrapped line",
         "the render payload (`ConfigMap mining/music-pipeline-payload`, mounted at `/payload`)\n"
         "   carries `music/genres.yaml`, the six blueprints, the planner\n", 0, 0, 1),
        ("fenced quote skipped",
         "```\n  brief:1  claimed \"six\" blueprint-less genres  measured 8\n```\n", 0, 0, 0),
    ]
    failures: list[str] = []
    for name, text, want_f, want_c, want_s in cases:
        skips: list[str] = []
        found, seen = check_text(name, text, live, skips)
        ok = len(found) == want_f and seen == want_c and len(skips) == want_s
        if not ok:
            failures.append(f"{name}: findings={len(found)} (want {want_f}), checked={seen} "
                            f"(want {want_c}), skips={len(skips)} (want {want_s})")
        for f in found:
            if want_f == 0:
                failures.append(f"  false positive in {name}: {f}")
    print(f"SELFTEST {'PASS' if not failures else 'FAIL'} check_brief_drift: "
          f"{len(cases)} case(s), one per shape (S1-S7) plus divergence, the anchored rule and "
          f"the cluster skip")
    for f in failures:
        print("  " + f)
    return 0 if not failures else 1


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
    genres, bps, names = live_census(repo)
    live = {"behind": div[0] if div else None, "ahead": div[1] if div else None,
            "genres": genres, "blueprints": bps, "blueprint_names": names}

    rels = args.briefs or (briefs_rev(repo, args.rev) if args.rev else briefs_worktree(repo))
    findings: list[str] = []
    skips: list[str] = []
    checked = 0
    for rel in rels:
        f, c = check_text(rel, read(repo, rel, args.rev), live, skips)
        findings.extend(f)
        checked += c

    where = f"revision {args.rev}" if args.rev else f"worktree {repo}"
    if skips and not args.quiet_skips:
        print(f"SKIP check_brief_drift: {len(skips)} census claim(s) name the deployed payload "
              f"(cluster state, not repo state) — not recomputed here:")
        for s in skips:
            print("  " + s)
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
