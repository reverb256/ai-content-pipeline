#!/usr/bin/env python3
"""check_stage_advance — every producing stage's advance step must be reachable
from the process that actually runs it.

WHY THIS EXISTS (incident 2026-10-16, card t_5a93164a)
------------------------------------------------------
`music/stages.yaml` ended every producing prompt with exactly one advance step:

    bash scripts/automation/advance-stage.sh {card} <next-stage> --board music

That step is refused for a dispatcher-spawned kanban worker. Measured from such
a worker's terminal:

    $ env | grep HERMES_DELEGATED
    HERMES_DELEGATED_CHILD_CONTEXT=/home/j_kro/.hermes      # fence active
    $ bash scripts/automation/advance-stage.sh t_92a09bdc genre-select --board music
    kanban: delegate_task child contexts cannot mutate Kanban tasks via the CLI
    $ echo $?
    1

Cause: a worker's terminal and every subprocess it starts are fenced
(`agent/delegation_context.py::kanban_path_is_fenced`, checked by
`hermes_cli/kanban.py::_is_delegated_child_cli_mutation` and by the durable
trust boundary in `kanban_db`). The SANCTIONED channel is the tool surface —
`tools/kanban_tools.py::_require_orchestrator_tool` states it: dispatcher-
spawned workers "must use kanban_complete, kanban_request_review,
kanban_request_changes, kanban_block, kanban_heartbeat, or kanban_comment for
their assigned task". So the marker must be posted with the `kanban_comment`
TOOL, and the CLI step is a fallback for the callers the fence does not cover
(the pipeline driver's `hermes -p <bot> chat`, cron, a human shell).

Blast radius of the old shape, measured: the four `brief` cards before this one
(t_38e84953, t_2541fd9c, t_9f7d6889, t_6272da09) all ended `done` with no
advance event, and no card has ever traversed brief → genre-select → … →
track. A marker that never moves means the driver re-dispatches the same stage
forever — the exact failure the advance step was added to prevent.

Rules enforced (FAIL)
---------------------
1. A producing stage (a `prompt`, and not `human_gate: true`) must name the
   tool channel: its prompt contains `kanban_comment`. A prompt that advances
   only through `advance-stage.sh` is a silent no-op for a dispatcher-spawned
   worker.
2. It must name the marker it writes: `stage: <token>` with `<token>` a stage
   DECLARED in the same file. A marker naming an undeclared stage is logged and
   skipped by the driver, so the card stalls.
3. If it also gives the CLI fallback, both channels must agree — the `stage: X`
   marker and the `advance-stage.sh {card} Y --board` target must be the SAME
   stage — and the fallback must carry `--board` (t_38e84953: without it every
   music advance went to faceless-youtube).
4. A prompt that closes the card must use `kanban_complete`, not the CLI
   `hermes kanban … complete` (refused for the same workers).

Not enforced, printed: whether a `stage:` marker is the LAST marker the driver
sees. Prose in a card's run summary that reads "stage: <word>" can capture the
last-match window (measured on t_92a09bdc, whose marker resolves to the bogus
stage `advance`); that fix belongs to the driver, and is carded separately.

Run:   /usr/bin/python3 music/scripts/check_stage_advance.py [--stages PATH]
       /usr/bin/python3 music/scripts/check_stage_advance.py --selftest
       (the profile's bundled python3 has no PyYAML; the system one does, which is
       also the interpreter the driver's own config parse resolves to)
Exit:  0 when every producing stage advances through a reachable channel; 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_STAGES = Path("/home/j_kro/ai-content-pipeline/music/stages.yaml")
CITED = "t_5a93164a (advance refused for dispatcher-spawned workers)"
MARKER = re.compile(r"stage: ([a-z-]+)")
CLI_TARGET = re.compile(
    r"advance-stage\.sh \{card\} ([a-z-]+) --board ([a-z-]+)"
)
CLI_NO_WELLFORMED = re.compile(r"advance-stage\.sh")
CLI_CLOSE = re.compile(r"hermes kanban --board \S+ complete \{card\}")


def _load(path: Path) -> dict:
    try:
        import yaml
    except ImportError:  # pragma: no cover - the driver resolves the same way
        raise SystemExit(
            f"FAIL check_stage_advance: this interpreter has no PyYAML, so "
            f"{path} cannot be read. Re-run with /usr/bin/python3 (the interpreter "
            "the pipeline driver's own config parse resolves to):\n"
            f"    /usr/bin/python3 {Path(__file__).resolve()} --stages {path}"
        )
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def run(stages: dict) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    notes: list[str] = []

    entries = [e for e in (stages.get("stages") or []) if isinstance(e, dict)]
    declared = {str(e["stage"]) for e in entries if e.get("stage")}
    producing = [
        e for e in entries
        if e.get("prompt") and not bool(e.get("human_gate", False))
    ]

    for entry in producing:
        stage = str(entry.get("stage"))
        prompt = str(entry.get("prompt"))
        markers = MARKER.findall(prompt)
        cli = CLI_TARGET.findall(prompt)
        cli_close = bool(CLI_CLOSE.search(prompt))

        if not markers and not cli:
            # Terminal stage: it does not move the card, it ENDS the run. That is
            # only legitimate through the tool channel.
            if "kanban_complete" not in prompt:
                problems.append(
                    f"{stage}: neither advances (no `stage: <next>` marker) nor closes with the "
                    f"`kanban_complete` tool — a card that reaches this stage stalls here. "
                    f"Cite {CITED}."
                )
            continue

        # 1 — the tool channel must be named, not just the fenced CLI.
        if "kanban_comment" not in prompt:
            problems.append(
                f"{stage}: no `kanban_comment` advance — the only named channel is the "
                f"`hermes kanban` CLI, which a dispatcher-spawned worker cannot use "
                f"(refused, exit 1). Cite {CITED}."
            )

        # 2 — the marker must name a declared stage.
        if not markers:
            problems.append(
                f"{stage}: names a CLI advance but no `stage: <next>` marker, so a "
                f"tool-only caller has nothing to post."
            )
        else:
            for token in markers:
                if token not in declared:
                    problems.append(
                        f"{stage}: marker `stage: {token}` names an UNDECLARED stage — the "
                        f"driver logs 'unknown stage' and skips the card. Declared: "
                        f"{', '.join(sorted(declared))}."
                    )

        # 3 — the CLI fallback, when present, must agree with the marker and carry --board.
        if CLI_NO_WELLFORMED.search(prompt) and not cli:
            problems.append(
                f"{stage}: names `advance-stage.sh` without the well-formed "
                f"`advance-stage.sh {{card}} <stage> --board <slug>` form — the --board flag "
                f"is required (t_38e84953: without it the music advance went to "
                f"faceless-youtube)."
            )
        if cli and markers:
            cli_stage = cli[0][0]
            if cli_stage not in markers:
                problems.append(
                    f"{stage}: the two advance channels DISAGREE — marker(s) {markers} vs CLI "
                    f"target `{cli_stage}`. Whichever runs decides the next stage."
                )

        # 4 — closing the card needs the tool too.
        if cli_close and "kanban_complete" not in prompt:
            problems.append(
                f"{stage}: closes the card with the CLI (`hermes kanban … complete`), which is "
                f"refused for a dispatcher-spawned worker — use the `kanban_complete` tool. "
                f"Cite {CITED}."
            )

    gates = [e for e in entries if bool(e.get("human_gate", False))]
    notes.append(
        f"{len(producing)} producing stage(s) checked, "
        f"{len(gates)} human gate(s) exempt ({', '.join(str(g.get('stage')) for g in gates) or 'none'})"
    )
    notes.append(
        "not checked here: whether the marker is the LAST `stage:` match the driver sees — "
        "prose in a run summary can capture it (t_92a09bdc resolves to the bogus stage `advance`)"
    )
    return problems, notes


def _write(cfg: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="check-stage-advance."))
    path = tmp / "stages.yaml"
    path.write_text(cfg)
    return path


GOOD = """
version: 1
stages:
  - stage: brief
    bot: producer
    prompt: "Run the brief stage. Then advance the card to genre-select: post the marker
      \\"stage: genre-select\\" on {card} with the kanban_comment tool. Without a kanban tool,
      run bash scripts/automation/advance-stage.sh {card} genre-select --board music."
  - stage: genre-select
    bot: producer
    prompt: "Resolve the genre. Then advance the card to track: post the marker
      \\"stage: track\\" on {card} with the kanban_comment tool."
  - stage: track
    bot: analyst
    prompt: "Run the track stage. Then close the card with the kanban_complete tool."
  - stage: human-approval
    human_gate: true
    prompt: "Parked for j_kro."
