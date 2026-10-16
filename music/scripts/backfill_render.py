#!/usr/bin/env python3
"""backfill_render — finish the delivery for a render the rail already made.

WHY THIS EXISTS (card t_d7f6d053, board music, measured 2026-10-16)
-----------------------------------------------------------------
Card t_b21aeb51 taught the render rail to BUILD and CERTIFY the delivered loop
(music/scripts/loop_close.py) instead of certifying a raw render whose tail is
digital silence. That fix only reaches the plan it has just rendered: the rail
decides what to do from `<stem>.rendered`, and a plan that was rendered BEFORE
the fix already carries that marker, so the rail skips it and will never
re-build its loop. The deliveries that are missing are, measured on the live
plans directory:

    /var/lib/music-plans/elemental-earth-chamber-loop.rendered  600 s loop claim,
      engine job 83d28d87c4894484afec77877a5819d2, artifact
      /var/lib/sunolocal/artifacts/suno-83d28d87….flac (53 736 489 B) — a REAL
      render, no master at the documented path, no loops/*.loop.wav.

Re-rendering (burning 3090 time for a plan whose render exists) is one way to
close that; this tool is the other, and the one this card took: the bytes of a
finished render are still in the engine's own store, so the master can be
RECOVERED to the documented path and the loop built from it with the render
untouched. The same pass is what makes every future pre-fix plan re-runnable,
so the rail is correct rather than one file being present.

WHAT IT DOES, in one pass per plan (the two halves share the mapping, so they
share the tool — a second backfill tool would be worse than the gap):
  1. RECOVER: a plan whose marker says "rendered" and whose render is NOT at
     the documented path (/var/lib/music-plans/<stem>.<ext>, card t_320bae4c,
     music/scripts/check_render_landed.py) gets the engine's own artifact copied
     to that path — byte-identical, sha256 verified, engine store read-only.
  2. CLOSE: if the plan CLAIMS a loop (its genre's video_shape in
     music/genres.yaml is loop-10min — the ONE definition, card t_b21aeb51) and
     its loop artifact is missing, music/scripts/loop_close.py builds the
     delivered loop from that master and the loop passes the rail's own check
     before anything is certified.
A second run is a NO-OP: nothing is written, nothing is measured twice into a
different file.

THE MAPPING IS EVIDENCE, NOT A GUESS
------------------------------------
The store's file names are job keys (`suno-<job-id>.<ext>`), which say nothing
about the plan, so the plan→render mapping is read from the store's own record
of the request it submitted (`/var/lib/sunolocal/jobs.sqlite3`, read-only): a
completed job matches when its stored request carries BOTH this plan's `title`
AND its `caption` (the full style prompt). One of the two is not enough — two
plans can share a title, and a caption can be edited after a render. When more
than one stored render matches and the master is missing, this tool REFUSES and
names them (`--job <id>` pins one explicitly): writing the wrong render to the
documented path would be a fabricated deliverable.

MODES
  --list [--plans DIR] [--store DIR] [--db PATH] [--json]
      Report every plan's state — marker, master at the documented path, loop
      artifact, the engine render resolved for it, and the action needed.
      Writes NOTHING.
  --plan FILE [--plans DIR] [--job ID] [--force-build-loop] [--json]
      Do the work for one plan (recover the master, close its loop).
  --all [--max-plans N] [--json]
      The rail's entry point: do the work for every plan that needs it.
  --selftest
      Prove every behaviour on real files in a scratch directory: RED on an
      unresolvable mapping, GREEN recovery with a hash check, GREEN loop build,
      the no-op second run, the refusal to guess between two renders, and the
      engine store left byte-for-byte untouched.

Exit codes: 0 = nothing to do, or every plan that needed work got it;
1 = at least one plan needed work and could NOT be finished (the record says
why); 2 = usage error. The rail runs --all and prints the outcome; a refusal
here does NOT stop the render loop, because a backfill is not a render.

Usage:
  python3 music/scripts/backfill_render.py --list
  python3 music/scripts/backfill_render.py --plan /var/lib/music-plans/x.json
  python3 music/scripts/backfill_render.py --all --max-plans 4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# ONE definition each, imported from the two scripts the rail already runs: the
# documented render path (card t_320bae4c) and what a marker MEANS (card
# t_69cab80b). This tool must not carry a second copy of either rule.
import check_render_landed   # noqa: E402
import render_state          # noqa: E402

# The engine's own store. READ-ONLY in this tool: the artifact is the engine's
# record of what it rendered, and the rail's copy at the documented path is what
# everything downstream reads (card t_320bae4c).
DEFAULT_STORE = "/var/lib/sunolocal/artifacts"
DEFAULT_DB = "/var/lib/sunolocal/jobs.sqlite3"
# The loop artifact's own paths, the same two the render rail writes.
LOOPS_DIR_NAME = "loops"
LOOP_FILE_SUFFIX = ".loop.wav"
LOOP_POINTS_SUFFIX = ".loop_points.json"
# The containers the engine produces (ace -> .flac, fixture -> .wav). Same order
# the rail's master_for() probes and check_render_landed.py documents.
ENGINE_EXTENSIONS = check_render_landed.DOCUMENTED_EXTENSIONS
DOCUMENTED_HOST_PATH = check_render_landed.DOCUMENTED_HOST_PATH

OK, REFUSED, USAGE = 0, 1, 2


# ── the engine store (read-only) ───────────────────────────────────────────

def store_rows(db: Path) -> list[dict]:
    """Every completed job in the engine's store, with its parsed request.

    Read-only (`mode=ro`): this tool never writes the engine's record. The
    connection is short-lived so a concurrent render's write cannot be blocked
    by it.
    """
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select job_id, request, created_at from jobs where status='completed'"
        ).fetchall()
    finally:
        con.close()
    out = []
    for job_id, request, created_at in rows:
        try:
            req = json.loads(request or "")
        except (TypeError, ValueError):
            req = {}
        out.append({"job": job_id, "request": req, "created_at": created_at})
    return out


def matching_jobs(rows: list[dict], plan: dict) -> list[dict]:
    """The completed jobs whose stored request names THIS plan.

    The match is the plan's own text: the request the engine stored carries the
    plan's `title` AND its `caption` (the full style prompt, which the wrapper
    submits as the prompt). Requiring both is what makes this evidence rather
    than a guess — a title alone can belong to two plans.
    """
    title, caption = plan.get("title"), plan.get("caption")
    if not title or not caption:
        return []
    return [r for r in rows
            if r["request"].get("title") == title
            and r["request"].get("prompt") == caption]


def artifact_of(job_id: str, store: Path) -> Path | None:
    for ext in ENGINE_EXTENSIONS:
        cand = store / f"suno-{job_id}.{ext}"
        if cand.is_file():
            return cand
    return None


def resolve_engine_render(plan: dict, rows: list[dict], store: Path,
                          pinned_job: str | None = None) -> dict:
    """The engine's own render of this plan, or the reason it cannot be named.

    Newest first: a re-render of the same plan is the delivered one, so when
    the caller has to choose it chooses the most recent stored render.
    """
    res: dict = {"candidates": [], "chosen": None, "artifact": None,
                 "bytes": None, "pinned": bool(pinned_job), "ambiguous": False,
                 "problems": []}
    pool = ([r for r in rows if r["job"] == pinned_job] if pinned_job
            else matching_jobs(rows, plan))
    if pinned_job and not pool:
        res["problems"].append(
            f"--job {pinned_job} is not a completed job in the engine's store")
        return res
    pool = sorted(pool, key=lambda r: r["created_at"], reverse=True)
    for r in pool:
        art = artifact_of(r["job"], store)
        res["candidates"].append({
            "job": r["job"], "created_at": r["created_at"],
            "artifact": str(art) if art else None,
            "bytes": art.stat().st_size if art else None})
    usable = [c for c in res["candidates"] if c["artifact"]]
    if not usable:
        if pinned_job:
            res["problems"].append(
                f"engine job {pinned_job} has no artifact in {store}")
        else:
            res["problems"].append(
                f"the engine store holds no completed render whose request "
                f"carries both this plan's title {plan.get('title')!r} and its "
                f"caption — nothing to recover from")
        return res
    res["chosen"] = usable[0]
    res["artifact"] = Path(usable[0]["artifact"])
    res["bytes"] = usable[0]["bytes"]
    res["ambiguous"] = len(usable) > 1
    return res


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ── half 1: recover the master to the documented path ──────────────────────

def recover_master(src: Path, dst: Path) -> str:
    """Copy the engine's artifact to the documented path. Returns its sha256.

    Written beside the destination and renamed, so a reader never sees a
    half-copied master at the documented path.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.parent / f".{dst.name}.part"
    try:
        with open(src, "rb") as g, open(tmp, "wb") as f:
            shutil.copyfileobj(g, f, 1024 * 1024)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dst)
        os.chmod(dst, 0o644)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return sha256_of(dst)


