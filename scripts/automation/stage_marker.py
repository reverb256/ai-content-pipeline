#!/usr/bin/env python3
"""stage_marker.py — THE stage-marker convention for a kanban card.

Board-agnostic on purpose: `scripts/automation/pipeline-driver.sh` walks any
board, so the convention lives here, outside the music lane, and both the driver
and every check call THIS file rather than re-implementing the rule.

WHY (incident 2026-10-16, card t_669bb02b; filed from card t_5a93164a)
---------------------------------------------------------------------
`pipeline-driver.sh::stage_of` read the marker as *the last `stage: <word>`
anywhere* in the rendered output of `hermes kanban show`:

    s=$(hermes kanban show "$1" | grep -oE "stage: [a-z-]+" | tail -1 | awk '{print $2}')

`hermes kanban show` prints, in this order (measured 2026-10-16 against
`hermes_cli/kanban.py::_cmd_show`): the card BODY, then `Result:`/`Latest
summary:`, then `Comments`, then `Events` (whose `completed` payload carries the
FULL run summary), then `Runs` (the run summary's first line). The run summary is
rendered AFTER the comments, so the writer's rule "the marker must be the last
board write" does NOT protect the read: prose in a run summary wins.

Measured on the live music board:

    $ hermes kanban --board music show t_92a09bdc | grep -nE "stage: [a-z-]+"
    36:stage: brief
    40:Ran the brief stage ... Did not advance the stage: advance-stage.sh is
       refused for dispatcher-spawned workers (exit 1) ...
    $ hermes kanban --board music show t_92a09bdc | grep -oE "stage: [a-z-]+" | tail -1
    stage: advance-stage

`advance-stage` is not a declared stage, so the driver logs "unknown stage" and
SKIPS the card: a silent stall instead of a route. The same hazard with a
declared token would route the card to the WRONG stage.

THE CONVENTION (one convention for every writer and every reader)
----------------------------------------------------------------
A card's stage marker is a LINE whose entire content is

    stage: <token>

nothing before it on the line and nothing after it. Markers are read from, in
write order:

  1. the card BODY — its lines, in order, then
  2. each COMMENT body — comments in the order the kanban CLI returns them
     (`kanban_db.list_comments`: `created_at ASC`, so oldest first), lines in
     order.

Run summaries, task results and events are NEVER a marker source. That is the
whole fix: a summary cannot capture a read that does not look at summaries.

Both writers already emit this shape:
  * `music/oracle.py` — a `stage: <resume>` line at the END of the card body.
  * the stage advance step — the comment body IS `stage: <next>` (the
    `kanban_comment` TOOL first; `scripts/automation/advance-stage.sh` is the
    CLI fallback for callers the worker fence does not cover).

A marker-shaped line inside the body or a comment IS a marker: the card's own
text is the card's own statement. Prose that happens to contain "stage: <word>"
mid-line is not a marker, and a summary is not read at all.

`declared` (optional) filters candidates to the stages a stage map declares.
`resolve()` returns both tokens:
  * `raw`      — the last candidate, whatever its token (this is the driver's
                 route; an undeclared token is still logged and skipped, the
                 driver contract from music/stages.yaml)
  * `resolved` — the last candidate whose token IS declared (what the card
                 routes to once the hygiene problem is fixed); equal to `raw`
                 when `declared` is None or the raw token is declared.

Consumers (do not re-implement):
  * `scripts/automation/pipeline-driver.sh::stage_of`  -> `raw` (the route)
  * `music/scripts/check_stage_markers.py`             -> both, + the legacy read

Usage:
  /usr/bin/python3 scripts/automation/stage_marker.py <card> [--board <slug>]
                                                  [--declared a,b,c] [--raw]
Exit: 0 = the card was read (a token may be empty: the card carries no marker);
      2 = the card could not be read — the caller must NOT guess a stage.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

# The token class stays [a-z-]+: every stage in every stage map is lowercase,
# and stage names may contain hyphens (music lane: genre-select, human-approval).
MARKER = re.compile(r"^stage: ([a-z-]+)\s*$", re.M)


class StageMarkerError(RuntimeError):
    """The card could not be read. Never guess a stage after this."""


def tokens(text: str | None) -> list[str]:
    """Every marker token in `text`, in line order."""
    return MARKER.findall(text or "")


def resolve(body: str | None, comments, declared=None) -> tuple[str | None, str | None]:
    """(raw, resolved) for a card, per the convention.

    `comments` is an iterable of comment bodies in write order (oldest first).
    """
    candidates = tokens(body)
    for comment in comments or ():
        candidates += tokens(comment)
    raw = candidates[-1] if candidates else None
    if declared is None:
        return raw, raw
    declared_set = set(declared)
    resolved = next((t for t in reversed(candidates) if t in declared_set), None)
    return raw, resolved


def from_payload(payload: dict, declared=None) -> tuple[str | None, str | None]:
    """`resolve()` over a decoded `hermes kanban show <card> --json` payload."""
    task = payload.get("task") or {}
    comments = [(c or {}).get("body") or "" for c in payload.get("comments") or []]
    return resolve(task.get("body") or "", comments, declared)


def read_show(board: str, card: str, *, timeout: int = 90) -> dict:
    """`hermes kanban --board <board> show <card> --json` -> decoded payload."""
    try:
        proc = subprocess.run(
            ["hermes", "kanban", "--board", board, "show", card, "--json"],
            capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        raise StageMarkerError(f"cannot run the kanban CLI: {exc}") from exc
    if proc.returncode != 0:
        raise StageMarkerError(
            f"`hermes kanban --board {board} show {card} --json` rc="
            f"{proc.returncode}: {proc.stderr.strip()[:200]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise StageMarkerError(f"the kanban CLI returned no JSON: {exc}") from exc


def marker_of(board: str, card: str, declared=None, *, raw_only: bool = False):
    """Convenience: read the card over the CLI and resolve its marker."""
    payload = read_show(board, card)
    raw, resolved = from_payload(payload, declared)
    return (raw if raw_only else resolved), raw


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Resolve a kanban card's stage marker (the one convention).")
    ap.add_argument("card")
    ap.add_argument("--board", default="faceless-youtube",
                    help="kanban board slug (default: the driver's default)")
    ap.add_argument("--declared", default=None,
                    help="comma-separated declared stages; the resolved token "
                         "is filtered to these")
    ap.add_argument("--raw", action="store_true",
                    help="print the raw last marker instead of the resolved one")
    args = ap.parse_args(argv)

    declared = [s.strip() for s in args.declared.split(",") if s.strip()] \
        if args.declared else None
    try:
        payload = read_show(args.board, args.card)
    except StageMarkerError as exc:
        print(f"stage_marker: {exc}", file=sys.stderr)
        return 2
    raw, resolved = from_payload(payload, declared)
    token = raw if args.raw else resolved
    if token:
        print(token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
