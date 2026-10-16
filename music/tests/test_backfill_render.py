#!/usr/bin/env python3
"""test_backfill_render — the backfill must refuse what it cannot name.

WHY THIS SUITE EXISTS (card t_d7f6d053, board music, 2026-10-16)
---------------------------------------------------------------
`music/scripts/backfill_render.py` finishes the delivery for a plan whose
`.rendered` marker certifies a render that is not at the documented path: it
recovers the master from the engine's own store and closes the plan's loop with
no re-render. Its whole value, and its whole risk, is the plan→render mapping:
writing the WRONG stored render to `/var/lib/music-plans/<stem>.<ext>` would put
a fabricated master in front of every stage that consumes one. So the cases
below are the mapping's rules, each measured on a fixture store:

  * a job matches only when its stored request carries BOTH the plan's title
    AND its caption (a title alone belongs to two plans sooner or later);
  * a stored render with no artifact in the store is not a candidate;
  * two usable candidates and no master to tell them apart is a REFUSAL that
    names them, not a coin flip;
  * the recovering copy uses the ENGINE's extension (a `.wav` fixture render
    must not land as `.flac`), verifies its own sha256, and leaves no `.part`;
  * an existing master is a NO-OP that reports whether the store still holds
    those bytes;
  * the engine's store is READ-ONLY: no artifact, and no row, changes;
  * a stem the rail has parked (`.looprefused`, `.noartifact`, `.refused`) or a
    `.rendered` marker the state machine cannot read is NOT acted on;
  * a loop claim whose render cannot carry a loop gets NO marker: a backfill
    refusal means the plan needs a RENDER, and the rail's own `.looprefused`
    would park it forever.

Run: python3 -m unittest music.tests.test_backfill_render   (from the repo root)
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "music" / "scripts"
TOOL = SCRIPTS / "backfill_render.py"
LOOP_CLOSE = SCRIPTS / "loop_close.py"
GENRES = REPO / "music" / "genres.yaml"
sys.path.insert(0, str(SCRIPTS))

import backfill_render as bf          # noqa: E402
import loop_close as loop_close_mod   # noqa: E402


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ffmpeg() -> Path | None:
    """The lane's ffmpeg, resolved the way the lane's own scripts resolve it."""
    return loop_close_mod.find_ffmpeg() / "ffmpeg"


def has_ffmpeg() -> bool:
    f = ffmpeg()
    return bool(f) and f.is_file()


def make_plan(path: Path, title: str, caption: str, genre: str,
              bpm: float = 150.0, duration: int = 120) -> None:
    path.write_text(json.dumps({
        "title": title, "caption": caption, "bpm": bpm, "key": "C minor",
        "duration": duration, "instrumental": True,
        "_meta": {"genre": genre}}, indent=2) + "\n", encoding="utf-8")


def make_store_db(db: Path, jobs: list[tuple[str, dict, float, str]]) -> None:
    """(job_id, request, created_at, status) rows in the engine's own schema."""
    con = sqlite3.connect(db)
    con.execute("create table jobs (job_id text primary key, request text "
                "not null, status text not null, result text, created_at real "
                "not null, updated_at real not null)")
    for job_id, req, ts, status in jobs:
        con.execute("insert into jobs values (?,?,?,NULL,?,?)",
                    (job_id, json.dumps(req), status, ts, ts))
    con.commit()
    con.close()


def synth(out: Path, music_s: float, silence_s: float, freq: int = 220) -> None:
    """music_s of a steady tone, then silence_s of digital silence."""
    codec = "flac" if out.suffix == ".flac" else "pcm_s16le"
    proc = subprocess.run(
        [str(ffmpeg()), "-v", "error", "-y",
         "-f", "lavfi", "-i",
         f"sine=frequency={freq}:sample_rate=44100:duration={music_s}",
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-filter_complex",
         "[0:a]aformat=channel_layouts=mono[a];"
         f"[1:a]atrim=0:{silence_s},asetpts=PTS-STARTPTS[b];"
         "[a][b]concat=n=2:v=0:a=1[out]",
         "-map", "[out]", "-c:a", codec, str(out)],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"fixture synth failed: {proc.stderr.strip()}")