def recover_half(plan_path: Path, plan: dict, plans: Path, store: Path,
                 rows: list[dict], pinned_job: str | None) -> dict:
    """Bring this plan's master to the documented path, or say why it cannot."""
    stem = plan_path.stem
    master = check_render_landed.landed_file(plans, stem)
    out: dict = {"present": master is not None,
                 "path": str(master) if master else
                         str(plans / f"{stem}.{ENGINE_EXTENSIONS[0]}"),
                 "action": "no-op", "sha256": None, "bytes": None,
                 "engine": None, "problems": []}
    engine = resolve_engine_render(plan, rows, store, pinned_job)
    out["engine"] = engine
    if master is not None:
        # Nothing to recover. Say what the bytes ARE, so a master that did not
        # come from the render the marker describes is visible rather than
        # assumed: a re-render stores a new artifact, and a pruned store has
        # none at all.
        out["bytes"] = master.stat().st_size
        out["sha256"] = sha256_of(master)
        # Say which stored render these bytes ARE: a re-render stores a new
        # artifact and a pruned store has none, so "the marker certifies a
        # render that is no longer in the store" should be visible rather than
        # assumed.
        matched = [c for c in engine["candidates"]
                   if c["artifact"] and sha256_of(Path(c["artifact"]))
                   == out["sha256"]]
        if matched:
            engine["chosen"] = matched[0]
            engine["match"] = "hash"
        elif len(engine["candidates"]) == 1:
            engine["match"] = "single-candidate-unverified"
        else:
            engine["match"] = "unresolved"
        return out

    if engine["problems"]:
        out["action"] = "refused"
        out["problems"] = list(engine["problems"])
        return out
    if engine["ambiguous"]:
        # Two stored renders of this plan, no master to tell them apart: refuse
        # rather than write a coin flip to the path every stage reads.
        out["action"] = "refused"
        named = ", ".join(f"{c['job']} ({c['bytes']} B, "
                          f"{c['created_at']:.0f})" for c in engine["candidates"]
                          if c["artifact"])
        out["problems"] = [
            f"{len(named.split(', '))} stored renders of this plan match its "
            f"title+caption and no master exists to tell them apart: {named} "
            f"— pass --job <id> to name the delivered one"]
        return out

    src = engine["artifact"]
    # The extension is the ENGINE's, not a default: the contract says a finished
    # render lands at /var/lib/music-plans/<stem>.<ext> where <ext> is the
    # container the engine produced (ace -> .flac, fixture -> .wav). Writing a
    # .wav render to a .flac name would put the right bytes behind the wrong
    # name and every probing stage would read it as something it is not.
    dst = plans / f"{stem}{src.suffix}"
    out["path"] = str(dst)
    try:
        out["sha256"] = recover_master(src, dst)
    except OSError as exc:
        out["action"] = "refused"
        out["problems"] = [
            f"cannot write the documented path {out['path']}: {exc} "
            f"(the plans dir is the rail's own mount; run this as root, or in "
            f"the render pod)"]
        return out
    out["action"] = "recovered"
    out["bytes"] = Path(out["path"]).stat().st_size
    src_sha = sha256_of(src)
    if src_sha != out["sha256"]:
        out["problems"].append(
            f"the recovered file's sha256 {out['sha256']} does not equal the "
            f"engine artifact's {src_sha} — the copy is NOT the render")
        out["action"] = "refused"
    out["engine"]["match"] = "hash" if src_sha == out["sha256"] else "mismatch"
    return out


