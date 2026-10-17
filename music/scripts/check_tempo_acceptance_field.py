#!/usr/bin/env python3
"""check_tempo_acceptance_field — a lane text may not state a tempo acceptance that names no field.

WHY THIS EXISTS
---------------
Every genre queue card written by this lane so far was accepted on this bullet:

    measured tempo is within a few BPM of 92 (do not trust the plan — measure the audio)

That bullet names no FIELD of the tool it points at. Until `ai-content-pipeline`
90c4d0c (card `t_ed609eb0`) the tool could not satisfy it for a percussion-free
genre at all: `music/rubrics/measure.py::_bpm()` folded 0.5 / 1.0 / 2.0 only from
its whole-band argmax, and on the elemental-air render that argmax sat at the
60 BPM END of the lag search range — so the 92 BPM anchor never entered
`bpm_candidates`, and the card's own acceptance could neither pass nor fail
honestly (`bpm 60.1`, conf 0.369; the same tool returned 60.1 for a control that
is really 120 BPM).

The naming rule is now the authoritative text in `music/rubrics/README.md`,
section "Tempo: what the tool measures, and what it does not" -> "The acceptance
rule for a percussion-free genre" (card `t_ed609eb0`). Card `t_f5f703ea` is this
check: the two closed queue cards got the corrected wording in COMMENTS (246,
247), and a worker cannot edit another card's body — so the rule needed a
DETECTOR, not another comment.

WHAT IT CHECKS
--------------
A LINE that makes a tempo claim of one of two shapes must name the field the
claim is judged by. The field may sit on the claim line or on the two lines
under it, so a wrapped bullet is read whole.

  T1  the retired shape — `within (a few|N) BPM of ...`. This is the incident's
      own wording, and nothing else in the lane writes it.
  T2  a `tempo:` line — a line whose content is labelled `tempo:` and that names
      a BPM target or `measure.py`. This is the shape the canonical bullet, and
      any future acceptance bullet, uses.

Field tokens: `ac_at_anchor`, `bpm_candidates`, `bpm_pulse`. A claim that names
none FAILS — that is the shape under which a false FAIL and a silent pass both
lived on one card.

WHAT IT DELIBERATELY DOES NOT FLAG (each measured against the live tree)
-----------------------------------------------------------------------
* A PLAN-side acceptance ("the plan's `bpm` field must read 150"). It judges the
  plan, not the rendered audio; `music/briefs/elemental-fire.md`,
  `elemental-water.md` and `activist.md` state exactly that, and card
  `t_f5f703ea` §Do 3 says to leave those alone.
* Prose that names `measure.py` and a BPM without accepting anything — e.g.
  `music/briefs/jungle-dnb.md:603`, the A/B test plan ("once with
  `style_weight = 0.9` (→ 168 BPM) ... and measure both with `measure.py`"), and
  the re-measurement TABLE at `:1009`, where a whole markdown table is one block.
  Neither claims a tempo acceptance, so neither is a claim. Both are selftest
  cases below.
* A QUOTATION of the retired wording. A block whose every line is a blockquote
  (`> ...`), or that carries a strikethrough span (`~~...~~`), is a citation or a
  struck-out record, not a live acceptance — `t_f5f703ea`'s own body quotes the
  retired bullet to explain it, and comment 246 strikes it out to replace it.

SOURCES (both halves of the card's "Done when")
-----------------------------------------------
  1. `music/briefs/**/*.md` — a brief that states an audio-measured tempo
     acceptance must carry the field.
  2. the LIVE music board, read-only (`tasks.body`), for every card that is NOT
     `done` and NOT `archived`. Those are the cards a worker will still be judged
     by. Closed cards are the record and are skipped on purpose: the two cards of
     the incident keep their retired wording in their bodies, with the correction
     in comments 246/247, and re-reading them every day would be noise, not a
     detector. Comments are never scanned for the same reason — a comment may
     quote the retired bullet to strike it out, and that is the fix happening.

The board db is read DIRECTLY and READ ONLY, like `check_oracle_board.py`: inside
a dispatcher-spawned worker the `hermes kanban` CLI is fenced for mutations, so a
check built on the CLI cannot run where the checks are run.

Run:  /usr/bin/python3 music/scripts/check_tempo_acceptance_field.py [--repo PATH]
                                                                   [--db PATH]
                                                                   [--briefs-only]
      /usr/bin/python3 music/scripts/check_tempo_acceptance_field.py --selftest
Exit: 0 = every tempo acceptance names its field, 1 = at least one does not,
      2 = usage error, 3 = could not run (no repo, no board db).

cited: t_f5f703ea (this check), t_ed609eb0 (the measurement fix + the
authoritative rule), t_b8afb055 / t_909069f0 (the two queue cards the rule was
written for; corrected in comments 246/247).
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path.home() / ".hermes/kanban/boards/music/kanban.db"
HERE = Path(__file__).resolve()
DEFAULT_REPO = HERE.parents[2]

# The field names the rule requires. Any one of them makes the acceptance
# judgeable; the retired wording names none of them.
FIELD_TOKENS = ("ac_at_anchor", "bpm_candidates", "bpm_pulse")

# T1 — the incident's own wording.
RETIRED = re.compile(r"within\s+(?:a few|\d+)\s*BPM\s+of", re.IGNORECASE)
# T2 — a line labelled `tempo:` (list, bullet or quote markers allowed).
TEMPO_LABEL = re.compile(r"^[\s>*\-•\d.)]*tempo\s*:", re.IGNORECASE)
BPM_TARGET = re.compile(r"\b\d{2,3}\s*BPM\b")
TOOL = "measure.py"

LOOKAHEAD = 2  # the field may sit on the two lines under a wrapped claim

# Cards whose acceptance nobody will be judged by again.
SKIP_STATUS = ("done", "archived")

FIX = ("      fix: carry the canonical bullet verbatim — it is quoted in\n"
       "      music/rubrics/README.md, section \"The acceptance rule for a\n"
       "      percussion-free genre\" (card t_ed609eb0).")


def blocks_of(text: str) -> list[list[tuple[int, str]]]:
    """Blank-line-separated blocks of (1-based line number, raw line)."""
    out: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for lineno, line in enumerate((text or "").splitlines(), 1):
        if line.strip():
            current.append((lineno, line))
            continue
        if current:
            out.append(current)
            current = []
    if current:
        out.append(current)
    return out


def is_citation(block: list[tuple[int, str]]) -> bool:
    """A blockquote, or a struck-out record: quoted, not asserted."""
    lines = [line for _, line in block if line.strip()]
    if any("~~" in line for line in lines):
        return True
    return bool(lines) and all(line.strip().startswith(">") for line in lines)


def triggers(line: str) -> bool:
    if RETIRED.search(line):
        return True
    return bool(TEMPO_LABEL.match(line)) and bool(
        BPM_TARGET.search(line) or TOOL in line)


def unfielded_claims(text: str) -> list[tuple[int, str]]:
    """Every tempo acceptance in `text` that names no field, as (line, text)."""
    found: list[tuple[int, str]] = []
    for block in blocks_of(text):
        if is_citation(block):
            continue
        for pos, (lineno, line) in enumerate(block):
            if not triggers(line):
                continue
            window = " ".join(l for _, l in block[pos: pos + 1 + LOOKAHEAD]).lower()
            if any(tok in window for tok in FIELD_TOKENS):
                continue
            found.append((lineno, line))
    return found


def brief_paths(repo: Path) -> list[Path]:
    return sorted(p for p in repo.glob("music/briefs/**/*.md") if p.is_file())


def open_cards(db: Path) -> list[tuple[str, str, str]]:
    """(id, status, body) for every card a worker can still be judged by."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        placeholders = ",".join("?" for _ in SKIP_STATUS)
        rows = con.execute(
            f"select id, coalesce(status,''), coalesce(body,'') from tasks "
            f"where coalesce(status,'') not in ({placeholders})", SKIP_STATUS
        ).fetchall()
    finally:
        con.close()
    return [(str(r[0]), str(r[1]), str(r[2])) for r in rows]