"""

ONLY_CLI = """
version: 1
stages:
  - stage: brief
    bot: producer
    prompt: "Run the brief stage. Then advance the card: bash scripts/automation/advance-stage.sh
      {card} genre-select --board music."
"""

UNDECLARED = """
version: 1
stages:
  - stage: brief
    bot: producer
    prompt: "Then advance: post the marker \\"stage: nowhere\\" with the kanban_comment tool."
"""

NO_BOARD = """
version: 1
stages:
  - stage: brief
    bot: producer
    prompt: "Then advance: post the marker \\"stage: genre-select\\" with the kanban_comment tool,
      or run bash scripts/automation/advance-stage.sh {card} genre-select -music."
  - stage: genre-select
    bot: producer
    prompt: "Then advance: post the marker \\"stage: lyrics\\" with the kanban_comment tool."
"""

DISAGREE = """
version: 1
stages:
  - stage: brief
    bot: producer
    prompt: "Then advance: post the marker \\"stage: lyrics\\" with the kanban_comment tool, or run
      bash scripts/automation/advance-stage.sh {card} genre-select --board music."
  - stage: lyrics
    bot: writer
    prompt: "Then advance: post the marker \\"stage: generate\\" with the kanban_comment tool."
  - stage: generate
    bot: producer
    prompt: "Nothing to do here."