# ── half 2: build and certify the delivered loop ───────────────────────────

def loop_artifact_paths(plans: Path, stem: str) -> tuple[Path, Path]:
    base = plans / LOOPS_DIR_NAME / stem
    return (base.with_name(stem + LOOP_FILE_SUFFIX),
            base.with_name(stem + LOOP_POINTS_SUFFIX))


def run_json(cmd: list[str]) -> tuple[int, dict | None, str]:
    """Run one of the lane's scripts with --json and parse its record."""
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    payload = None
    try:
        payload = json.loads(proc.stdout)
    except (TypeError, ValueError):
        payload = None
    return proc.returncode, payload, (proc.stderr or proc.stdout or "").strip()


def loop_half(plan_path: Path, plans: Path, master: Path, loop_close: Path,
              genres: Path | None, build: bool) -> dict:
    """Close and certify the delivered loop for a loop-claiming plan.

    The claim, the loop build and the certification are all
    music/scripts/loop_close.py — the rail's own script — so a backfilled loop
    is the same artifact a fresh render would have produced.
    """
    stem = plan_path.stem
    loop_wav, loop_points = loop_artifact_paths(plans, stem)
    out: dict = {"claim": None, "action": "not-a-claim", "path": str(loop_wav),
                 "loop_points": str(loop_points), "size_s": None, "bars": None,
                 "start_s": None, "level_delta_db": None, "checked": None,
                 "problems": []}
    claim_cmd = [sys.executable, str(loop_close), "--claims-loop",
                 "--plan", str(plan_path), "--json"]
    if genres is not None:
        claim_cmd += ["--genres-yaml", str(genres)]
    rc, claim, tail = run_json(claim_cmd)
    out["claim"] = (claim or {}).get("claim")
    if rc not in (0, 1):
        # A loop claim that cannot be resolved is not evidence of "no loop".
        # The rail fails closed here too; so does the backfill.
        out["action"] = "refused"
        out["problems"] = [f"the plan's loop claim could not be resolved "
                           f"(rc={rc}): {tail[:200]}"]
        return out
    if rc == 1:
        out["action"] = "not-a-claim"
        return out

    loop_wav_exists = loop_wav.is_file()
    loop_points_exists = loop_points.is_file()
    if loop_wav_exists and loop_points_exists and not build:
        out["action"] = "no-op"
    else:
        cmd = [sys.executable, str(loop_close), "--master", str(master),
               "--plan", str(plan_path), "--out", str(loop_wav),
               "--loop-points-out", str(loop_points), "--json"]
        if genres is not None:
            cmd += ["--genres-yaml", str(genres)]
        rc, rec, tail = run_json(cmd)
        rec = rec or {}
        if rc != 0:
            out["action"] = "loop-refused-needs-render"
            out["problems"] = ((rec or {}).get("problems") or
                               [tail[-400:] or "loop_close failed"])
            return out
        out["action"] = "built"
        out["size_s"] = rec.get("span_s")
        out["bars"] = rec.get("bars")
        out["start_s"] = rec.get("start_s")
        out["level_delta_db"] = rec.get("level_delta_db")

    # Certify what is on disk NOW, whether this run built it or found it. This
    # is the same check the rail runs on the artifact it is about to certify.
    chk = [sys.executable, str(loop_close), "--check-only", "--master",
           str(loop_wav), "--json"]
    rc, info, tail = run_json(chk)
    out["checked"] = "PASS" if rc == 0 else "FAIL"
    if out["level_delta_db"] is None and isinstance(info, dict):
        out["level_delta_db"] = (info.get("info") or {}).get("level_delta_db")
    if rc != 0:
        out["action"] = "loop-refused-needs-render"
        out["problems"] = ((info or {}).get("problems") or
                           [tail[-400:] or "the loop check failed"])
        return out
    if out["action"] == "built" and not loop_points.is_file():
        out["problems"].append(
            f"{loop_points} was not written — the loop artifact has no "
            f"loop_points.json")
    return out


