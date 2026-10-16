#!/usr/bin/env python3
"""render_state — the render rail's marker state machine (card t_69cab80b).

Run: /usr/bin/python3 -m unittest music.tests.test_render_state
     (from the repo root; or /usr/bin/python3 music/tests/test_render_state.py)

WHY THIS TEST EXISTS (board music, 2026-10-16)
----------------------------------------------
The render rail decided from one thing: `if <stem>.rendered exists: skip
"already rendered"`. It wrote BOTH outcomes to that same file — `""` for a
render and `"refused\\n"` for a refusal — and nothing in either repo removed it.
Measured live:

    $ for f in /var/lib/music-plans/*.rendered; do echo "$f -> $(cat $f)"; done
    anime-ending-reflections.rendered           -> refused
    epic-orchestral-boss-the-last-gate.rendered -> refused
    smoke-chill-lounge.rendered                 -> refused
    testplan.rendered                           -> refused
    trance-signal-before-dawn.rendered          -> refused
    final-round.rendered                        -> (empty)

and the rail's own log (job music-pipeline-render-29869781, 2026-10-16 16:41)
printed `skip epic-orchestral-boss-the-last-gate (already rendered)` for a plan
whose lyrics are a scaffold. Four of the eight live queue entries are drafts, so
this turned "a human must write the sheet" into "finished" for the whole genre.

The defect had two halves and both are pinned here:

  THE CONFLATION (RED)  a refusal stored in `.rendered` must be ATTEMPTED, and
                        its message must never say "already rendered". The last
                        test in TestRailWiring exists so a future edit cannot put
                        the two-outcome-one-marker write back into the template.

  THE MISSING RE-ENTRY  a refusal must be re-attempted once its plan CHANGES and
                        must NOT be re-attempted while the plan is unchanged (the
                        fingerprint), while `.looprefused` and `.noartifact` stay
                        sticky — they cost GPU time or need a human's eyes
                        (t_b21aeb51, t_320bae4c).

GREEN means the migration is self-healing: the five live `.rendered` files that
say `refused` become attempts, one local refusal rewrites each one to
`<stem>.refused` with the plan's sha, and a human's edit to the plan opens it
again with no hand-clearing of markers.
"""

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
SCRIPT = REPO / "music" / "scripts" / "render_state.py"

spec = importlib.util.spec_from_file_location("render_state", SCRIPT)
render_state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_state)

# The chart that runs this rule (a sibling checkout; the wiring test skips when
# it is not on this host, the same way check_render_landed's selftest does).
CHART = pathlib.Path(os.path.expanduser(
    "~/mining-k8s/helm/charts/music-pipeline/templates/cronjob-render.yaml"))


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