"""

CLI_CLOSE_ONLY = """
version: 1
stages:
  - stage: track
    bot: analyst
    prompt: "Then close the card: run hermes kanban --board music complete {card}."
"""

STALLS = """
version: 1
stages:
  - stage: brief
    bot: producer
    prompt: "Write the brief. Report it in the summary."
"""


def selftest() -> int:
    """Prove the check fires on each failure class it claims to catch."""
    cases = [
        ("clean map reports nothing", GOOD, None),
        ("CLI-only advance caught", ONLY_CLI, "no `kanban_comment` advance"),
        ("undeclared marker caught", UNDECLARED, "UNDECLARED stage"),
        ("missing --board caught", NO_BOARD, "without the well-formed"),
        ("channel disagreement caught", DISAGREE, "DISAGREE"),
        ("CLI-only close caught", CLI_CLOSE_ONLY, "kanban_complete"),
        ("advance dropped entirely caught", STALLS, "stalls here"),
    ]
    for label, cfg, expect in cases:
        path = _write(cfg)
        problems, _ = run(_load(path))
        if expect is None:
            if problems:
                print(f"SELFTEST FAIL ({label}): clean map reported {problems}")
                return 1
            continue
        if not any(expect in p for p in problems):
            print(f"SELFTEST FAIL ({label}): expected {expect!r} in {problems}")
            return 1
    print("PASS --selftest: clean map cleared; CLI-only advance, undeclared marker, "
          "missing --board, channel disagreement and CLI-only close all caught")
    return 0


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Check that stage advances are reachable.")
    ap.add_argument("--stages", default=str(DEFAULT_STAGES))
    ap.add_argument("--repo", default=str(here.parents[2]))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    stages_path = Path(args.stages)
    if not stages_path.is_file():
        print(f"FAIL check_stage_advance: no stage map at {stages_path}")
        return 1

    problems, notes = run(_load(stages_path))
    for note in notes:
        print(f"note    {note}")
    if problems:
        print(f"FAIL check_stage_advance: {len(problems)} unreachable advance step(s) in "
              f"{stages_path}")
        for p in problems:
            print(f"  {p}")
        print(f"  cited: {CITED}")
        return 1
    print(f"PASS check_stage_advance: every producing stage in {stages_path} advances through "
          f"a channel a dispatcher-spawned worker can reach")
    return 0


if __name__ == "__main__":
    sys.exit(main())
