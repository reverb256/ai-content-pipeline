#!/usr/bin/env python3
"""check_stage_markers — the cards the pipeline driver WOULD DISPATCH must carry
a marker the driver can route, and it must be the marker the one convention
resolves (scripts/automation/stage_marker.py).

WHY THIS EXISTS (incident 2026-10-16, card t_669bb02b, filed from t_5a93164a)
---------------------------------------------------------------------------
`pipeline-driver.sh::stage_of` used to read the stage marker as *the last
`stage: <word>` anywhere* in the rendered `hermes kanban show` output:

    s=$(hermes kanban show "$1" | grep -oE "stage: [a-z-]+" | tail -1 | awk '{print $2}')

The rendering order (measured against `hermes_cli/kanban.py::_cmd_show`) is
body, Result/latest summary, Comments, Events (payload = the FULL run summary),
Runs. The summary therefore lands AFTER the comments, and prose in it wins:

    $ hermes kanban --board music show t_92a09bdc | grep -oE "stage: [a-z-]+" | tail -1
    stage: advance-stage        <- from the summary's "Did not advance the stage:
                                   advance-stage.sh is refused ..."
    $ # 'advance-stage' is not a declared stage
    $ # -> the driver logs "unknown stage" and SKIPS the card: a silent stall

The fix (same card) moved the read onto the convention in
`scripts/automation/stage_marker.py`: a marker is a LINE that IS
`stage: <token>` — in the card BODY or in a COMMENT body — and run summaries are
not a marker source at all. The driver and this check call that one file, so a
divergence between "what the writer writes" and "what the readers route on" is
now measurable instead of latent.

Rules enforced (FAIL)
---------------------
M1  A card in the driver's dispatch set carries a marker that music/stages.yaml
    does not declare. The driver logs "unknown stage" and skips the card, so it
    stalls silently instead of being routed.
M2  A card in the driver's dispatch set resolves to a different token under the
    LEGACY positional read than under the convention. Prose then decides the
    route for any reader that still greps the rendered text — the hazard
    t_669bb02b was filed for.
    (Both rules mark the card FAIL so the card's own text is fixed; a summary
    must not contain a bare `stage: <word>` line, and the marker must be real.)

Not enforced, printed (notes)
-----------------------------
N1  Cards in the dispatch set with NO marker at all. The driver routes them to
    the board default (`default_stage` — `brief` on music), which is why every
    tick logs 30+ `card -> stage brief` lines.
N2  `running` cards, with their markers: a card that comes back to `ready` with
    a bad marker is visible before the next tick dispatches it.

Run:  /usr/bin/python3 music/scripts/check_stage_markers.py [--db PATH]
                                        [--repo PATH] [--stages PATH]
                                        [--verify-cli] [--selftest]
      --verify-cli cross-checks the board-db read against `hermes kanban show
      --json` for every card in scope (slow: one CLI call per card).
Exit: 0 = every dispatchable card routes; 1 = violation(s); 2 = could not run.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".hermes/kanban/boards/music/kanban.db"
REPO = Path(__file__).resolve().parents[2]
DEFAULT_STAGES = REPO / "music" / "stages.yaml"

# The status the driver dispatches: `get_ready_cards()` greps `^▶` from
# `hermes kanban list`, and hermes_cli/kanban_output.py maps `ready` -> `▶`.
DISPATCH_STATUS = "ready"
# The legacy (pre-fix) read, kept here ONLY to measure what a positional reader
# would decide — never to decide anything.
LEGACY = re.compile(r"stage: ([a-z-]+)")
CITED = ("t_669bb02b (positional marker / prose capture) · t_5a93164a (advance "
         "channel) · t_92a09bdc (live card the legacy read mis-resolved to "
         "`advance-stage`)")


def load_stage_marker(repo: Path) -> Any:
    """The ONE convention, loaded by path (scripts/ is not a package)."""
    path = repo / "scripts" / "automation" / "stage_marker.py"
    spec = importlib.util.spec_from_file_location("stage_marker", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the stage-marker convention at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def declared_stages(stages: Path) -> list[str]:
    import yaml
    cfg = yaml.safe_load(stages.read_text()) or {}
    return [str(e["stage"]) for e in cfg.get("stages") or [] if isinstance(e, dict)]


def default_stage(stages: Path) -> str:
    import yaml
    cfg = yaml.safe_load(stages.read_text()) or {}
    return str(cfg.get("default_stage", "opportunity"))


def read_cards(db: Path) -> list[dict]:
    """Every card as {id,title,status,body,comments,window}. Read only.

    `window` reproduces what the LEGACY reader saw in `hermes kanban show`:
    body, then the latest summary/result, then the comments, then the run
    summaries (the CLI prints the summary again inside Events and Runs, after
    the comments — that is exactly how prose captured t_92a09bdc).
    """
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        cards = []
        for row in con.execute(
                "select id, title, status, coalesce(body,'') as body, "
                "coalesce(result,'') as result from tasks order by id"):
            tid = row["id"]
            comments = [r[0] or "" for r in con.execute(
                "select body from task_comments where task_id=? "
                "order by coalesce(created_at, 0), id", (tid,))]
            runs = [r[0] or "" for r in con.execute(
                "select coalesce(summary,'') as summary from task_runs "
                "where task_id=? order by id", (tid,))]
            window = "\n".join([row["body"], row["result"]] + comments + runs)
            cards.append(dict(id=tid, title=row["title"], status=row["status"],
                              body=row["body"], comments=comments, window=window))
        return cards
    finally:
        con.close()


def legacy_token(window: str) -> str | None:
    """What the pre-fix read decided for this card (measurement only)."""
    hits = LEGACY.findall(window or "")
    return hits[-1] if hits else None


def find_problems(cards: list[dict], declared: list[str], default: str,
                  stage_marker: Any) -> tuple[list[str], list[str], list[str]]:
    """Pure check over cards. Returns (problems, notes, dispatch_lines)."""
    problems: list[str] = []
    notes: list[str] = []
    dispatch_lines: list[str] = []
    declared_list = ", ".join(declared)

    in_scope = [c for c in cards if c["status"] == DISPATCH_STATUS]
    running = [c for c in cards if c["status"] == "running"]

    for card in in_scope:
        raw, resolved = stage_marker.resolve(card["body"], card["comments"], declared)
        legacy = legacy_token(card["window"])
        route = raw or default
        dispatch_lines.append(
            f"  {card['id']}  [{card['status']}]  marker={raw or '(none)'}"
            f" -> route {route}"
            + (f"  [resolved {resolved}]" if resolved and resolved != raw else "")
            + f"   legacy-read={legacy or '(none)'}   {card['title'][:52]}")

        if raw is not None and raw not in declared:
            problems.append(
                f"M1 VIOLATED: card {card['id']} carries the marker {raw!r}, which "
                f"{DEFAULT_STAGES.name} does not declare — the driver logs "
                f"'unknown stage' and SKIPS the card, so it stalls silently "
                f"instead of being routed. Declared: {declared_list}.")

        if legacy is not None and legacy != route:
            problems.append(
                f"M2 VIOLATED: card {card['id']} routes to {route!r} under the "
                f"convention but to {legacy!r} under the legacy positional read — "
                f"prose in the card (a run summary/result/event is rendered AFTER "
                f"the comments) captures every reader that greps the rendered "
                f"text. The route must not depend on which reader looks.")

    for card in running:
        raw, resolved = stage_marker.resolve(card["body"], card["comments"], declared)
        legacy = legacy_token(card["window"])
        notes.append(
            f"N2 running card {card['id']} marker={raw or '(none)'} legacy-read="
            f"{legacy or '(none)'}"
            + (f" resolved={resolved}" if resolved != raw else "")
            + f" — {card['title'][:52]}")

    no_marker = [c for c in in_scope
                 if stage_marker.resolve(c["body"], c["comments"], declared)[0] is None]
    notes.append(
        f"N1 {len(no_marker)} of {len(in_scope)} card(s) the driver would dispatch "
        f"carry NO marker and route to the board default {default!r} — the `card -> "
        f"stage {default}` noise in performance/pipeline-driver.log. Not a violation "
        f"of the convention (music/stages.yaml documents the default), but a card "
        f"that is not a stage chain should not enter the driver's walk.")
    for card in no_marker:
        notes.append(f"   no marker: {card['id']} [{card['status']}] "
                     f"{card['title'][:60]}")
    return problems, notes, dispatch_lines


def verify_cli(cards: list[dict], stage_marker: Any, declared: list[str],
               board: str) -> tuple[list[str], int]:
    """Cross-check the db read against `hermes kanban show --json`."""
    problems: list[str] = []
    checked = 0
    for card in cards:
        if card["status"] not in (DISPATCH_STATUS, "running"):
            continue
        try:
            payload = stage_marker.read_show(board, card["id"])
        except Exception as exc:  # noqa: BLE001 — a failed read is not a pass
            problems.append(f"CLI READ FAILED for {card['id']}: {exc}")
            continue
        cli_raw, cli_res = stage_marker.from_payload(payload, declared)
        db_raw, db_res = stage_marker.resolve(card["body"], card["comments"], declared)
        checked += 1
        if (cli_raw, cli_res) != (db_raw, db_res):
            problems.append(
                f"CLI/DB DISAGREE for {card['id']}: cli=({cli_raw!r},{cli_res!r}) "
                f"db=({db_raw!r},{db_res!r}) — the check does not judge the same "
                f"card the driver reads.")
        human = subprocess.run(["hermes", "kanban", "--board", board, "show",
                                card["id"]], capture_output=True, text=True)
        if human.returncode == 0:
            legacy_cli = legacy_token(human.stdout)
            if legacy_cli != legacy_token(card["window"]):
                problems.append(
                    f"LEGACY READER MISMATCH for {card['id']}: cli={legacy_cli!r} "
                    f"db={legacy_token(card['window'])!r} — the check must measure "
                    f"what the old read saw, or its M2 evidence is wrong.")
    return problems, checked


def selftest(stage_marker: Any) -> int:
    """Prove M1, M2 and the notes fire on known-bad boards."""
    declared = ["brief", "genre-select", "lyrics", "generate", "track"]
    default = "brief"

    def card(cid: str, status: str, body: str = "", comments=(), window=None):
        window = window if window is not None else "\n".join(
            [body] + list(comments))
        return dict(id=cid, title=f"card {cid}", status=status, body=body,
                    comments=list(comments), window=window)

    clean = [
        card("t_ok1", "ready", "brief text\n\nstage: genre-select\n"),
        card("t_ok2", "ready", "no marker here but a summary says stage: brief"),
        card("t_ok3", "done", "stage: track\n"),
        card("t_ok4", "ready", "report\n", ["done, moving on\nstage: lyrics\n"]),
        card("t_ok5", "running", "stage: brief\n"),
    ]
    unknown = [
        card("t_bad1", "ready", "body\n\nstage: nowhere\n", [],
             window="body\n\nstage: nowhere\n"),
    ]
    captured = [
        card("t_bad2", "ready", "body\n\nstage: genre-select\n",
             [],
             window=("body\n\nstage: genre-select\n\nRan the stage: genre-select "
                     "was left as it was and the helper did not advance the "
                     "stage: lyrics\n")),
    ]
    no_marker = [card("t_none", "ready", "a card with no marker at all\n")]

    cases = [
        ("clean board is silent", clean, 0, None),
        ("undeclared marker -> M1", unknown, 1, "M1 VIOLATED"),
        ("prose capture -> M2", captured, 1, "M2 VIOLATED"),
        ("no marker -> note, not a failure", no_marker, 0, None),
    ]
    ok = True
    for label, cards, want, needle in cases:
        problems, notes, _lines = find_problems(cards, declared, default, stage_marker)
        good = len(problems) == want and (needle is None or
                                          any(needle in p for p in problems))
        print(f"  {'ok  ' if good else 'BAD '} {label}: {len(problems)} "
              f"problem(s), want {want}")
        if not good:
            ok = False
            for p in problems:
                print(f"        {p}")
    # The no-marker note must name the default it routes to.
    _p, notes, _l = find_problems(no_marker, declared, default, stage_marker)
    if not any("'brief'" in n for n in notes):
        print("  BAD  the no-marker note must name the board default")
        ok = False
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_stage_markers")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Cards the pipeline driver would dispatch must carry a "
                    "routable stage marker.")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--stages", default=None)
    ap.add_argument("--board", default=None,
                    help="board slug for --verify-cli (default: the db's board dir)")
    ap.add_argument("--verify-cli", action="store_true",
                    help="cross-check the db read against `hermes kanban show --json`")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    stages = Path(args.stages) if args.stages else repo / "music" / "stages.yaml"
    db = Path(args.db).expanduser()
    board = args.board or db.parent.name

    try:
        stage_marker = load_stage_marker(repo)
        if args.selftest:
            return selftest(stage_marker)
        declared = declared_stages(stages)
        default = default_stage(stages)
        if not db.exists():
            print(f"FATAL check_stage_markers: no board db at {db}", file=sys.stderr)
            return 2
        cards = read_cards(db)
    except Exception as exc:  # noqa: BLE001 — a broken check is not a pass
        print(f"FATAL check_stage_markers: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2

    problems, notes, dispatch_lines = find_problems(cards, declared, default,
                                                    stage_marker)
    in_scope = [c for c in cards if c["status"] == DISPATCH_STATUS]

    print(f"board db  : {db}")
    print(f"stage map : {stages}  ({len(declared)} declared, default {default!r})")
    print(f"convention: {repo / 'scripts/automation/stage_marker.py'} "
          f"(sha256 {_sha(repo / 'scripts/automation/stage_marker.py')})")
    print(f"driver would dispatch {len(in_scope)} card(s) "
          f"(status {DISPATCH_STATUS}: `hermes kanban list` marks them `^▶`)")
    for line in dispatch_lines:
        print(line)

    if args.verify_cli:
        cli_problems, checked = verify_cli(cards, stage_marker, declared, board)
        print(f"--verify-cli: {checked} card(s) cross-checked against "
              f"`hermes kanban --board {board} show --json`")
        problems += cli_problems

    for note in notes:
        print(f"note    {note}")

    if problems:
        for p in problems:
            print(f"  - {p}")
        print(f"FAIL check_stage_markers: {len(problems)} violation(s) on the "
              f"cards the driver would dispatch")
        print(f"  cited: {CITED}")
        return 1

    print(f"PASS check_stage_markers: all {len(in_scope)} dispatchable card(s) "
          f"resolve to a declared stage under the convention "
          f"(scripts/automation/stage_marker.py)")
    return 0


def _sha(path: Path) -> str:
    import hashlib
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return "(missing)"


if __name__ == "__main__":
    sys.exit(main())
