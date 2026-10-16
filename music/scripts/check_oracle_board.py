#!/usr/bin/env python3
"""music/scripts/check_oracle_board.py — a genre must never carry two OPEN oracle cards.

INCIDENT (2026-10-09, card t_bf0e5edd)
--------------------------------------
music/oracle.py created a card for every genre above the score threshold, with
no read of the board. Two runs ten minutes apart produced 28 cards for 14
genres — every genre exactly twice (performance/music-oracle-runs.log):

    2026-10-09T03:27:53 — oracle run: 14 scored, 14 created, top=chill-lounge(8.9)
    2026-10-09T03:37:53 — oracle run: 14 scored, 14 created, top=chill-lounge(9.1)

Each duplicate put a whole second stage chain in flight: on 2026-10-16 six
music-producer workers ran at once, one per duplicate card, and three raced on
genre briefs that already existed on disk.

The emit-side fix is open_oracle_genres() in music/oracle.py (commit ade6e87),
covered by music/test_oracle_dedupe.py. That suite proves the GUARD works; it
cannot see the BOARD. This check is the other half: it reads the live board and
fails when the guard was bypassed — a run made before the guard landed, a manual
`hermes kanban create`, a card re-created by hand, a rolled-back deploy.

WHY SQLITE AND NOT THE CLI: open_oracle_genres() shells out to
`hermes kanban list --json`. Inside a dispatcher-spawned worker session the
kanban CLI refuses ALL calls ("delegate_task child contexts cannot mutate
Kanban tasks or boards", measured 2026-10-16), so a check built on the CLI
cannot run where the checks are run. The board db is read directly, READ ONLY.

Invariants
----------
  B1  No genre carries two or more OPEN oracle cards.
      FAIL lists each genre, every card id, its status and its created date.
  B2  Every open oracle card's title parses with the guard's own parser
      (oracle.genre_from_title). A card the guard cannot name is a card it
      cannot dedupe, so B2 is the guard's precondition, not a style rule.

Run:  /usr/bin/python3 music/scripts/check_oracle_board.py [--db PATH]
      /usr/bin/python3 music/scripts/check_oracle_board.py --selftest
Exit: 0 = invariant holds, 1 = violated, 2 = could not run.
"""

import argparse
import importlib.util
import sqlite3
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".hermes/kanban/boards/music/kanban.db"
REPO = Path(__file__).resolve().parents[2]