def scan(repo: Path, db: Path | None) -> tuple[list[str], list[str], list[str]]:
    """Returns (failures, checked_labels, notes)."""
    failures: list[str] = []
    checked: list[str] = []
    notes: list[str] = []

    for path in brief_paths(repo):
        rel = path.relative_to(repo).as_posix()
        checked.append(rel)
        for lineno, line in unfielded_claims(path.read_text(encoding="utf-8")):
            failures.append(
                f"  {rel}:{lineno}  tempo acceptance names no field\n"
                f"      {line.strip()[:110]}\n" + FIX)

    if db is None:
        notes.append("board: skipped (--briefs-only)")
    elif not Path(db).exists():
        notes.append(f"board: could not read {db} (absent)")
    else:
        for card_id, status, body in open_cards(Path(db)):
            checked.append(f"{card_id} [{status}]")
            for lineno, line in unfielded_claims(body):
                failures.append(
                    f"  {card_id} [{status}] body:{lineno}  tempo acceptance names no field\n"
                    f"      {line.strip()[:110]}\n" + FIX)
    return failures, checked, notes


# --------------------------------------------------------------------------- #
# selftest: the incident's own wording must FAIL; the canonical bullet must PASS
# --------------------------------------------------------------------------- #

RETIRED_BULLET = """\
## Acceptance

The task is done when a real audio file exists on disk, produced by a real run, and:
1. measured tempo is within a few BPM of 92 (do not trust the plan — measure the audio),
2. the file has no percussion kit and no bass weight (a listener check).
"""