# ── one plan ───────────────────────────────────────────────────────────────

def stem_record(plans: Path, stem: str) -> dict:
    """What the rail's state machine says about this stem, in one place.

    A backfill may only act on a stem whose marker says a render FINISHED: an
    unreadable `.rendered` means the rail re-attempts the render, and the
    sticky states (.looprefused, .noartifact) are the rail's "do not come back
    here without a human" — a backfill that ignored them would re-do work the
    lane decided to stop.
    """
    rendered = render_state.marker(plans, stem, render_state.RENDERED)
    kind, payload = render_state.read_marker(rendered)
    sticky = None
    for state in (render_state.LOOPREFUSED, render_state.NOARTIFACT,
                  render_state.REFUSED):
        p = render_state.marker(plans, stem, state)
        if p.is_file():
            sticky = state
            break
    if sticky:
        state = sticky
    elif kind == "finished":
        state = render_state.RENDERED
    else:
        state = "none" if kind == "absent" else kind
    return {"stem": stem, "state": state, "marker": str(rendered),
            "marker_kind": kind, "marker_payload": payload, "sticky": sticky}


def run_plan(plan_path: Path, plans: Path, store: Path, rows: list[dict],
             loop_close: Path, genres: Path | None, pinned_job: str | None,
             build: bool, act: bool) -> dict:
    stem = plan_path.stem
    rec = stem_record(plans, stem)
    rec["plan"] = str(plan_path)
    rec["master"] = None
    rec["loop"] = None
    rec["problems"] = []
    rec["changed"] = False
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        rec["problems"].append(f"cannot read the plan: {exc}")
        rec["action"] = "refused"
        return rec
    if not isinstance(plan, dict):
        rec["problems"].append("the plan is not a JSON object")
        rec["action"] = "refused"
        return rec

    rec["action"] = "none"
    if rec["state"] != render_state.RENDERED:
        # Report what the engine holds, so --list answers the whole question,
        # but do not act: the rail owns these states.
        rec["engine"] = resolve_engine_render(plan, rows, store, pinned_job)
        return rec

    if not act:
        present = check_render_landed.landed_file(plans, stem)
        rec["master"] = {"path": str(present or
                                    plans / f"{stem}.{ENGINE_EXTENSIONS[0]}"),
                         "present": present is not None,
                         "action": "present" if present else "missing"}
        rec["engine"] = resolve_engine_render(plan, rows, store, pinned_job)
        loop_wav, loop_points = loop_artifact_paths(plans, stem)
        if loop_wav.is_file() and loop_points.is_file():
            loop_action = "present"
        elif loop_wav.is_file() or loop_points.is_file():
            loop_action = "partial"
        else:
            loop_action = "missing"
        rec["loop"] = {"action": loop_action, "present": loop_wav.is_file(),
                       "path": str(loop_wav)}
        return rec

    mh = recover_half(plan_path, plan, plans, store, rows, pinned_job)
    rec["master"] = mh
    rec["engine"] = mh.pop("engine")
    rec["problems"] += mh["problems"]
    if mh["action"] == "refused":
        rec["action"] = "refused"
        return rec
    if mh["action"] == "recovered":
        rec["changed"] = True

    master = check_render_landed.landed_file(plans, stem)
    if master is None:
        rec["action"] = "refused"
        rec["problems"].append("no master at the documented path after the copy")
        return rec
    lh = loop_half(plan_path, plans, master, loop_close, genres, build)
    rec["loop"] = lh
    rec["problems"] += lh["problems"]
    if lh["action"] == "built":
        rec["changed"] = True
    if lh["action"] in ("refused", "loop-refused-needs-render"):
        rec["action"] = lh["action"]
    elif rec["changed"]:
        rec["action"] = "done"
    else:
        rec["action"] = "no-op"
    return rec


