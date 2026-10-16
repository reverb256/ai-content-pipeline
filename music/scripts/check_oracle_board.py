#!/usr/bin/env python3
"""music/scripts/check_oracle_board.py — live-board invariants for oracle cards.

INCIDENT 1 (2026-10-09, card t_bf0e5edd)
----------------------------------------
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

INCIDENT 2 (2026-10-16, card t_6599927d)
----------------------------------------
A re-emitted card carried `stage: brief` unconditionally, although the genre's
brief was already on disk — measured that day, ALL 14 genres had one, so the 13
cards of the 14:05 wave (`t_2c5b59f2` … `t_354d5d25`) each sent a music-producer
run back through the brief stage to rediscover a delivered artifact. The rule
that replaced it lives in music/stage_state.py; B3 below reads the LIVE board and
fails a card that sits behind its genre's resume point.

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
  B3  No open oracle card sits BEHIND its genre's resume stage — the stage
      music/stage_state.py resolves from the genre's artifacts on disk. A card
      at or behind a delivered stage spends a worker run re-doing delivered
      work (incident 2). The card's position is the LAST `stage:` match in the
      card, exactly as the driver reads it (card t_92a09bdc: the driver takes
      the last match, so the check must too).
  B4  That marker must name a stage DECLARED in music/stages.yaml. The driver
      logs "unknown stage" and skips such a card, so it stalls silently.
      Measured 2026-10-16: the live card t_92a09bdc resolves to `advance-stage`
      — prose in a run summary, not the advance step (check_stage_advance.py
      cites an earlier reading of that same window as `advance`).

Run:  /usr/bin/python3 music/scripts/check_oracle_board.py [--db PATH]
                                                          [--stages PATH]
      /usr/bin/python3 music/scripts/check_oracle_board.py --selftest
Exit: 0 = invariant holds, 1 = violated, 2 = could not run.
"""

import argparse
import importlib.util
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".hermes/kanban/boards/music/kanban.db"
REPO = Path(__file__).resolve().parents[2]
DEFAULT_STAGES = REPO / "music" / "stages.yaml"

# The driver's own regex (pipeline-driver.sh::stage_of takes the LAST match).
MARKER = re.compile(r"stage: ([a-z-]+)")


def _load_module(name: str, path: Path) -> Any:
    """Load a lane module by path — music/ is not a package (no __init__.py)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_oracle(repo: Path) -> Any:
    return _load_module("music_oracle", repo / "music" / "oracle.py")


def load_stage_state(repo: Path) -> Any:
    return _load_module("music_stage_state", repo / "music" / "stage_state.py")


def read_board(db: Path) -> list[tuple[str, str, str, float]]:
    """(id, title, status, created_at) for every task on the board. Read only."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return con.execute(
            "select id, title, status, coalesce(created_at, 0) from tasks").fetchall()
    finally:
        con.close()


def read_card_windows(db: Path) -> dict[str, str]:
    """task_id -> the text the driver greps for its stage marker.

    The driver takes the LAST `stage: [a-z-]+` match from the output of
    `hermes kanban show <card>`, whose sections run: body, latest run summary,
    comments, runs. This reader reproduces that order from the board db, so the
    check and the driver agree on where a card stands. Measured 2026-10-16 on
    the live board: this reader reproduced the CLI's token for 42/42 oracle
    cards (every alternative section order did as well, so no card on this board
    is ambiguous today).
    """
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        windows: dict[str, str] = {}
        for task_id, body in con.execute("select id, coalesce(body, '') from tasks"):
            comments = [r[0] or "" for r in con.execute(
                "select body from task_comments where task_id=? "
                "order by coalesce(created_at, 0), id", (task_id,))]
            runs = [r[0] or "" for r in con.execute(
                "select summary from task_runs where task_id=? order by id", (task_id,))]
            windows[str(task_id)] = "\n".join([body] + runs[-1:] + comments + runs)
        return windows
    finally:
        con.close()