def load_oracle(repo: Path) -> Any:
    """Load music/oracle.py by path — music/ is not a package (no __init__.py)."""
    path = repo / "music" / "oracle.py"
    spec = importlib.util.spec_from_file_location("music_oracle", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_board(db: Path) -> list[tuple[str, str, str, float]]:
    """(id, title, status, created_at) for every task on the board. Read only."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return con.execute(
            "select id, title, status, coalesce(created_at, 0) from tasks").fetchall()
    finally:
        con.close()


def find_violations(oracle: Any, rows: list[tuple[str, str, str, float]]) -> list[str]:
    """Pure check over board rows. No board, no clock, no network.

    B1: >1 open card for one genre. B2: an open card the guard cannot parse.
    """
    problems: list[str] = []
    open_by_genre: dict[str, list[tuple[str, str, str, float]]] = {}

    for task_id, title, status, created in rows:
        if status not in oracle.OPEN_STATUSES:
            continue
        if not str(title).startswith(oracle.CARD_TITLE_PREFIX):
            continue
        genre = oracle.genre_from_title(title)
        if genre is None:
            problems.append(
                f"B2 VIOLATED: card {task_id} is open (status={status}) and titled "
                f"{title!r}, which {oracle.CARD_TITLE_PREFIX!r} cannot parse into a "
                f"genre — the dedupe guard cannot name what it cannot dedupe.")
            continue
        open_by_genre.setdefault(genre, []).append((task_id, title, status, created))

    for genre, cards in sorted(open_by_genre.items()):
        if len(cards) < 2:
            continue
        cards.sort(key=lambda c: c[3])
        detail = "; ".join(
            f"{tid} [{status}] {title!r} (created {int(created)})"
            for tid, title, status, created in cards)
        problems.append(
            f"B1 VIOLATED: genre {genre!r} carries {len(cards)} OPEN oracle cards — "
            f"a genre must carry at most 1 (one card owns the genre's stage chain; "
            f"each extra card dispatches a second chain). Cards: {detail}")

    return problems


def selftest(oracle: Any) -> int:
    """Feed the checker known-good and known-bad boards. No db is touched."""
    clean = [
        ("t_a", "music-oracle: chill-lounge (score 8.9)", "running", 1.0),
        ("t_b", "music-oracle: chill-lounge (score 9.1)", "done", 2.0),
        ("t_c", "music-oracle: chill-lounge (score 8.4)", "archived", 3.0),
        ("t_d", "music-oracle: trance (score 8.0)", "ready", 4.0),
        ("t_e", "music: Virtual Reflections - export", "ready", 5.0),
    ]
    duplicate = clean + [
        ("t_f", "music-oracle: chill-lounge (score 8.6)", "blocked", 6.0),
    ]
    unparseable = clean + [
        ("t_g", f"{oracle.CARD_TITLE_PREFIX}", "ready", 7.0),
    ]

    got_clean = find_violations(oracle, clean)
    got_dup = find_violations(oracle, duplicate)
    got_unparseable = find_violations(oracle, unparseable)

    checks = [
        ("clean board (one open card per genre, plus done + archived twins)",
         len(got_clean), 0),
        ("re-created duplicate (2nd open chill-lounge card)", len(got_dup), 1),
        ("open card whose title names no genre", len(got_unparseable), 1),
    ]
    ok = all(got == want for _, got, want in checks)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_oracle_board:")
    for label, got, want in checks:
        print(f"  {'ok  ' if got == want else 'BAD '} {label}: {got} violation(s) (want {want})")
    if got_dup:
        print(f"  B1 message: {got_dup[0]}")
    if got_unparseable:
        print(f"  B2 message: {got_unparseable[0]}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="A genre must never carry two open oracle cards.")
    ap.add_argument("--db", default=str(DEFAULT_DB),
                    help="kanban board db (default: the music board)")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--selftest", action="store_true",
                    help="prove B1 fires on a re-created duplicate and stays silent clean")
    args = ap.parse_args(argv)

    try:
        oracle = load_oracle(Path(args.repo).resolve())

        if args.selftest:
            return selftest(oracle)

        db = Path(args.db).expanduser()
        if not db.exists():
            print(f"FATAL check_oracle_board: no board db at {db}", file=sys.stderr)
            return 2

        rows = read_board(db)
        problems = find_violations(oracle, rows)
        open_cards = [
            (r[0], oracle.genre_from_title(r[1]), r[2])
            for r in rows
            if r[2] in oracle.OPEN_STATUSES
            and str(r[1]).startswith(oracle.CARD_TITLE_PREFIX)
        ]
    except Exception as exc:  # noqa: BLE001 — a broken check is not a pass
        print(f"FATAL check_oracle_board: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"board db  : {db}")
    print(f"open cards: {len(open_cards)} across "
          f"{len({g for _, g, _ in open_cards})} genre(s)")
    for tid, genre, status in sorted(open_cards, key=lambda c: (str(c[1]), c[0])):
        print(f"  {genre:22} {tid}  [{status}]")

    if problems:
        for p in problems:
            print(f"  - {p}")
        print(f"FAIL check_oracle_board: {len(problems)} violation(s) "
              f"(incident t_bf0e5edd: 28 cards for 14 genres)")
        return 1

    print(f"PASS check_oracle_board: every one of the "
          f"{len({g for _, g, _ in open_cards})} open oracle genre(s) carries exactly "
          f"one open card; every open title parses into a genre")
    return 0


if __name__ == "__main__":
    sys.exit(main())
