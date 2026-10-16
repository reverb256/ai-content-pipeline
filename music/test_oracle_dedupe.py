#!/usr/bin/env python3
"""music/test_oracle_dedupe.py — regression tests for the oracle's open-card guard.

INCIDENT (2026-10-09, found while working card t_96821eed)
----------------------------------------------------------
music/oracle.py created a card for every genre above the score threshold on
every run, with no check for a card that was already open. Two runs ten
minutes apart produced 28 cards for 14 genres:

    performance/music-oracle-runs.log
    2026-10-09T03:27:53 — oracle run: 14 scored, 14 created, top=chill-lounge(8.9)
    2026-10-09T03:37:53 — oracle run: 14 scored, 14 created, top=chill-lounge(9.1)

Each duplicate put a second full stage chain in flight for the same genre
(six duplicate cards were claimed by the dispatcher on 2026-10-16 12:59:50).

The guard: open_oracle_genres() maps genre -> open card id, and the run skips
any genre that already has one. A failed board read fails CLOSED — no cards.

Run:  /usr/bin/python3 music/test_oracle_dedupe.py
Exit: 0 = all pass, 1 = failure.
"""

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

MUSIC_DIR = Path(__file__).resolve().parent

# Load music/oracle.py by path: music/ is not a package (no __init__.py).
_spec = importlib.util.spec_from_file_location("music_oracle", MUSIC_DIR / "oracle.py")
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load {MUSIC_DIR / 'oracle.py'}")
oracle: Any = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oracle)


def board_task(task_id: str, title: str, status: str) -> dict:
    """One entry of `hermes kanban --board music list --json` output."""
    return {"id": task_id, "title": title, "status": status}


# Titles and ids copied from the live board (2026-10-16).
REAL_BOARD = [
    board_task("t_38e84953", "music-oracle: chill-lounge (score 8.9)", "running"),
    board_task("t_9f7d6889", "music-oracle: sentimental-piano (score 8.9)", "running"),
    board_task("t_96821eed", "music-oracle: anime-opening (score 7.55)", "running"),
    board_task("t_abaa7e2d", "music-oracle: anime-opening (score 7.75)", "ready"),
    board_task("t_4c838339", "music-oracle: chill-lounge (score 9.1)", "ready"),
    board_task("t_2541fd9c", "music-oracle: anime-ending (score 7.65)", "blocked"),
    board_task("t_006db63d", "music-oracle: jungle-dnb (score 7.0)", "review"),
    board_task("t_deadone1", "music: Virtual Reflections — export, preserve", "ready"),
    board_task("t_deadone2", "music-oracle: activist (score 7.25)", "done"),
    board_task("t_deadone3", "music-oracle: trance (score 8.3)", "archived"),
]