def last_stage_marker(window: str) -> str | None:
    """The stage the driver would route the card to, or None when it has none."""
    hits = MARKER.findall(window or "")
    return hits[-1] if hits else None


def find_violations(oracle: Any, rows: list[tuple[str, str, str, float]],
                    windows: dict[str, str] | None = None,
                    resume: Any = None, order: list[str] | None = None,
                    default: str | None = None) -> list[str]:
    """Pure check over board rows. No board, no clock, no network.

    B1: >1 open card for one genre. B2: an open card the guard cannot parse.
    B3: an open card behind its genre's resume stage (needs `windows`, `resume`
    and `order`). B4: an open card whose marker names no declared stage.
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

    if windows is None or resume is None or order is None:
        return problems

    index = {stage: i for i, stage in enumerate(order)}
    for genre, cards in sorted(open_by_genre.items()):
        resume_at = resume(genre)
        if resume_at not in index:
            problems.append(
                f"B3 UNKNOWN: genre {genre!r} resumes at {resume_at!r}, which "
                f"music/stages.yaml does not declare — the rule and the stage map "
                f"have diverged, so this card cannot be judged.")
            continue
        for task_id, _title, status, _created in cards:
            stage = last_stage_marker(windows.get(task_id, "")) or default
            if stage not in index:
                problems.append(
                    f"B4 VIOLATED: open card {task_id} [{status}] for {genre!r} carries "
                    f"the stage marker {stage!r}, which music/stages.yaml does not "
                    f"declare — the driver logs 'unknown stage' and skips the card, so "
                    f"it stalls where it is. Declared: {', '.join(order)}.")
                continue
            if index[stage] < index[resume_at]:
                problems.append(
                    f"B3 VIOLATED: open card {task_id} [{status}] for {genre!r} sits at "
                    f"stage {stage!r}, BEHIND its genre's resume stage {resume_at!r} — "
                    f"the stage's artifact is already on disk, so dispatching it spends "
                    f"a worker run re-doing delivered work (card t_6599927d: 13 such "
                    f"brief-stage runs on 2026-10-16, and all 14 genres had a brief).")
    return problems


def selftest(oracle: Any) -> int:
    """Feed the checker known-good and known-bad boards. No live db is touched."""
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

    stage_state = load_stage_state(REPO)
    order = stage_state.load_stage_order()
    default = stage_state.default_stage()
    # Fixture genre "chill-lounge" has a brief on disk -> resume genre-select.
    resume = lambda genre: stage_state.resume_stage(REPO, genre)[0]  # noqa: E731

    def win(*markers: str) -> str:
        return "\n".join(markers)

    def windows_for(rows, override: dict | None = None) -> dict[str, str]:
        """Every card positioned at its resume stage unless `override` says otherwise."""
        override = override or {}
        return {tid: override.get(tid, win("stage: genre-select")) for tid, *_ in rows}

    # The shape the 14:05 wave carried: a fresh body marker, `stage: brief`, for a
    # genre whose brief is already delivered.
    behind = [("t_h", "music-oracle: chill-lounge (score 8.6)", "ready", 8.0)]
    behind_windows = windows_for(behind, {"t_h": win("stage: brief")})
    # A card already advanced to the resume point (and beyond) is fine.
    on_point = [("t_i", "music-oracle: chill-lounge (score 8.6)", "ready", 9.0)]
    on_point_windows = windows_for(on_point)
    # The driver reads the LAST match: prose after the real marker must not pass.
    marker_lost = [("t_j", "music-oracle: chill-lounge (score 8.6)", "ready", 10.0)]
    marker_lost_windows = windows_for(marker_lost,
                                      {"t_j": win("stage: genre-select\n\nstage: brief")})
    # A marker naming no declared stage stalls the card. 'advance-stage' is the
    # token measured on the live card t_92a09bdc (run-summary prose).
    unknown = [("t_k", "music-oracle: chill-lounge (score 8.6)", "ready", 11.0)]
    unknown_windows = windows_for(unknown, {"t_k": win("stage: advance-stage")})

    got_clean = find_violations(oracle, clean, windows_for(clean), resume, order, default)
    got_dup = find_violations(oracle, duplicate, windows_for(duplicate),
                              resume, order, default)
    got_unparseable = find_violations(oracle, unparseable, windows_for(unparseable),
                                      resume, order, default)
    got_behind = find_violations(oracle, behind, behind_windows, resume, order, default)
    got_on_point = find_violations(oracle, on_point, on_point_windows, resume, order, default)
    got_marker_lost = find_violations(oracle, marker_lost, marker_lost_windows,
                                      resume, order, default)
    got_unknown = find_violations(oracle, unknown, unknown_windows, resume, order, default)

    checks = [
        ("clean board (one open card per genre, advanced past its resume stage)",
         len(got_clean), 0),
        ("re-created duplicate (2nd open chill-lounge card)", len(got_dup), 1),
        ("open card whose title names no genre", len(got_unparseable), 1),
        ("body marker `stage: brief` for a genre whose brief is on disk", len(got_behind), 1),
        ("card already at its resume stage (genre-select)", len(got_on_point), 0),
        ("marker pushed behind by later prose (driver takes the LAST match)",
         len(got_marker_lost), 1),
        ("marker naming an undeclared stage", len(got_unknown), 1),
    ]
    ok = all(got == want for _, got, want in checks)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_oracle_board:")
    for label, got, want in checks:
        print(f"  {'ok  ' if got == want else 'BAD '} {label}: {got} (want {want})")
        if got == want and want == 0 and got:
            print("      (a zero expected, non-zero found)")
    for label, found in (("B1", got_dup), ("B2", got_unparseable), ("B3", got_behind),
                         ("B4", got_unknown)):
        if found:
            print(f"  {label} message: {found[0]}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Live-board invariants for music board oracle cards.")
    ap.add_argument("--db", default=str(DEFAULT_DB),
                    help="kanban board db (default: the music board)")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--stages", default=None,
                    help="stage map (default: <repo>/music/stages.yaml)")
    ap.add_argument("--selftest", action="store_true",
                    help="prove B1-B4 fire on known-bad boards and stay silent clean")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    stages = Path(args.stages) if args.stages else repo / "music" / "stages.yaml"

    try:
        oracle = load_oracle(repo)

        if args.selftest:
            return selftest(oracle)

        stage_state = load_stage_state(repo)
        order = stage_state.load_stage_order(stages)
        default = stage_state.default_stage(stages)
        resume = lambda genre: stage_state.resume_stage(  # noqa: E731
            repo, genre, stages_yaml=stages)[0]

        db = Path(args.db).expanduser()
        if not db.exists():
            print(f"FATAL check_oracle_board: no board db at {db}", file=sys.stderr)
            return 2

        rows = read_board(db)
        windows = read_card_windows(db)
        problems = find_violations(oracle, rows, windows, resume, order, default)
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
    print(f"stage map : {stages}")
    print(f"open cards: {len(open_cards)} across "
          f"{len({g for _, g, _ in open_cards})} genre(s)")
    for tid, genre, status in sorted(open_cards, key=lambda c: (str(c[1]), c[0])):
        stage = last_stage_marker(windows.get(tid, "")) or default
        print(f"  {genre:22} {tid}  [{status}]  at {stage:16} resume {resume(genre)}")

    if problems:
        for p in problems:
            print(f"  - {p}")
        print(f"FAIL check_oracle_board: {len(problems)} violation(s) "
              f"(incidents t_bf0e5edd, t_6599927d)")
        return 1

    print(f"PASS check_oracle_board: every one of the "
          f"{len({g for _, g, _ in open_cards})} open oracle genre(s) carries exactly "
          f"one open card, positioned at or past its resume stage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