# ── reporting ──────────────────────────────────────────────────────────────

def print_record(rec: dict, as_json: bool) -> None:
    if as_json:
        return
    print(f"{rec['stem']}")
    print(f"  marker   : {rec['state']}"
          + (f" (kind {rec['marker_kind']})" if rec.get("marker_kind") else ""))
    eng = rec.get("engine") or {}
    chosen = eng.get("chosen")
    if chosen:
        print(f"  engine   : {chosen['job']}  {Path(chosen['artifact']).name}"
              f"  {chosen['bytes']} B"
              + (f"  (of {len(eng['candidates'])} matching renders)"
                 if eng.get("candidates") else ""))
        if eng.get("match"):
            print(f"  engine→master: {eng['match']}")
    else:
        for p in (eng.get("problems") or []):
            print(f"  engine   : {p}")
    m = rec.get("master") or {}
    if m:
        print(f"  master   : {m['action'].upper()} {m['path']}"
              + (f"  {m['bytes']} B  sha256 {str(m['sha256'])[:16]}…"
                 if m.get("sha256") else ""))
    lp = rec.get("loop") or {}
    if lp:
        line = f"  loop     : {lp['action'].upper()}"
        if lp.get("size_s"):
            line += (f" {lp['path']} ({lp['size_s']:.3f}s, {lp['bars']} bars, "
                     f"from {lp['start_s']:.3f}s)")
        elif lp.get("path"):
            line += f" {lp['path']}"
        if lp.get("level_delta_db") is not None:
            line += f"  delta {lp['level_delta_db']:.1f} dB"
        print(line)
        if lp.get("checked"):
            print(f"  check    : {lp['checked']} loop_close --check-only")
    for p in (rec.get("problems") or []):
        print(f"  PROBLEM  : {p}")


def summarise(records: list[dict]) -> dict:
    s = {"plans": len(records), "recovered": 0, "loops_built": 0,
         "no_op": 0, "refused": 0, "needs_render": 0, "not_acted": 0,
         "failed": 0}
    for r in records:
        m = (r.get("master") or {}).get("action")
        l = (r.get("loop") or {}).get("action")
        if m == "recovered":
            s["recovered"] += 1
        if l == "built":
            s["loops_built"] += 1
        if r.get("action") == "refused":
            s["refused"] += 1
            s["failed"] += 1
        elif r.get("action") == "loop-refused-needs-render":
            s["needs_render"] += 1
            s["failed"] += 1
        elif r.get("action") == "no-op":
            s["no_op"] += 1
        elif r.get("action") == "none":
            s["not_acted"] += 1
    return s


# ── cli ────────────────────────────────────────────────────────────────────