class FakeRun:
    """Stand-in for oracle.subprocess.run that records every call."""

    def __init__(self, list_payload=None, list_returncode=0, list_stdout=None):
        self.calls = []
        self.bodies = {}
        self.list_payload = list_payload
        self.list_returncode = list_returncode
        self.list_stdout = list_stdout

    def __call__(self, cmd, capture_output=True, text=True, **kwargs):
        self.calls.append(list(cmd))
        if "list" in cmd:
            if self.list_stdout is not None:
                return subprocess.CompletedProcess(cmd, self.list_returncode,
                                                   self.list_stdout, "")
            return subprocess.CompletedProcess(
                cmd, self.list_returncode,
                json.dumps(self.list_payload if self.list_payload is not None else []), "")
        if "create" in cmd:
            # Capture the body before create_kanban_card unlinks it.
            if "--body-file" in cmd:
                body_path = Path(cmd[cmd.index("--body-file") + 1])
                self.bodies[cmd[cmd.index("create") + 1]] = body_path.read_text()
            return subprocess.CompletedProcess(cmd, 0, "t_created\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def create_calls(self):
        return [c for c in self.calls if "create" in c]


class TitleGrammarTest(unittest.TestCase):
    """card_title and genre_from_title must round-trip the board's titles."""

    def test_round_trip_real_titles(self):
        for genre, total in (("anime-opening", 7.55), ("chill-lounge", 8.9),
                             ("commentary-beds", 8.1), ("chiptune-8bit", 7.5)):
            title = oracle.card_title(genre, total)
            self.assertEqual(oracle.genre_from_title(title), genre, title)

    def test_grammar_matches_titles_already_on_the_board(self):
        self.assertEqual(
            oracle.card_title("anime-opening", 7.55),
            "music-oracle: anime-opening (score 7.55)")

    def test_non_oracle_titles_are_ignored(self):
        for title in ("music: Virtual Reflections — export, preserve",
                      "ops: fix Longhorn attach failure",
                      "test-probe", ""):
            self.assertIsNone(oracle.genre_from_title(title), title)


class OpenGenresTest(unittest.TestCase):
    """open_oracle_genres() reads the board and reports in-flight genres."""

    def _call(self, fake):
        original = oracle.subprocess.run
        oracle.subprocess.run = fake
        try:
            return oracle.open_oracle_genres("music")
        finally:
            oracle.subprocess.run = original

    def test_maps_every_open_genre_once(self):
        fake = FakeRun(list_payload=REAL_BOARD)
        open_genres = self._call(fake)
        self.assertEqual(open_genres, {
            "chill-lounge": "t_38e84953",      # first open card wins
            "sentimental-piano": "t_9f7d6889",
            "anime-opening": "t_96821eed",
            "anime-ending": "t_2541fd9c",
            "jungle-dnb": "t_006db63d",
        })
        # done / archived are closed: activist must NOT be listed.
        self.assertNotIn("activist", open_genres)

    def test_queries_the_music_board_as_json(self):
        fake = FakeRun(list_payload=REAL_BOARD)
        self._call(fake)
        self.assertEqual(fake.calls[0],
                         ["hermes", "kanban", "--board", "music", "list", "--json"])

    def test_cli_failure_returns_none(self):
        fake = FakeRun(list_payload=None, list_returncode=1, list_stdout="boom")
        self.assertIsNone(self._call(fake))

    def test_malformed_json_returns_none(self):
        fake = FakeRun(list_stdout="{not json")
        self.assertIsNone(self._call(fake))

    def test_non_list_json_returns_none(self):
        fake = FakeRun(list_stdout='{"tasks": []}')
        self.assertIsNone(self._call(fake))


class NoDuplicateCardTest(unittest.TestCase):
    """The incident: a genre with an open card must not get a second card."""

    def setUp(self):
        # The trend signal does a live web fetch. Pin it: the test measures the
        # dedupe, not the network.
        self._trend = oracle.trend_signal_score
        oracle.trend_signal_score = lambda genre: 5.0

    def tearDown(self):
        oracle.trend_signal_score = self._trend

    def _run(self, fake, open_genres):
        original_run = oracle.subprocess.run
        original_open = oracle.open_oracle_genres
        oracle.subprocess.run = fake
        oracle.open_oracle_genres = lambda board: open_genres
        try:
            with redirect_stdout(io.StringIO()):
                return oracle.run_oracle()
        finally:
            oracle.subprocess.run = original_run
            oracle.open_oracle_genres = original_open

    def test_every_genre_open_creates_nothing(self):
        """The second run of 2026-10-09 — the state that produced 28 cards."""
        fake = FakeRun(list_payload=REAL_BOARD)
        all_genres = {g: f"t_{g}" for g in oracle.load_registry()["genres"]}
        summary = self._run(fake, all_genres)

        self.assertEqual(fake.create_calls(), [],
                         "a genre with an open card must not get another card")
        self.assertEqual(summary["cards_created"], 0)
        self.assertEqual(sorted(summary["skipped_existing"]), sorted(all_genres))
        self.assertTrue(summary["board_read_ok"])

    def test_only_the_missing_genre_gets_a_card(self):
        fake = FakeRun(list_payload=REAL_BOARD)
        all_genres = set(oracle.load_registry()["genres"])
        open_genres = {g: f"t_{g}" for g in all_genres - {"anime-opening"}}
        summary = self._run(fake, open_genres)

        creates = fake.create_calls()
        self.assertEqual(len(creates), 1, f"expected exactly one create: {creates}")
        cmd = creates[0]
        title = cmd[cmd.index("create") + 1]
        self.assertTrue(title.startswith("music-oracle: anime-opening (score "), title)
        self.assertEqual(summary["cards_created"], 1)

        # Routing contract: the board and the assignee the dispatcher needs.
        self.assertEqual(cmd[:4], ["hermes", "kanban", "--board", "music"])
        self.assertEqual(cmd[cmd.index("--assignee") + 1], "music-producer")

        # Stage contract: the driver finds the card's stage in the body.
        body = fake.bodies[title]
        self.assertIn("stage: brief", body)

    def test_unreadable_board_fails_closed(self):
        """A failed board read must never become a flood of new cards."""
        fake = FakeRun(list_stdout="boom", list_returncode=1)
        summary = self._run(fake, None)

        self.assertEqual(fake.create_calls(), [],
                         "no cards may be created when the board cannot be read")
        self.assertEqual(summary["cards_created"], 0)
        self.assertFalse(summary["board_read_ok"])


class DryRunTest(unittest.TestCase):
    """--dry-run must not touch the board at all."""

    def test_dry_run_creates_nothing_and_does_not_list(self):
        trend = oracle.trend_signal_score
        oracle.trend_signal_score = lambda genre: 5.0
        fake = FakeRun(list_payload=REAL_BOARD)
        original_run = oracle.subprocess.run
        oracle.subprocess.run = fake
        try:
            with redirect_stdout(io.StringIO()):
                summary = oracle.run_oracle(dry_run=True)
        finally:
            oracle.subprocess.run = original_run
            oracle.trend_signal_score = trend

        self.assertEqual([c for c in fake.calls if "kanban" in c], [],
                         "--dry-run must not call the kanban CLI")
        self.assertEqual(summary["cards_created"], 0)


if __name__ == "__main__":
    # Import-time guard: oracle.py needs PyYAML (like /usr/bin/python3 has).
    if "yaml" not in sys.modules:
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            print("SKIP: run this test with an interpreter that has PyYAML "
                  "(e.g. /usr/bin/python3)", file=sys.stderr)
            sys.exit(1)
    unittest.main(verbosity=2)