CANONICAL_BULLET = """\
## Acceptance

1. tempo: `/usr/bin/python3 music/rubrics/measure.py <artifact> --anchor-bpm 92` ->
   `ac_at_anchor.verdict == "supported"` (a candidate within 3 BPM of the anchor at
   ac >= 0.25, or the anchor's own lag ac >= 0.25 within ±10 % of its period). Do not
   accept or reject on the bare `bpm` field. If `bpm_pulse == "none"` and the verdict is
   `not_supported`, the tool cannot see a pulse: decide the tempo by the stem or ear
   check and say so in the card — never a silent FAIL, never a pass.
"""

RETIRED_QUOTED = """\
Every queue card so far was accepted on this bullet:

> measured tempo is within a few BPM of 92 (do not trust the plan — measure the audio)

That bullet names no field, and the tool could not satisfy it.
"""

RETIRED_STRUCK = """\
**Correction to this card's acceptance text** (its wording is what a future card would copy):

> ~~1. measured tempo is within a few BPM of 92 (do not trust the plan — measure the audio)~~

**Use instead:** the bullet below.
"""

BARE_TEMPO_LABEL = """\
## Acceptance

tempo: the master must measure 92 BPM.
"""

PLAN_SIDE_ACCEPTANCE = """\
**Acceptance for this genre: the plan's `bpm` field must read 150, never 100, 120 or 156.**
"""

JUNGLE_AB_PLAN = """\
  The test that settles (a) vs (b) is one controlled A/B on the GPU rail:
  render the same caption twice, once with `style_weight = 0.9` (→ 168 BPM) and once with it
  absent (→ 120 BPM), and measure both with `measure.py`. If both come back near 76, the
  `bpm` input is cosmetic and the fix must be a caption-level tempo strategy.
"""

JUNGLE_TABLE = """\
| Section | Claim | Re-measured 2026-10-16 | Verdict |
|---|---|---|---|
| §6.3 | the smoke artifact: bpm 76.0 (conf 0.24) with a 152.0 octave | re-ran `music/rubrics/measure.py`: every figure identical | ok |
| §6.3 | `int(60 + 0.8 x 120)` = 156, four below the pocket floor | `check_brief_bpm_solutions.py` PASSes the 0.9 → 168 BPM claim | ok |
"""

SELFTEST_CASES = [
    ("retired wording (t_b8afb055 / t_909069f0) FAILS", RETIRED_BULLET, 1),
    ("the canonical bullet PASSES", CANONICAL_BULLET, 0),
    ("a QUOTED retired bullet is a citation, not a claim", RETIRED_QUOTED, 0),
    ("a STRUCK-OUT retired bullet is a record, not a claim", RETIRED_STRUCK, 0),
    ("a bare `tempo:` line that names no field FAILS", BARE_TEMPO_LABEL, 1),
    ("a plan-side acceptance is not an audio claim", PLAN_SIDE_ACCEPTANCE, 0),
    ("jungle-dnb's A/B prose is not a claim", JUNGLE_AB_PLAN, 0),
    ("jungle-dnb's re-measurement table is not a claim", JUNGLE_TABLE, 0),
]


def selftest() -> int:
    bad = 0
    for label, text, want in SELFTEST_CASES:
        got = len(unfielded_claims(text))
        ok = got == want
        print(f"{'PASS' if ok else 'FAIL'} selftest: {label} "
              f"(unfielded claims: {got}, expected {want})")
        if not ok:
            bad += 1
    if bad:
        print(f"FAIL check_tempo_acceptance_field --selftest: {bad} case(s) misbehaved")
        return 1
    print(f"PASS check_tempo_acceptance_field --selftest: {len(SELFTEST_CASES)} cases")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="FAIL a lane text whose tempo acceptance names no field.")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--briefs-only", action="store_true",
                    help="skip the live board (no board db needed)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    if not (repo / "music" / "briefs").is_dir():
        print(f"FATAL check_tempo_acceptance_field: {repo} carries no music/briefs")
        return 3

    db = None if args.briefs_only else Path(args.db)
    if db is not None and not db.exists():
        print(f"FATAL check_tempo_acceptance_field: cannot read the board db {db}")
        return 3

    failures, checked, notes = scan(repo, db)

    if failures:
        print(f"FAIL check_tempo_acceptance_field: {len(failures)} tempo acceptance(s) "
              f"name no field, of {len(checked)} text(s) checked")
        print("\n".join(failures))
        print("  cited: t_f5f703ea (this check), t_ed609eb0 (the rule); "
              "t_b8afb055 / t_909069f0 (the cards it was written for)")
        return 1

    print(f"PASS check_tempo_acceptance_field: {len(checked)} text(s) checked, "
          "every tempo acceptance names ac_at_anchor / bpm_candidates / bpm_pulse")
    for note in notes:
        print(f"  note {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