def selftest() -> int:
    """RED and GREEN on real files, in a scratch directory.

    Every case builds its own plans dir, engine store and store DB, so the
    assertions do not depend on what the live board happens to hold.
    """
    import loop_close as loop_close_mod   # the lane's ffmpeg resolution

    ff = loop_close_mod.find_ffmpeg() / "ffmpeg"
    checks: list[tuple[str, bool, str]] = []
    loop_close = HERE / "loop_close.py"
    genres = HERE.parent / "genres.yaml"

    def expect(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    def store_snapshot(store: Path) -> list[tuple]:
        return sorted((p.name, p.stat().st_size, sha256_of(p))
                      for p in store.iterdir())

    def make_plan(path: Path, title: str, caption: str, genre: str,
                  bpm: float = 150.0, duration: int = 120) -> None:
        path.write_text(json.dumps({
            "title": title, "caption": caption, "bpm": bpm,
            "key": "C minor", "duration": duration, "instrumental": True,
            "_meta": {"genre": genre}}, indent=2) + "\n", encoding="utf-8")

    def make_db(db: Path, jobs: list[tuple[str, dict, float]]) -> None:
        con = sqlite3.connect(db)
        con.execute("create table jobs (job_id text primary key, request text "
                    "not null, status text not null, result text, created_at "
                    "real not null, updated_at real not null)")
        for job_id, req, ts in jobs:
            con.execute("insert into jobs values (?,?,'completed',NULL,?,?)",
                        (job_id, json.dumps(req), ts, ts))
        con.commit()
        con.close()

    def tone_with_silence(out: Path, music_s: float, silence_s: float,
                          freq: float = 220.0) -> None:
        """music_s of a steady tone, then silence_s of digital silence.

        The container is the file's own extension — a render the engine stored
        is `.flac`, and a fixture engine's is `.wav`, exactly as the rail's
        master_for() probes for them.
        """
        codec = "flac" if out.suffix == ".flac" else "pcm_s16le"
        proc = subprocess.run(
            [str(ff), "-v", "error", "-y",
             "-f", "lavfi", "-i",
             f"sine=frequency={int(freq)}:sample_rate=44100:duration={music_s}",
             "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-filter_complex",
             "[0:a]aformat=channel_layouts=mono[a];"
             f"[1:a]atrim=0:{silence_s},asetpts=PTS-STARTPTS[b];"
             "[a][b]concat=n=2:v=0:a=1[out]",
             "-map", "[out]", "-c:a", codec, str(out)],
            capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"fixture synth failed: {proc.stderr.strip()}")

    def run_tool(plans: Path, store: Path, db: Path, *args: str):
        cmd = [sys.executable, os.path.abspath(__file__), *args,
               "--plans", str(plans), "--store", str(store), "--db", str(db),
               "--loop-close", str(loop_close), "--genres-yaml", str(genres)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        return p.returncode, (p.stdout or "") + (p.stderr or "")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        plans = root / "plans"
        store = root / "artifacts"
        plans.mkdir()
        store.mkdir()

        # ---- RED: a marker that certifies a render the store cannot name.
        make_plan(plans / "orphan-loop.json", "Orphan", "orphan caption",
                  "elemental-earth")
        (plans / "orphan-loop.rendered").write_text("")
        # ---- GREEN: one stored render, matched on title+caption.
        make_plan(plans / "recover-me.json", "Recover Me", "recover caption",
                  "chill-lounge")
        (plans / "recover-me.rendered").write_text("")
        (store / "suno-aaa.flac").write_bytes(b"fLaC" + b"\x00" * 512)
        # ---- a fixture engine's render is a .wav (the ext is the engine's).
        make_plan(plans / "wav-render.json", "Wav Render", "wav caption",
                  "sentimental-piano")
        (plans / "wav-render.rendered").write_text("")
        (store / "suno-bbb.wav").write_bytes(b"RIFF" + b"\x00" * 256)
        # ---- AMBIGUOUS: two stored renders of one plan, no master.
        make_plan(plans / "two-renders.json", "Two Renders", "two caption",
                  "elemental-air")
        (plans / "two-renders.rendered").write_text("")
        (store / "suno-ccc.flac").write_bytes(b"fLaC" + b"C" * 512)
        (store / "suno-ddd.flac").write_bytes(b"fLaC" + b"D" * 900)
        # ---- STICKY: the rail has parked this stem; a backfill must not act.
        make_plan(plans / "sticky-loop.json", "Sticky", "sticky caption",
                  "elemental-earth")
        (plans / "sticky-loop.rendered").write_text("")
        (plans / "sticky-loop.looprefused").write_text("refused once\n")
        (store / "suno-eee.flac").write_bytes(b"fLaC" + b"\x00" * 64)
        # ---- GREEN loop claim: a real, closable render (tone + silence tail).
        make_plan(plans / "loop-claim.json", "Loop Claim", "loop caption",
                  "elemental-earth", bpm=150.0, duration=25)
        (plans / "loop-claim.rendered").write_text("")
        tone_with_silence(store / "suno-fff.flac", 20.6, 5.0)

        jobs = [
            ("aaa", {"title": "Recover Me", "prompt": "recover caption"}, 100.0),
            ("bbb", {"title": "Wav Render", "prompt": "wav caption"}, 101.0),
            ("ccc", {"title": "Two Renders", "prompt": "two caption"}, 102.0),
            ("ddd", {"title": "Two Renders", "prompt": "two caption"}, 103.0),
            ("eee", {"title": "Sticky", "prompt": "sticky caption"}, 104.0),
            ("fff", {"title": "Loop Claim", "prompt": "loop caption"}, 105.0),
        ]
        db = root / "jobs.sqlite3"
        make_db(db, jobs)

        before_store = store_snapshot(store)
        before_db = sha256_of(db)

        # --list writes nothing at all.
        rc, out = run_tool(plans, store, db, "--list")
        expect("--list reports without writing", rc == 0, f"rc={rc}\n{out}")
        expect("--list names the plan with no engine render",
               "nothing to recover" in out, out)
        expect("--list does not create a master",
               not (plans / "recover-me.flac").exists())

        # --all does the work for every stem that needs it.
        rc, out = run_tool(plans, store, db, "--all")
        expect("--all exits 1 when one plan cannot be finished",
               rc == 1, f"rc={rc}\n{out}")
        expect("RED: the unresolvable mapping is REFUSED, naming the store",
               "nothing to recover" in out and "refused" in out.lower(), out)
        expect("RED: the ambiguous plan is REFUSED with both jobs named",
               "ccc" in out and "ddd" in out, out)
        expect("GREEN: the .flac render is recovered to the documented path",
               (plans / "recover-me.flac").is_file(), out)
        expect("GREEN: the recovered bytes ARE the engine artifact's",
               (plans / "recover-me.flac").read_bytes()
               == (store / "suno-aaa.flac").read_bytes(), out)
        expect("GREEN: the ext is the engine's (.wav render -> .wav master)",
               (plans / "wav-render.wav").is_file(), out)
        expect("the documented-path contract agrees the render landed",
               subprocess.run(
                   [sys.executable, str(HERE / "check_render_landed.py"),
                    "--check", "--plans", str(plans), "--stem", "recover-me",
                    "--host-path", DOCUMENTED_HOST_PATH],
                   capture_output=True, text=True).returncode == 0)
        expect("the loop claim is closed and certified",
               "built" in out and (plans / "loops" / "loop-claim.loop.wav").is_file(),
               out)
        expect("the loop artifact has its loop_points.json",
               (plans / "loops" / "loop-claim.loop_points.json").is_file(), out)
        expect("the built loop PASSes the rail's own check",
               "PASS loop_close --check-only" in out, out)
        expect("STICKY: a .looprefused stem is not acted on",
               not (plans / "sticky-loop.flac").exists(), out)
        expect("a non-loop claim builds no loop artifact",
               not (plans / "loops" / "recover-me.loop.wav").exists(), out)

        # The engine's store is the engine's: read-only, byte for byte.
        expect("the engine store is untouched (names, sizes, hashes)",
               store_snapshot(store) == before_store)
        expect("the engine store DB is untouched", sha256_of(db) == before_db)

        # ---- the second run is a NO-OP, and still certifies what is there.
        stamp = {p: (p.stat().st_mtime_ns, sha256_of(p))
                 for p in sorted(plans.rglob("*")) if p.is_file()}
        rc2, out2 = run_tool(plans, store, db, "--all")
        after = {p: (p.stat().st_mtime_ns, sha256_of(p))
                 for p in sorted(plans.rglob("*")) if p.is_file()}
        expect("the second run is a no-op (no file changed)",
               stamp == after, f"run1={stamp}\nrun2={after}")
        expect("the no-op run still reports the certification",
               "PASS loop_close --check-only" in out2, out2)
        expect("the no-op run reports the master as a no-op",
               "NO-OP" in out2, out2)

        # ---- --job resolves the ambiguity explicitly.
        rc3, out3 = run_tool(plans, store, db, "--plan",
                             str(plans / "two-renders.json"), "--job", "ddd")
        expect("--job names the delivered render and recovers it",
               (plans / "two-renders.flac").is_file()
               and (plans / "two-renders.flac").read_bytes()
               == (store / "suno-ddd.flac").read_bytes(), out3)

    bad = 0
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}"
              + ("" if ok else f"\n        {detail.strip()[:600]}"))
        bad += 0 if ok else 1
    if bad:
        print(f"\n{len(checks) - bad}/{len(checks)} checks behaved")
        print(f"BROKEN: {bad} check(s) misbehaved")
        return 1
    print(f"\nOK: {len(checks)} checks behaved (refuses what it cannot name, "
          f"recovers what the store holds, closes the loop, no-op on re-run, "
          f"never writes the engine's store)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="backfill_render — recover a plan's render from the "
                    "engine's store and close its delivered loop, with no "
                    "re-render (card t_d7f6d053)")
    p.add_argument("--plans", default=DOCUMENTED_HOST_PATH,
                   help="the plans dir (the documented render path)")
    p.add_argument("--store", default=DEFAULT_STORE,
                   help="the engine's artifact store (read-only)")
    p.add_argument("--db", default=DEFAULT_DB,
                   help="the engine's job store (read-only)")
    p.add_argument("--loop-close", default=str(HERE / "loop_close.py"))
    p.add_argument("--genres-yaml", default=None)
    p.add_argument("--job", default=None,
                   help="pin the engine job id for an ambiguous plan")
    p.add_argument("--max-plans", type=int, default=0,
                   help="stop after N plans that needed work (0 = no cap)")
    p.add_argument("--build-loop", action="store_true",
                   help="re-build the loop even when the artifact exists")
    p.add_argument("--list", action="store_true")
    p.add_argument("--plan", default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    modes = [args.list, bool(args.plan), args.all, args.selftest]
    if sum(1 for m in modes if m) != 1:
        print("usage: pick exactly one of --list, --plan FILE, --all, "
              "--selftest", file=sys.stderr)
        return USAGE
    if args.selftest:
        return selftest()

    plans = Path(args.plans)
    store = Path(args.store)
    db_path = Path(args.db)
    loop_close = Path(args.loop_close)
    genres = Path(args.genres_yaml) if args.genres_yaml else None
    if genres is None:
        cand = HERE.parent / "genres.yaml"
        genres = cand if cand.is_file() else None
    if not loop_close.is_file():
        print(f"FATAL: no loop_close at {loop_close}", file=sys.stderr)
        return USAGE
    if not plans.is_dir():
        print(f"FATAL: no plans dir at {plans}", file=sys.stderr)
        return USAGE

    if args.plan:
        plan_paths = [Path(args.plan)]
    else:
        plan_paths = sorted(plans.glob("*.json"))
    if not plan_paths and args.plan:
        print(f"FATAL: no plan at {args.plan}", file=sys.stderr)
        return USAGE

    rows: list[dict] = []
    db_problem = None
    if db_path.is_file():
        try:
            rows = store_rows(db_path)
        except sqlite3.Error as exc:
            db_problem = f"cannot read the engine store {db_path}: {exc}"
    else:
        db_problem = f"no engine store DB at {db_path}"

    records: list[dict] = []
    changed = 0
    for plan_path in plan_paths:
        act = bool(args.plan or args.all)
        # A refusal needs no act, but the DECISION does; --list never acts.
        rec = run_plan(plan_path, plans, store, rows, loop_close, genres,
                       args.job, args.build_loop, act)
        if db_problem:
            rec["problems"].append(db_problem)
            if rec["state"] == render_state.RENDERED:
                rec["action"] = "refused"
        records.append(rec)
        if rec["changed"]:
            changed += 1
        if args.max_plans and changed >= args.max_plans:
            print(f"       stopped after {args.max_plans} plan(s) that needed "
                  f"work (--max-plans)", file=sys.stderr)
            break

    for rec in records:
        print_record(rec, args.json)
    summary = summarise(records)
    if args.json:
        print(json.dumps({"plans": records, "summary": summary}, indent=2))
    else:
        print(f"backfill_render: {summary['plans']} plan(s) — "
              f"recovered={summary['recovered']} "
              f"loops_built={summary['loops_built']} "
              f"no_op={summary['no_op']} refused={summary['refused']} "
              f"needs_render={summary['needs_render']} "
              f"not_acted={summary['not_acted']} "
              f"(plans={plans}, store={store})")
    return REFUSED if summary["failed"] else OK


if __name__ == "__main__":
    sys.exit(main())