class Fixture(unittest.TestCase):
    """A scratch plans dir, an engine store and its job DB."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.plans = root / "plans"
        self.store = root / "artifacts"
        self.plans.mkdir()
        self.store.mkdir()
        self.db = root / "jobs.sqlite3"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers --------------------------------------------------------
    def plan(self, stem: str, title: str, caption: str, genre: str,
             marker: str = "rendered", bpm: float = 150.0,
             duration: int = 120) -> Path:
        p = self.plans / f"{stem}.json"
        make_plan(p, title, caption, genre, bpm, duration)
        if marker == "rendered":
            (self.plans / f"{stem}.rendered").write_text("")
        elif marker:
            (self.plans / f"{stem}.{marker}").write_text("parked\n")
        return p

    def artifact(self, job: str, ext: str = "flac", payload: bytes | None = None):
        p = self.store / f"suno-{job}.{ext}"
        p.write_bytes(payload if payload is not None else b"fLaC" + b"\x00" * 256)
        return p

    def store_state(self) -> dict:
        return {p.name: (p.stat().st_size, sha256_of(p))
                for p in sorted(self.store.iterdir())}

    def run_tool(self, *args: str, plans: Path | None = None,
                 store: Path | None = None, db: Path | None = None):
        cmd = [sys.executable, str(TOOL), *args,
               "--plans", str(plans or self.plans),
               "--store", str(store or self.store),
               "--db", str(db or self.db),
               "--loop-close", str(LOOP_CLOSE),
               "--genres-yaml", str(GENRES)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


class TestMapping(Fixture):
    """The plan→render mapping is evidence, and only evidence."""

    def test_a_title_alone_is_not_a_match(self):
        plan = self.plan("solo", "Shared Title", "this plan's own caption",
                         "chill-lounge")
        self.artifact("j1")
        make_store_db(self.db, [("j1", {"title": "Shared Title",
                                        "prompt": "ANOTHER plan's caption"},
                                 100.0, "completed")])
        rows = bf.store_rows(self.db)
        self.assertEqual(bf.matching_jobs(rows, json.loads(plan.read_text())), [])

    def test_both_title_and_caption_are_required(self):
        plan = self.plan("both", "T", "C", "chill-lounge")
        self.artifact("j1")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        rows = bf.store_rows(self.db)
        got = bf.matching_jobs(rows, json.loads(plan.read_text()))
        self.assertEqual([r["job"] for r in got], ["j1"])

    def test_a_failed_job_is_never_a_source(self):
        plan = self.plan("failed", "T", "C", "chill-lounge")
        self.artifact("j1")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "failed")])
        self.assertEqual(bf.matching_jobs(bf.store_rows(self.db),
                                          json.loads(plan.read_text())), [])

    def test_a_completed_job_with_no_artifact_is_not_usable(self):
        plan = self.plan("noart", "T", "C", "chill-lounge")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        res = bf.resolve_engine_render(json.loads(plan.read_text()),
                                       bf.store_rows(self.db), self.store)
        self.assertIsNone(res["artifact"])
        self.assertEqual(len(res["candidates"]), 1)
        self.assertTrue(res["problems"])

    def test_two_usable_renders_are_reported_newest_first_and_ambiguous(self):
        plan = self.plan("two", "T", "C", "chill-lounge")
        self.artifact("old", payload=b"fLaC" + b"o" * 64)
        self.artifact("new", payload=b"fLaC" + b"n" * 64)
        make_store_db(self.db, [("old", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed"),
                                ("new", {"title": "T", "prompt": "C"}, 200.0,
                                 "completed")])
        res = bf.resolve_engine_render(json.loads(plan.read_text()),
                                       bf.store_rows(self.db), self.store)
        self.assertTrue(res["ambiguous"])
        self.assertEqual(res["chosen"]["job"], "new")

    def test_a_pinned_job_overrides_the_mapping(self):
        plan = self.plan("pin", "T", "C", "chill-lounge")
        self.artifact("old", payload=b"fLaC" + b"o" * 64)
        self.artifact("new", payload=b"fLaC" + b"n" * 64)
        make_store_db(self.db, [("old", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed"),
                                ("new", {"title": "T", "prompt": "C"}, 200.0,
                                 "completed")])
        res = bf.resolve_engine_render(json.loads(plan.read_text()),
                                       bf.store_rows(self.db), self.store,
                                       pinned_job="old")
        self.assertEqual(res["chosen"]["job"], "old")
        self.assertTrue(res["pinned"])


class TestRecoverHalf(Fixture):
    """Half 1: the master at the documented path, or a named refusal."""

    def recover(self, stem: str, job: str, pinned: str | None = None):
        plan_path = self.plans / f"{stem}.json"
        plan = json.loads(plan_path.read_text())
        return bf.recover_half(plan_path, plan, self.plans, self.store,
                              bf.store_rows(self.db), pinned)

    def test_a_wav_render_lands_as_wav_not_flac(self):
        # <ext> is the container the ENGINE produced (the contract's own words);
        # a .wav written to a .flac name is the right bytes behind the wrong
        # name and every probing stage would read it as something it is not.
        self.plan("wavonly", "T", "C", "sentimental-piano")
        src = self.artifact("j1", ext="wav", payload=b"RIFF" + b"w" * 128)
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        out = self.recover("wavonly", "j1")
        self.assertEqual(out["action"], "recovered")
        self.assertTrue((self.plans / "wavonly.wav").is_file())
        self.assertFalse((self.plans / "wavonly.flac").exists())
        self.assertEqual(sha256_of(self.plans / "wavonly.wav"), sha256_of(src))

    def test_the_copy_verifies_its_hash_and_leaves_no_part_file(self):
        self.plan("copy", "T", "C", "chill-lounge")
        src = self.artifact("j1", payload=b"fLaC" + b"x" * 4096)
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        out = self.recover("copy", "j1")
        self.assertEqual(out["sha256"], sha256_of(src))
        self.assertEqual(out["engine"]["match"], "hash")
        self.assertEqual(list(self.plans.glob(".*.part")), [])
        self.assertEqual(bf.check_render_landed.landed_file(self.plans, "copy"),
                         self.plans / "copy.flac")

    def test_an_existing_master_is_a_no_op_that_reports_the_hash_match(self):
        self.plan("have", "T", "C", "chill-lounge")
        src = self.artifact("j1", payload=b"fLaC" + b"h" * 512)
        shutil.copyfile(src, self.plans / "have.flac")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        before = (self.plans / "have.flac").stat().st_mtime_ns
        out = self.recover("have", "j1")
        self.assertEqual(out["action"], "no-op")
        self.assertEqual(out["engine"]["match"], "hash")
        self.assertEqual((self.plans / "have.flac").stat().st_mtime_ns, before)

    def test_an_unresolvable_mapping_refuses_and_writes_nothing(self):
        self.plan("orphan", "Orphan", "orphan caption", "elemental-earth")
        make_store_db(self.db, [])
        out = self.recover("orphan", "none")
        self.assertEqual(out["action"], "refused")
        self.assertEqual(
            sorted(p.name for p in self.plans.iterdir()),
            ["orphan.json", "orphan.rendered"])
        self.assertTrue(any("nothing to recover from" in p
                            for p in out["problems"]), out["problems"])

    def test_two_candidates_and_no_master_refuses_and_names_both(self):
        self.plan("amb", "T", "C", "chill-lounge")
        self.artifact("ccc", payload=b"fLaC" + b"c" * 64)
        self.artifact("ddd", payload=b"fLaC" + b"d" * 64)
        make_store_db(self.db, [("ccc", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed"),
                                ("ddd", {"title": "T", "prompt": "C"}, 200.0,
                                 "completed")])
        out = self.recover("amb", "x")
        self.assertEqual(out["action"], "refused")
        self.assertFalse((self.plans / "amb.flac").exists())
        joined = " ".join(out["problems"])
        self.assertIn("ccc", joined)
        self.assertIn("ddd", joined)

    def test_the_engine_store_is_never_written(self):
        self.plan("copy", "T", "C", "chill-lounge")
        self.artifact("j1", payload=b"fLaC" + b"x" * 512)
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        before_store = self.store_state()
        before_db = sha256_of(self.db)
        self.recover("copy", "j1")
        self.assertEqual(self.store_state(), before_store)
        self.assertEqual(sha256_of(self.db), before_db)


class TestStemState(Fixture):
    """Half 0: which stems a backfill may touch at all."""

    def test_an_empty_rendered_marker_is_a_finished_render(self):
        self.plan("ok", "T", "C", "chill-lounge")
        self.assertEqual(bf.stem_record(self.plans, "ok")["state"], "rendered")

    def test_a_fingerprinted_rendered_marker_is_a_finished_render(self):
        self.plan("ok2", "T", "C", "chill-lounge")
        (self.plans / "ok2.rendered").write_text("rendered abc 2026-10-16T00:00Z")
        self.assertEqual(bf.stem_record(self.plans, "ok2")["state"], "rendered")

    def test_a_looprefused_stem_is_not_acted_on(self):
        self.plan("parked", "T", "C", "elemental-earth", marker="looprefused")
        self.artifact("j1")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        rec = bf.run_plan(self.plans / "parked.json", self.plans, self.store,
                          bf.store_rows(self.db), LOOP_CLOSE, GENRES, None,
                          False, True)
        self.assertEqual(rec["action"], "none")
        self.assertFalse((self.plans / "parked.flac").exists())

    def test_a_refused_stem_is_not_acted_on(self):
        self.plan("draft", "T", "C", "chill-lounge", marker="refused")
        self.artifact("j1")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        rec = bf.run_plan(self.plans / "draft.json", self.plans, self.store,
                          bf.store_rows(self.db), LOOP_CLOSE, GENRES, None,
                          False, True)
        self.assertEqual(rec["action"], "none")
        self.assertFalse((self.plans / "draft.flac").exists())

    def test_an_unreadable_rendered_marker_is_not_acted_on(self):
        # The state machine re-attempts the RENDER for this shape, so the
        # backfill must not treat the bytes as a finished delivery.
        self.plan("odd", "T", "C", "chill-lounge")
        (self.plans / "odd.rendered").write_text("something else entirely\n")
        self.artifact("j1")
        make_store_db(self.db, [("j1", {"title": "T", "prompt": "C"}, 100.0,
                                 "completed")])
        rec = bf.run_plan(self.plans / "odd.json", self.plans, self.store,
                          bf.store_rows(self.db), LOOP_CLOSE, GENRES, None,
                          False, True)
        self.assertEqual(rec["action"], "none")
        self.assertFalse((self.plans / "odd.flac").exists())


@unittest.skipUnless(has_ffmpeg(), "the lane's ffmpeg is not locatable")
class TestEndToEnd(Fixture):
    """The whole tool on a fixture: recover, close, no-op, and a refusal."""

    def test_recover_and_close_then_a_second_run_is_a_no_op(self):
        self.plan("earth", "Loop Claim", "loop caption", "elemental-earth",
                  bpm=150.0, duration=25)
        synth(self.store / "suno-fff.flac", 20.6, 5.0)
        make_store_db(self.db, [("fff", {"title": "Loop Claim",
                                         "prompt": "loop caption"}, 100.0,
                                 "completed")])
        db_sha, store_before = sha256_of(self.db), self.store_state()

        rc, out = self.run_tool("--plan", str(self.plans / "earth.json"))
        self.assertEqual(rc, 0, out)
        self.assertTrue((self.plans / "earth.flac").is_file(), out)
        self.assertEqual(sha256_of(self.plans / "earth.flac"),
                         sha256_of(self.store / "suno-fff.flac"))
        loop = self.plans / "loops" / "earth.loop.wav"
        lp = self.plans / "loops" / "earth.loop_points.json"
        self.assertTrue(loop.is_file(), out)
        self.assertTrue(lp.is_file(), out)
        self.assertIn("PASS loop_close --check-only", out)
        self.assertEqual(json.loads(lp.read_text())["seamless"], True)
        # The engine's store is untouched: no artifact changed, no row added.
        self.assertEqual(self.store_state(), store_before)
        self.assertEqual(sha256_of(self.db), db_sha)

        files = {p: (p.stat().st_mtime_ns, sha256_of(p))
                 for p in sorted(self.plans.rglob("*")) if p.is_file()}
        rc2, out2 = self.run_tool("--all")
        after = {p: (p.stat().st_mtime_ns, sha256_of(p))
                 for p in sorted(self.plans.rglob("*")) if p.is_file()}
        self.assertEqual(rc2, 0, out2)
        self.assertEqual(files, after, "the second run changed a file")
        self.assertIn("NO-OP", out2)
        self.assertIn("PASS loop_close --check-only", out2)

    def test_a_render_that_cannot_carry_a_loop_gets_no_marker(self):
        # The render is shorter than one bar, so no bar-aligned loop fits.
        # A backfill refusal means this plan needs a RE-RENDER: writing
        # .looprefused (the rail's sticky state) would park it forever.
        self.plan("tiny", "Tiny", "tiny caption", "elemental-earth",
                  bpm=150.0, duration=1)
        synth(self.store / "suno-tiny.flac", 1.0, 0.0)
        make_store_db(self.db, [("tiny", {"title": "Tiny",
                                          "prompt": "tiny caption"}, 100.0,
                                 "completed")])
        rc, out = self.run_tool("--plan", str(self.plans / "tiny.json"))
        self.assertEqual(rc, 1, out)
        self.assertIn("NEEDS_RENDER", out.replace("-", "_"), out)
        self.assertTrue((self.plans / "tiny.flac").is_file(), out)
        self.assertFalse((self.plans / "tiny.looprefused").exists())
        self.assertFalse((self.plans / "loops" / "tiny.loop.wav").exists())

    def test_a_non_loop_genre_recovers_its_master_and_builds_no_loop(self):
        self.plan("chill", "Slow", "chill caption", "chill-lounge")
        synth(self.store / "suno-cl.flac", 5.0, 0.5)
        make_store_db(self.db, [("cl", {"title": "Slow",
                                        "prompt": "chill caption"}, 100.0,
                                 "completed")])
        rc, out = self.run_tool("--plan", str(self.plans / "chill.json"))
        self.assertEqual(rc, 0, out)
        self.assertTrue((self.plans / "chill.flac").is_file(), out)
        self.assertFalse((self.plans / "loops" / "chill.loop.wav").exists())
        self.assertIn("NOT-A-CLAIM", out)


if __name__ == "__main__":
    unittest.main()