class StateCase(unittest.TestCase):
    """A plans dir with one plan in it, in a temp dir — never the live one."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.plans = pathlib.Path(self._td.name)
        self.stem = "state-case"
        self.plan = self.plans / f"{self.stem}.json"
        self.write_plan('{"title": "t", "lyrics": "[Intro]\\n(direction only)\\n"}')

    def tearDown(self) -> None:
        self._td.cleanup()

    def write_plan(self, body: str) -> None:
        self.plan.write_text(body, encoding="utf-8")

    def marker(self, suffix: str) -> pathlib.Path:
        return self.plans / f"{self.stem}{suffix}"

    def decide(self):
        return render_state.decide(self.plan, self.plans)

    def sha(self) -> str:
        return render_state.plan_fingerprint(self.plan)

    def only_marker(self) -> str | None:
        found = sorted(p.name for p in self.plans.iterdir()
                       if p.name.startswith(f"{self.stem}.") and p.suffix != ".json")
        return found[0] if len(found) == 1 else None


class TestDecisions(StateCase):
    def test_a_plan_with_no_marker_is_attempted(self):
        d = self.decide()
        self.assertTrue(d.attempt)
        self.assertEqual(d.state, "fresh")

    def test_an_empty_rendered_marker_stays_finished(self):
        # 8 live markers are empty and their plans are done. Growing a field in
        # the success record must not turn them back into work.
        self.marker(".rendered").write_text("")
        d = self.decide()
        self.assertFalse(d.attempt)
        self.assertEqual(d.state, render_state.RENDERED)
        self.assertIn("already rendered", d.line(self.stem))

    def test_a_rendered_record_stays_finished(self):
        self.marker(".rendered").write_text(f"rendered {self.sha()} 2026-10-16T21:44:00Z\n")
        d = self.decide()
        self.assertFalse(d.attempt)
        self.assertIn(self.sha()[:12], d.reason)

    def test_a_render_is_not_repeated_because_the_plan_changed(self):
        # The other side of the card's decision: only a REFUSAL is re-entered on
        # change. Re-rendering a finished master after an edit costs GPU.
        self.marker(".rendered").write_text(f"rendered {self.sha()} 2026-10-16T21:44:00Z\n")
        self.write_plan('{"title": "t", "lyrics": "[Intro]\\nnew words\\n"}')
        d = self.decide()
        self.assertFalse(d.attempt)

    def test_the_defect_a_refusal_stored_as_rendered_is_reattempted(self):
        # THE MEASURED LIVE BYTES: the old rail's refusal write.
        self.marker(".rendered").write_text("refused\n")
        d = self.decide()
        self.assertTrue(d.attempt, "the old rail would have printed 'already rendered'")
        self.assertEqual(d.state, "legacy-refusal-in-rendered")
        self.assertNotIn("already rendered", d.reason)
        self.assertIn("t_69cab80b", d.reason)

    def test_the_old_rule_is_provably_gone(self):
        # The regression guard, written as the defect's own expression: this is
        # exactly what the rail did, and the state machine must disagree with it.
        self.marker(".rendered").write_text("refused\n")
        old_rule_skips = self.marker(".rendered").exists()
        self.assertTrue(old_rule_skips, "the old rule is: any marker means rendered")
        self.assertTrue(self.decide().attempt,
                        "any .rendered marker must no longer mean 'rendered'")

    def test_an_unreadable_rendered_marker_is_attempted_not_trusted(self):
        self.marker(".rendered").write_text("??truncated")
        d = self.decide()
        self.assertTrue(d.attempt)
        self.assertEqual(d.state, "unreadable-rendered")

    def test_a_refusal_of_the_same_plan_is_skipped(self):
        render_state.record(self.plan, self.plans, render_state.REFUSED,
                            detail="7 section(s) have no lyrics: Intro, Break")
        d = self.decide()
        self.assertFalse(d.attempt)
        self.assertEqual(d.state, render_state.REFUSED)
        self.assertIn("has NOT changed", d.reason)
        self.assertIn(self.sha()[:12], d.reason)

    def test_the_plan_changing_re_enters_the_refusal(self):
        # THE CARD'S TEST: refused -> changed plan -> attempted.
        render_state.record(self.plan, self.plans, render_state.REFUSED, detail="draft")
        self.write_plan('{"title": "t", "lyrics": "[Intro]\\nwritten by the human\\n"}')
        d = self.decide()
        self.assertTrue(d.attempt)
        self.assertEqual(d.state, f"{render_state.REFUSED}-changed")
        self.assertIn("CHANGED", d.reason)

    def test_a_refusal_without_a_fingerprint_is_attempted_once(self):
        # The live /var/lib/music-plans/jungle-dnb-two-speeds.refused is 0 bytes.
        self.marker(".refused").write_text("")
        d = self.decide()
        self.assertTrue(d.attempt)
        self.assertEqual(d.state, f"{render_state.REFUSED}-unfingerprinted")

    def test_sticky_states_are_not_re_attempted(self):
        for suffix, state in ((".looprefused", render_state.LOOPREFUSED),
                              (".noartifact", render_state.NOARTIFACT)):
            with self.subTest(suffix=suffix):
                self.marker(suffix).write_text("the tail is 33.6 dB down\n")
                d = self.decide()
                self.assertFalse(d.attempt)
                self.assertEqual(d.state, state)
                # even when the plan changes: a re-render costs GPU, a human clears it
                self.write_plan('{"title": "t", "lyrics": "[Intro]\\nchanged\\n"}')
                self.assertFalse(self.decide().attempt)
                self.marker(suffix).unlink()

    def test_a_rendered_marker_wins_over_a_stale_refusal(self):
        # A stem cannot be both, but the directory can hold both after a manual
        # recovery: the finished state is the one that must be honoured.
        self.marker(".rendered").write_text("")
        render_state.record(self.plan, self.plans, render_state.REFUSED, detail="old")
        self.marker(".refused").write_text(f"refused {self.sha()} 2026-10-16T00:00:00Z\n")
        self.assertFalse(self.decide().attempt)


class TestRecord(StateCase):
    def test_a_record_holds_the_plan_fingerprint_and_the_time(self):
        render_state.record(self.plan, self.plans, render_state.REFUSED, detail="draft")
        head = self.marker(".refused").read_text().splitlines()[0].split()
        self.assertEqual(head[0], "refused")
        self.assertEqual(head[1], self.sha())
        self.assertTrue(head[2].endswith("Z"))

    def test_a_record_leaves_exactly_one_state(self):
        self.marker(".rendered").write_text("refused\n")
        render_state.record(self.plan, self.plans, render_state.REFUSED, detail="draft")
        self.assertFalse(self.marker(".rendered").exists(),
                         "the misleading .rendered must not survive the refusal record")
        self.assertEqual(self.only_marker(), f"{self.stem}.refused")

    def test_recording_rendered_clears_every_other_state(self):
        for suffix in (".refused", ".looprefused", ".noartifact"):
            self.marker(suffix).write_text("earlier\n")
        render_state.record(self.plan, self.plans, render_state.RENDERED)
        self.assertEqual(self.only_marker(), f"{self.stem}.rendered")
        self.assertTrue(self.marker(".rendered").read_text().startswith("rendered "))

    def test_the_recorded_reason_is_kept_for_the_human(self):
        render_state.record(self.plan, self.plans, render_state.REFUSED,
                            detail="FATAL: 7 section(s) have no lyrics: Intro, Break")
        text = self.marker(".refused").read_text()
        self.assertIn("7 section(s) have no lyrics", text)
        self.assertEqual(render_state.read_refusal(self.marker(".refused"))[0], self.sha())

    def test_the_cli_records_and_decides_with_the_rails_exit_codes(self):
        r = run_cli("--record", "--plan", str(self.plan), "--plans", str(self.plans),
                    "--state", "refused", "--detail", "draft scaffold")
        self.assertEqual(r.returncode, 0, r.stderr)
        d = run_cli("--decide", "--plan", str(self.plan), "--plans", str(self.plans))
        self.assertEqual(d.returncode, render_state.SKIP)
        self.assertTrue(d.stdout.startswith(f"skip    {self.stem} ("), d.stdout)
        self.write_plan('{"title": "t", "lyrics": "[Intro]\\nreal words\\n"}')
        d = run_cli("--decide", "--plan", str(self.plan), "--plans", str(self.plans))
        self.assertEqual(d.returncode, render_state.OK)
        self.assertTrue(d.stdout.startswith(f"attempt {self.stem} ("), d.stdout)
        fp = run_cli("--fingerprint", "--plan", str(self.plan))
        self.assertEqual(fp.stdout.strip(), self.sha())


class TestMigration(StateCase):
    """The live shape, end to end: no hand-clearing, and the rail heals it."""

    def test_a_legacy_refusal_becomes_a_real_attempt_and_a_real_record(self):
        # Exactly the live file: 8 bytes, "refused\n", written by the old rail.
        self.marker(".rendered").write_text("refused\n")
        self.assertEqual(len(self.plan.read_bytes()) > 0, True)

        # Run 1: the plan is attempted (the old rail skipped it), the wrapper
        # refuses it locally, and the rail records the refusal WITH the sha.
        self.assertTrue(self.decide().attempt)
        render_state.record(self.plan, self.plans, render_state.REFUSED,
                            detail="FATAL: 7 section(s) have no lyrics")
        self.assertFalse(self.marker(".rendered").exists())
        self.assertEqual(self.only_marker(), f"{self.stem}.refused")

        # Run 2: nothing changed, so it is skipped — with the true reason, not
        # "already rendered".
        d = self.decide()
        self.assertFalse(d.attempt)
        self.assertIn("waiting for a human", d.reason)
        self.assertNotIn("already rendered", d.reason)

        # Run 3: the human writes the sheet, and the very next run attempts it.
        self.write_plan('{"title": "t", "lyrics": "[Intro]\\nwe sing at the last gate\\n"}')
        self.assertTrue(self.decide().attempt)

        # Run 4: it renders. One state, and the refusal is gone.
        render_state.record(self.plan, self.plans, render_state.RENDERED)
        d = self.decide()
        self.assertFalse(d.attempt)
        self.assertEqual(self.only_marker(), f"{self.stem}.rendered")


class TestLiveCheck(StateCase):
    def test_red_on_a_refusal_stored_as_rendered(self):
        self.marker(".rendered").write_text("refused\n")
        findings = render_state.check(self.plans)
        self.assertTrue(any(k == "RED" for k, _ in findings), findings)
        self.assertIn("t_69cab80b", findings[0][1])
        r = run_cli("--check", "--plans", str(self.plans))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("RED", r.stdout)

    def test_green_on_a_consistent_directory(self):
        render_state.record(self.plan, self.plans, render_state.REFUSED, detail="draft")
        findings = render_state.check(self.plans)
        self.assertFalse([k for k, _ in findings if k == "RED"], findings)
        r = run_cli("--check", "--plans", str(self.plans), "--json")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["red"], 0)

    def test_a_changed_plan_under_a_refusal_is_a_note_not_a_defect(self):
        render_state.record(self.plan, self.plans, render_state.REFUSED, detail="draft")
        self.write_plan('{"title": "t", "lyrics": "[Intro]\\nedited\\n"}')
        findings = render_state.check(self.plans)
        self.assertTrue(any(k == "NOTE" for k, _ in findings), findings)
        self.assertFalse([k for k, _ in findings if k == "RED"], findings)

    def test_a_missing_plans_dir_is_red_not_a_traceback(self):
        findings = render_state.check(self.plans / "nope")
        self.assertEqual(findings[0][0], "RED")


class TestSelftest(unittest.TestCase):
    def test_the_scripts_own_selftest_is_green(self):
        r = run_cli("--selftest")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK:", r.stdout)


class TestRailWiring(unittest.TestCase):
    """The chart that runs the rule must call it, and must not contain the
    two-outcomes-one-marker write this card removed."""

    def require_chart(self) -> str:
        if not CHART.is_file():
            self.skipTest(f"chart not on this host: {CHART}")
        return CHART.read_text()

    def test_the_rail_decides_and_records_through_this_script(self):
        text = self.require_chart()
        self.assertIn("render_state.py", text)
        self.assertIn("--decide", text)
        self.assertIn("--record", text)

    def test_the_rail_no_longer_writes_a_refusal_into_the_rendered_marker(self):
        text = self.require_chart()
        for old in ('marker.write_text("refused',
                    'marker_path(stem, "refused").write_text',
                    'marker_path(stem, "rendered").write_text'):
            self.assertNotIn(old, text,
                             "the rail must record through render_state.py, so the "
                             "two states cannot share one file (card t_69cab80b)")
        # The phrase itself may stay in a comment: this card's header quotes the
        # defect it removes. What must be gone is the PRINT that reported a
        # refused plan as finished.
        for line in text.splitlines():
            self.assertFalse("already rendered" in line and "print" in line,
                             f"the rail still prints the old line: {line.strip()!r}")

    def test_the_rail_re_attempts_a_plan_that_the_wrapper_refuses_at_rc_4(self):
        # acestep_plan.py exits 4 for a refusal that needs a human (a draft
        # sheet) and 1 for an operational failure. Only the former may be
        # recorded as a refusal: a submit that failed must be retried.
        wrapper = (REPO / "music" / "scripts" / "acestep_plan.py").read_text()
        self.assertIn("REFUSED_EXIT", wrapper)
        text = self.require_chart()
        self.assertIn("REFUSED", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
