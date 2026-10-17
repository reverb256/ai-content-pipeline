#!/usr/bin/env python3
"""music/test_stage_marker.py — the stage-marker convention (card t_669bb02b).

REGRESSION UNDER TEST
---------------------
`pipeline-driver.sh::stage_of` used to route a card on the LAST `stage: <word>`
anywhere in the rendered `hermes kanban show` output. The rendering order is
body, Result/latest summary, Comments, Events, Runs — so the run summary is
printed AFTER the comments and prose in it captures the read. Measured on the
live music board: card t_92a09bdc resolved to the undeclared stage
`advance-stage` (from "...Did not advance the stage: advance-stage.sh is
refused...") instead of the `stage: brief` its body declares.

The convention (`scripts/automation/stage_marker.py`) must therefore:

  1. read a marker ONLY from a line that IS `stage: <token>` — in the card body
     or in a comment body — and never from a run summary, a result or an event,
  2. keep the marker a comment carries even when the comment is a multi-line
     report (the legacy writers put the marker line inside the report),
  3. take the LAST marker in write order (body first, then comments oldest
     first), so an advance moves the card forward,
  4. not mistake prose for a marker ("...the stage: brief was left as it was"
     is not a marker),
  5. report both the raw token (the driver's route, undeclared tokens included —
     the driver logs "unknown stage" and skips) and the resolved token (the last
     DECLARED one), so the hygiene problem is measurable without changing the
     driver's contract.

Run:  /usr/bin/python3 music/test_stage_marker.py
Exit: 0 = all pass, 1 = failure.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "stage_marker", REPO / "scripts" / "automation" / "stage_marker.py")
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError("cannot load scripts/automation/stage_marker.py")
stage_marker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stage_marker)

DECLARED = ["brief", "genre-select", "lyrics", "generate", "curate", "stems",
            "master", "gate", "package", "visual", "publish", "track",
            "human-approval", "escalate"]

# The card t_92a09bdc window, verbatim in shape: the body declares `stage: brief`;
# the run summary (rendered again inside Events and Runs, after the comments)
# says "...the stage: advance-stage.sh...". The convention must return `brief`.
INCIDENT_92A09BDC: dict = dict(
    task=dict(id="t_92a09bdc", body="# Music Oracle Card — elemental-air\n\n"
                                "**Resume at `brief`.** ...\n\nstage: brief\n"),
    comments=[dict(author="music-producer",
                   body="# brief stage complete — elemental-air\n\n"
                        "**Deliverable:** music/briefs/elemental-air/"
                        "above-the-weather/brief.md\n")],
    latest_summary=("Ran the brief stage for the elemental-air oracle card. ... "
                    "Did not advance the stage: advance-stage.sh is refused for "
                    "dispatcher-spawned workers (exit 1), and no audio was "
                    "generated (brief stage only)."),
    runs=[dict(summary=("Ran the brief stage ... Did not advance the stage: "
                        "advance-stage.sh is refused ..."))],
)

# The advance form the post-t_5a93164a workers use: the marker is the FIRST line
# of the comment and the worker appends the reason under it (t_006db63d).
ADVANCE_COMMENT_FIRST: dict = dict(
    task=dict(body="card body\n\nstage: brief\n"),
    comments=[dict(author="music-producer",
                   body="stage: genre-select\n\n(Posted as a comment because "
                        "advance-stage.sh is refused from a worker.)")],
)

# The legacy advance form: the marker is the LAST line of a multi-line report.
ADVANCE_COMMENT_LAST: dict = dict(
    task=dict(body="card body\n\nstage: brief\n"),
    comments=[dict(author="music-producer",
                   body="## brief stage — trance — DONE\n\nArtifact: ...\n\n"
                        "stage: lyrics\n")],
)


class TestConvention(unittest.TestCase):
    def test_body_marker_is_read(self):
        raw, res = stage_marker.resolve("text\n\nstage: genre-select\n", [])
        self.assertEqual((raw, res), ("genre-select", "genre-select"))

    def test_hyphenated_stage_names(self):
        self.assertEqual(stage_marker.tokens("stage: human-approval\n"),
                         ["human-approval"])

    def test_mid_line_prose_is_not_a_marker(self):
        self.assertEqual(stage_marker.tokens(
            "Did not advance the stage: advance-stage.sh is refused\n"), [])
        self.assertEqual(stage_marker.tokens(
            "The YAML itself is valid (14 stages, `default_stage: brief`)\n"), [])

    def test_indented_marker_is_not_a_marker(self):
        self.assertEqual(stage_marker.tokens("    stage: brief\n"), [])

    def test_later_comment_wins(self):
        raw, _res = stage_marker.resolve("stage: brief\n",
                                         ["stage: genre-select\n",
                                          "stage: lyrics\n"])
        self.assertEqual(raw, "lyrics")

    def test_legacy_report_ending_carries_the_marker(self):
        raw, _res = stage_marker.from_payload(
            ADVANCE_COMMENT_LAST, DECLARED)
        self.assertEqual(raw, "lyrics")

    def test_advance_comment_with_trailing_prose_is_read(self):
        raw, _res = stage_marker.from_payload(ADVANCE_COMMENT_FIRST, DECLARED)
        self.assertEqual(raw, "genre-select")

    def test_run_summary_never_captures_the_marker(self):
        """t_92a09bdc: the summary says `stage: advance-stage.sh`, the card is at brief."""
        raw, res = stage_marker.from_payload(INCIDENT_92A09BDC, DECLARED)
        self.assertEqual(raw, "brief")
        self.assertEqual(res, "brief")
        # The legacy read, over the same card, is what mis-routed it.
        window = "\n".join([INCIDENT_92A09BDC["task"]["body"],
                            INCIDENT_92A09BDC["latest_summary"]]
                           + [c["body"] for c in INCIDENT_92A09BDC["comments"]]
                           + [r["summary"] for r in INCIDENT_92A09BDC["runs"]])
        legacy = stage_marker_legacy(window)
        self.assertEqual(legacy, "advance-stage")
        self.assertNotIn(legacy, DECLARED)

    def test_raw_keeps_an_undeclared_token_and_resolved_filters_it(self):
        raw, res = stage_marker.resolve("stage: brief\n\nstage: nowhere\n",
                                        [], DECLARED)
        self.assertEqual(raw, "nowhere")
        self.assertEqual(res, "brief")

    def test_no_marker_returns_none(self):
        self.assertEqual(stage_marker.resolve("a card with no marker\n", []),
                         (None, None))
        self.assertEqual(stage_marker.from_payload(
            dict(task=dict(id="t", body=""), comments=[])), (None, None))

    def test_comment_order_is_write_order(self):
        """Comments arrive oldest-first (kanban_db.list_comments: created_at ASC)."""
        raw, _res = stage_marker.resolve(
            "stage: brief\n", ["stage: genre-select\n", "stage: brief was left\n"])
        self.assertEqual(raw, "genre-select")


def stage_marker_legacy(window: str):
    """The pre-fix read, reproduced here to pin the incident it caused."""
    import re
    hits = re.findall(r"stage: ([a-z-]+)", window or "")
    return hits[-1] if hits else None


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
