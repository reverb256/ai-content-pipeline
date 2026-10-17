#!/usr/bin/env python3
"""check_render_ledger — a delivered render must be in the render log.

WHY THIS EXISTS (card t_d6b0cb36, board music, measured 2026-10-16)
------------------------------------------------------------------
`music/quota-ledger.json` says of its own `renders:` list:

    "_renders_note": "... They are recorded here because this file is the
     pipeline's only durable render log and card t_b8afb055 asks for the
     render to be recorded in it."

So an unrecorded render is a DEFECT, not an omission. Measured on nexus:

    $ ls /var/lib/music-plans/*.rendered        # every one of them a marker
    $ python3 -c "import json;print(len(json.load(open('music/quota-ledger.json'))['renders']))"
    1

One entry, eight finished renders. Seven delivered masters were absent:

    chill-lounge-slow-gold, commentary-beds-lo-fi-jazz-bed,
    commentary-beds-lo-fi-jazz-sting, elemental-earth-chamber-loop,
    elemental-fire-emberfall, final-round,
    sentimental-piano-room-with-the-light-going

`/var/lib/sunolocal/artifacts/` held the audio for all of them, so the music
existed: the LOG was short. Nothing kept the two in step, which is why every
card that queues a genre had to remember to append an entry by hand — and a
hand-written log is not a log.

WHO WRITES AN ENTRY: THE CHECK, NOT THE RAIL (the card's first decision)
------------------------------------------------------------------------
The render rail already knows the plan, the engine job id and the artifact it
produced, so appending the entry there looked like the robust option. It cannot
be done, and the reason is structural rather than a missing line of code:

  * the render pod mounts `/payload` from the chart's ConfigMap **readOnly**
    (mining-k8s helm/charts/music-pipeline/templates/cronjob-render.yaml) and
    its only writable volume is the plans hostPath `/var/lib/music-plans`;
  * this ledger is `music/quota-ledger.json` in the **lane repo**, whose reader
    is `music/oracle.py:load_quota` (`MUSIC_DIR / "quota-ledger.json"`);
  * `grep -rn quota-ledger /home/j_kro/mining-k8s` returns NOTHING: the chart
    has no channel to the file at all.

So a rail-side write means mounting a user's git working tree into a root-run
pod, which would make every render leave the repo dirty under root ownership
and bypass review — a worse defect than the one being fixed. The card names
this case: "If the rail cannot commit, the answer is the check, not the
auto-write." That is this file. It is the same shape as its two siblings, whose
rules the rail DOES run because they live in the pod's payload:
`check_render_landed.py` (card t_320bae4c, where a render lands) and
`render_state.py` (card t_69cab80b, what a marker means).

THE RULE
--------
A DELIVERED RENDER IS IN THE LOG. For every marker the rail itself reads as a
finished render (`render_state.read_marker` — the ONE definition, imported, not
copied), the ledger must carry one `renders[]` entry whose `name` is that
marker's stem.

  * A marker that is NOT a finished render (a `refused`/`looprefused`/
    `noartifact` state, or the legacy `refused` text) is NOT a delivered render
    and needs NO entry — the card says so explicitly: "Do NOT write a ledger
    entry for a `refused` marker: those are drafts waiting on a human."
  * A plan the pipeline did not write (its `_meta.genre` is not in
    `music/genres.yaml`) is not a delivered render either. The planner validates
    the genre against that registry, so a plan outside it cannot have come from
    the pipeline — this is what keeps the rail's own smoke plan (`testplan.json`,
    genre `test`) out of the log. Reported as a NOTE, not a failure.

RED is a delivered render with no entry: that is the undercount this card is
about. NOTEs are the other directions of drift (an entry with no marker left;
an entry whose recorded `sha256`/`bytes` no longer match the master on disk).
They stay NOTEs deliberately — the log is evidence a human reads, and the
incident to page on is the missing entry.

MODES
  --check [--plans DIR] [--ledger FILE] [--genres FILE] [--json]
      exit 0  in step (NOTEs are printed and do not fail the check)
      exit 1  RED: at least one delivered render has no ledger entry
      exit 2  usage error
      exit 3  REFUSED: the check cannot answer — the plans directory is not
              there, the ledger will not parse, or the genre registry is
              missing. A check that cannot check must not report success.
  --record --stem STEM [--card t_xxx] [--title TEXT] ...
      Append or REFRESH that stem's ONE entry, derived from live state: the
      plan JSON, the master at the documented render path, the engine artifact
      store and the sunolocal job store. Keyed on `name`, so re-running cannot
      double-record. Curated fields already in the entry (card, queue_commit,
      queue_entry, render_job, the bpm measurements, quota_consumed …) are
      PRESERVED: the recorder owns only what it measures.
      exit 3  the entry cannot be derived honestly — the marker is not a
              finished render, or the store cannot say which job produced this
              master (more than one candidate: no guess is written).
  --backfill
      The same, for every finished render of a registered genre that has no
      entry. This is the one command the RED check tells the operator to run.
  --selftest
      Prove the red, the green and the idempotence on real files in a scratch
      directory, then prove the live directory is in step when it is present.

Usage:
  python3 music/scripts/check_render_ledger.py --check \\
      --plans /var/lib/music-plans --ledger music/quota-ledger.json
  python3 music/scripts/check_render_ledger.py --backfill
  python3 music/scripts/check_render_ledger.py --record --stem chill-lounge-slow-gold
  python3 music/scripts/check_render_ledger.py --selftest
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import render_state  # noqa: E402  the rail's own marker reader - ONE definition

DEFAULT_PLANS = "/var/lib/music-plans"
DEFAULT_LEDGER = REPO / "music" / "quota-ledger.json"
DEFAULT_GENRES = REPO / "music" / "genres.yaml"
DEFAULT_JOBS_DB = "/var/lib/sunolocal/jobs.sqlite3"
DEFAULT_STORE = "/var/lib/sunolocal/artifacts"
# The same order check_render_landed.py probes, so the two cannot disagree.
EXTENSIONS = ("flac", "wav", "mp3")
RECORDED_BY = "music/scripts/check_render_ledger.py --record (card t_d6b0cb36)"
FFPROBE_CANDIDATES = (
    os.environ.get("FFPROBE", ""),
    "/home/j_kro/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffprobe",
    "/usr/bin/ffprobe",
    "ffprobe",
)

OK, RED, USAGE, REFUSED = 0, 1, 2, 3


class CannotCheck(Exception):
    """The question cannot be answered — never a pass (see `check`)."""


# ── the live state ──────────────────────────────────────────────────────────
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def registered_genres(genres_file: Path) -> set[str]:
    import yaml
    data = yaml.safe_load(genres_file.read_text())
    return set((data.get("genres") or {}).keys())


def find_master(plans: Path, stem: str) -> Path | None:
    """The documented render path (card t_320bae4c): <plans>/<stem>.<ext>."""
    for ext in EXTENSIONS:
        cand = plans / f"{stem}.{ext}"
        if cand.is_file():
            return cand
    return None


def finished_renders(plans: Path) -> list[dict]:
    """Every marker that IS a delivered render, with the rail's own reader."""
    out: list[dict] = []
    for marker in sorted(plans.glob("*.rendered")):
        stem = marker.name[: -len(".rendered")]
        kind, payload = render_state.read_marker(marker)
        st = marker.stat()
        out.append({
            "stem": stem,
            "marker": marker,
            "marker_name": marker.name,
            "kind": kind,
            "payload": payload,
            "mtime": datetime.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(),
            "bytes": st.st_size,
        })
    return out


def ledger_renders(ledger_file: Path) -> list[dict]:
    doc = json.loads(ledger_file.read_text())
    renders = doc.get("renders")
    if not isinstance(renders, list):
        raise ValueError("the ledger has no `renders` list")
    return renders


def plan_facts(plans: Path, stem: str) -> dict:
    plan = plans / f"{stem}.json"
    if not plan.is_file():
        return {"plan_path": None}
    doc = json.loads(plan.read_text())
    meta = doc.get("_meta") or {}
    return {
        "plan_path": str(plan),
        "plan_sha256": sha256_of(plan),
        "genre": meta.get("genre"),
        "title": doc.get("title"),
        "bpm": doc.get("bpm"),
        "key": doc.get("key"),
        "duration": doc.get("duration"),
        "instrumental": doc.get("instrumental"),
    }


# ── the check ───────────────────────────────────────────────────────────────
def check(plans: Path, ledger_file: Path, genres_file: Path) -> list[tuple[str, str]]:
    """[(level, message)] — RED for a delivered render the log does not carry.

    Raises CannotCheck when the question cannot be answered at all. That is
    deliberately NOT an empty list: an absent plans directory returns no
    markers, and a check that reads "no markers" as "in step" would report
    success for a host where the rail does not exist.
    """
    if not plans.is_dir():
        raise CannotCheck(f"{plans} is not a directory - the rail's markers cannot be "
                          f"read, so 'the log is in step' cannot be answered")
    genres = registered_genres(genres_file)
    entries = ledger_renders(ledger_file)
    logged = [e for e in entries if isinstance(e, dict)]
    by_name = {str(e.get("name")): e for e in logged if e.get("name")}
    findings: list[tuple[str, str]] = []

    for rec in finished_renders(plans):
        stem = rec["stem"]
        if rec["kind"] != "finished":
            # Not a delivered render: a refusal is a draft waiting on a human.
            continue
        facts = plan_facts(plans, stem)
        genre = facts.get("genre")
        if facts["plan_path"] is None:
            findings.append(("NOTE", f"{rec['marker_name']}: no {stem}.json - an orphan "
                                     f"marker the rail never reads; not required in the log"))
            continue
        if not genre or genre not in genres:
            findings.append(("NOTE", f"{rec['marker_name']}: genre {genre!r} is not in "
                                     f"{genres_file.name} - not a plan the pipeline wrote "
                                     f"(the planner validates the genre against that "
                                     f"registry), so the log does not carry it"))
            continue
        entry = by_name.get(stem)
        if entry is None:
            findings.append((
                "RED", f"{rec['marker_name']} ({rec['bytes']} B, {genre}, rendered "
                       f"{rec['mtime'][:19]}) has NO entry in {ledger_file.name} - the "
                       f"rail delivered this render and the log does not carry it; run "
                       f"`music/scripts/check_render_ledger.py --record --stem {stem}` "
                       f"(card t_d6b0cb36)"))
            continue
        master = find_master(plans, stem)
        if master is not None:
            want_sha = entry.get("sha256")
            want_bytes = entry.get("bytes")
            got_sha = sha256_of(master)
            got_bytes = master.stat().st_size
            if want_sha and want_sha != got_sha:
                findings.append((
                    "NOTE", f"{entry.get('name')}: the log records sha256 {want_sha[:12]}… "
                            f"but {master.name} is now {got_sha[:12]}… - the render was "
                            f"replaced; re-record it (--record --stem {stem})"))
            elif want_bytes and want_bytes != got_bytes:
                findings.append((
                    "NOTE", f"{entry.get('name')}: the log records {want_bytes} B but "
                            f"{master.name} is {got_bytes} B - re-record it"))
        elif not entry.get("artifact"):
            findings.append((
                "NOTE", f"{entry.get('name')}: the entry records no artifact, and no "
                        f"master is at {plans}/{stem}.<{'|'.join(EXTENSIONS)}> - the "
                        f"render survived only in the engine artifact store, or it is "
                        f"older than that path's contract (card t_320bae4c)"))

    for name, entry in sorted(by_name.items()):
        marker = plans / f"{name}.rendered"
        if not marker.exists():
            findings.append((
                "NOTE", f"{ledger_file.name} records {name!r} but there is no "
                        f"{name}.rendered in {plans} - the log is ahead of the rail's "
                        f"own state for this stem"))
    return findings


# ── the recorder ────────────────────────────────────────────────────────────
def _ffprobe() -> str | None:
    for cand in FFPROBE_CANDIDATES:
        if not cand:
            continue
        if os.path.isabs(cand):
            if os.access(cand, os.X_OK):
                return cand
        elif subprocess.run(["sh", "-c", f"command -v {cand}"],
                            capture_output=True).returncode == 0:
            return cand
    return None


def measure_audio(path: Path) -> dict:
    probe = _ffprobe()
    if probe is None:
        return {}
    r = subprocess.run(
        [probe, "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True)
    if r.returncode != 0:
        return {}
    doc = json.loads(r.stdout or "{}")
    stream = (doc.get("streams") or [{}])[0]
    fmt = doc.get("format") or {}
    out: dict = {}
    try:
        out["duration_s_measured"] = round(float(fmt.get("duration")), 3)
    except (TypeError, ValueError):
        pass
    if stream.get("sample_rate"):
        out["sample_rate_hz"] = int(stream["sample_rate"])
    if stream.get("channels"):
        out["channels"] = int(stream["channels"])
    return out


def load_jobs(jobs_db: Path) -> list[dict]:
    if not jobs_db.is_file():
        return []
    con = sqlite3.connect(f"file:{jobs_db}?mode=ro", uri=True)
    out = []
    for job_id, status, created, updated, request, result in con.execute(
            "select job_id, status, created_at, updated_at, request, result from jobs"):
        try:
            req = json.loads(request)
        except Exception:
            req = {}
        try:
            res = json.loads(result) if result else {}
        except Exception:
            res = {}
        out.append({
            "job_id": job_id, "status": status,
            "created_at": datetime.datetime.fromtimestamp(created).astimezone().isoformat(),
            "updated_at": datetime.datetime.fromtimestamp(updated).astimezone().isoformat(),
            "title": req.get("title"), "duration": req.get("duration"),
            "engine": req.get("engine"), "audio_url": res.get("audio_url"),
        })
    return out


def job_artifact(job: dict, store: Path) -> Path | None:
    """The engine's own copy of this job's audio, when it is still there."""
    url = job.get("audio_url") or ""
    if "path=" in url:
        cand = Path(url.split("path=", 1)[1])
        if cand.is_file():
            return cand
    for p in sorted(store.glob(f"suno-{job['job_id']}.*")):
        if p.is_file():
            return p
    return None


def match_job(jobs: list[dict], facts: dict, master: Path | None,
              store: Path) -> tuple[dict | None, str]:
    """(job, how) — or (None, why not). More than one candidate is NOT a guess."""
    completed = [j for j in jobs if j["status"] == "completed"]
    if master is not None:
        want = sha256_of(master)
        hits = []
        for j in completed:
            art = job_artifact(j, store)
            if art is not None and sha256_of(art) == want:
                hits.append(j)
        if len(hits) == 1:
            return hits[0], (f"byte-identical (sha256 {want[:12]}…) to the master at the "
                             f"documented render path")
        if len(hits) > 1:
            return None, ("more than one engine job produced bytes identical to the "
                          "master: " + ", ".join(h["job_id"][:12] for h in hits))
    title = facts.get("title")
    if title:
        titled = [j for j in completed if j["title"] == title]
        if len(titled) == 1:
            return titled[0], (f"the only completed engine job whose title is {title!r} "
                               f"(the plan's own title)")
        if len(titled) > 1:
            return None, ("more than one completed engine job shares the plan's title "
                          f"{title!r}: " + ", ".join(
                              f"{j['job_id'][:12]} ({j['updated_at'][:19]}, "
                              f"{j['duration']} s)" for j in titled))
    return None, (f"no completed engine job in the store answers to this plan "
                  f"(title {title!r}, duration {facts.get('duration')} s)")


def build_entry(plans: Path, stem: str, store: Path, jobs_db: Path,
                card: str | None, notes_in: list[str] | None = None) -> tuple[dict, list[str], str | None]:
    """(fields, notes, refusal_reason) for one stem, from live state only."""
    notes: list[str] = []
    facts = plan_facts(plans, stem)
    if facts["plan_path"] is None:
        return {}, notes, f"no plan at {plans}/{stem}.json - nothing to derive from"

    marker = plans / f"{stem}.rendered"
    kind, payload = render_state.read_marker(marker)
    if kind != "finished":
        return {}, notes, (f"{marker.name} is not a finished render (state "
                           f"{kind!r}: {payload[:60]!r}) - card t_d6b0cb36: do NOT write "
                           f"an entry for a refused marker")

    fields: dict = {
        "name": stem,
        "genre": facts.get("genre"),
        "plan": facts["plan_path"],
        "plan_sha256": facts["plan_sha256"],
        "marker": marker.name,
        "recorded_by": RECORDED_BY,
    }
    if payload:
        fields["marker_record"] = payload
    if marker.exists():
        fields["rendered_at"] = datetime.datetime.fromtimestamp(
            marker.stat().st_mtime).astimezone().isoformat()
    for key in ("title", "bpm", "key", "duration"):
        if facts.get(key) is not None:
            fields[{"bpm": "bpm_requested", "key": "keyscale_requested"}.get(key, key)] = \
                facts[key]
    if facts.get("instrumental") is not None:
        fields["instrumental"] = bool(facts["instrumental"])
    if card:
        fields["card"] = card

    master = find_master(plans, stem)
    job, how = match_job(load_jobs(jobs_db), facts, master, store)
    if job is None and master is None and "more than one" in how:
        # Ambiguity is the one thing this recorder will not paper over.
        return {}, notes, how
    if job is None:
        if master is None:
            notes.append(f"{stem}: {how} - the entry records the plan and the marker, "
                         f"and no artifact")
        fields["artifact_source"] = how
        if master is not None:
            fields["master"] = str(master)
            fields["sha256"] = sha256_of(master)
            fields["bytes"] = master.stat().st_size
            fields.update(measure_audio(master))
            fields["artifact"] = str(master)
            fields["artifact_source"] = "the master at the documented render path"
    else:
        art = job_artifact(job, store)
        fields["sunolocal_job_id"] = job["job_id"]
        if master is not None:
            fields["master"] = str(master)
        fields["artifact_source"] = how
        if art is not None:
            fields["artifact"] = str(art)
            fields["audio_url"] = f"/api/v1/audio?path={art}"
            fields["sha256"] = sha256_of(art)
            fields["bytes"] = art.stat().st_size
            fields.update(measure_audio(art))
            if master is not None and fields.get("sha256") != sha256_of(master):
                notes.append(f"{stem}: the master at the documented path and the engine "
                             f"artifact differ; the entry records the engine artifact")
        if job.get("engine") and job["engine"] != "ace":
            fields["engine"] = job["engine"]
        elif job.get("engine"):
            fields["engine"] = "ace (local, in-cluster)"
            fields["quota_consumed"] = {"standard_downloads": 0, "studio_exports": 0,
                                        "credits": 0}
        fields["render_started_at"] = job["created_at"]
        fields["render_completed_at"] = job["updated_at"]
        if master is None:
            notes.append(f"{stem}: no master at the documented render path "
                         f"({plans}/{stem}.<{'|'.join(EXTENSIONS)}>) - the engine's own "
                         f"copy recorded above is the surviving one (cards t_320bae4c, "
                         f"t_8c3cd415)")
    if notes or notes_in:
        # Evidence the recorder could not measure, or measured as an absence (why
        # a card is absent, what a marker predates), belongs in the entry.
        fields["notes"] = notes + list(notes_in or [])
    return fields, notes, None


def record(plans: Path, ledger_file: Path, stems: list[str], store: Path,
           jobs_db: Path, card: str | None, dry_run: bool,
           notes_in: list[str] | None = None) -> int:
    doc = json.loads(ledger_file.read_text())
    renders = doc.setdefault("renders", [])
    if not isinstance(renders, list):
        print(f"FAIL check_render_ledger: {ledger_file} has no `renders` list",
              file=sys.stderr)
        return REFUSED
    counters = {k: v for k, v in doc.items() if k != "renders"}

    rc = OK
    changed = 0
    for stem in stems:
        fields, notes, refusal = build_entry(plans, stem, store, jobs_db, card,
                                             notes_in)
        for n in notes:
            print(f"  NOTE {n}")
        if refusal:
            print(f"FAIL check_render_ledger: refusing to record {stem}: {refusal}",
                  file=sys.stderr)
            rc = REFUSED
            continue
        index = next((i for i, e in enumerate(renders)
                      if isinstance(e, dict) and e.get("name") == stem), None)
        if index is None:
            renders.append(fields)
            print(f"  ADD   {stem}: {len(fields)} measured field(s)")
            changed += 1
        else:
            before = json.dumps(renders[index], sort_keys=True)
            for key, value in fields.items():
                renders[index][key] = value
            # Curated keys already present are never removed by a refresh.
            if json.dumps(renders[index], sort_keys=True) == before:
                print(f"  SAME  {stem}: already recorded, nothing to change")
                continue
            print(f"  UPD   {stem}: refreshed the measured fields")
            changed += 1

    if changed and not dry_run:
        # Write through a temp file in the same directory, so a reader never sees
        # a half-written log. `sort_keys` stays False: the ledger's own key order
        # (period, counters, _renders_note, renders) is what a human reads.
        tmp = ledger_file.with_suffix(ledger_file.suffix + ".tmp")
        tmp.write_text(json.dumps(doc, indent=2, sort_keys=False) + "\n")
        tmp.replace(ledger_file)
        after = json.loads(ledger_file.read_text())
        if {k: v for k, v in after.items() if k != "renders"} != counters:
            print("FAIL check_render_ledger: the write changed a quota counter - "
                  "restoring is not automatic, inspect the file", file=sys.stderr)
            return REFUSED
        print(f"  WRITE {ledger_file}: {len(after['renders'])} entry(ies) "
              f"({changed} changed, counters untouched)")
    elif changed:
        print(f"  DRY   {changed} change(s) not written (--dry-run)")
    else:
        print("  NONE  nothing to record")
    return rc


# ── selftest: the red, the green and the idempotence, on real files ─────────
def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def expect(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        plans = root / "plans"
        plans.mkdir()
        store = root / "store"
        store.mkdir()
        jobs_db = root / "jobs.sqlite3"
        con = sqlite3.connect(jobs_db)
        con.execute("create table jobs (job_id text primary key, request text not null,"
                    " status text not null, result text, created_at real not null,"
                    " updated_at real not null)")
        con.commit()
        genres = root / "genres.yaml"
        genres.write_text("genres:\n  chill-lounge:\n    bpm_anchor: 72\n"
                          "  sentimental-piano:\n    bpm_anchor: 72\n")
        ledger = root / "quota-ledger.json"
        ledger.write_text(json.dumps({
            "period": "2026-10", "standard_downloads_used": 0,
            "standard_downloads_limit": 60, "studio_exports": 0, "credits_used": 0,
            "credits_limit": 10000, "warn_at": 55, "hard_stop_at": 58,
            "_renders_note": "the render log", "renders": [],
        }, indent=2) + "\n")

        # THE INCIDENT: a delivered render - 0-byte marker, master at the path -
        # and an empty `renders:` list. This is the whole of card t_d6b0cb36.
        stem = "selftest-delivered"
        plan = plans / f"{stem}.json"
        plan.write_text(json.dumps({"title": "Selftest", "bpm": 72, "key": "C minor",
                                    "duration": 30, "instrumental": True,
                                    "_meta": {"genre": "chill-lounge"}}, indent=2))
        (plans / f"{stem}.rendered").write_text("")
        master = plans / f"{stem}.flac"
        master.write_bytes(b"fLaC" + b"\x00" * 4096)
        art = store / f"suno-{'a' * 32}.flac"
        art.write_bytes(master.read_bytes())

        findings = check(plans, ledger, genres)
        reds = [m for lvl, m in findings if lvl == "RED"]
        expect("a delivered render with no ledger entry is RED (the card's red)",
               len(reds) == 1 and stem in reds[0], str(findings))
        expect("the RED names the command that fixes it",
               "check_render_ledger.py --record --stem" in (reds[0] if reds else ""),
               str(reds))
        expect("the RED cites the card", "t_d6b0cb36" in (reds[0] if reds else ""),
               str(reds))

        # a refusal is NOT a delivered render: no entry required, ever.
        (plans / f"{stem}.refused").write_text("refused " + "0" * 64 + " 2026-10-16T00:00:00Z\n"
                                               "7 section(s) have no lyrics\n")
        (plans / f"{stem}.rendered").unlink()
        findings = check(plans, ledger, genres)
        expect("a refusal needs NO LEDGER ENTRY (the card's own warning)",
               not [m for lvl, m in findings if lvl == "RED"], str(findings))
        (plans / f"{stem}.refused").unlink()

        # the legacy conflation: `refused` written into `.rendered` is not a render
        (plans / f"{stem}.rendered").write_text("refused\n")
        findings = check(plans, ledger, genres)
        expect("a legacy refusal stored in .rendered needs no entry either",
               not [m for lvl, m in findings if lvl == "RED"], str(findings))
        (plans / f"{stem}.rendered").write_text("")

        # a plan the pipeline did not write is not a delivered render
        (plans / "selftest-smoke.json").write_text(json.dumps(
            {"title": "Test Song", "_meta": {"genre": "test"}}))
        (plans / "selftest-smoke.rendered").write_text("")
        findings = check(plans, ledger, genres)
        expect("an unregistered genre is a NOTE, not a RED",
               not [m for lvl, m in findings
                    if lvl == "RED" and "selftest-smoke" in m]
               and any("test" in m for lvl, m in findings if lvl == "NOTE"),
               str(findings))
        (plans / "selftest-smoke.rendered").unlink()
        (plans / "selftest-smoke.json").unlink()

        # the engine job that produced this master IS in the job store
        job_id = "a" * 32
        con.execute("insert into jobs values (?,?,?,?,?,?)",
                    (job_id, json.dumps({"title": "Selftest", "duration": 30,
                                         "engine": "ace"}), "completed",
                     json.dumps({"audio_url": f"/api/v1/audio?path={art}"}),
                     1792180000.0, 1792180123.0))
        con.commit()

        # --record derives the entry from live state and turns the red green
        rc = record(plans, ledger, [stem], store, jobs_db, card="t_selftest", dry_run=False)
        expect("--record exits 0", rc == OK, f"rc={rc}")
        entries = json.loads(ledger.read_text())["renders"]
        expect("--record writes EXACTLY ONE entry", len(entries) == 1, str(entries))
        expect("the entry carries the measured sha256",
               entries and entries[0].get("sha256") == sha256_of(master), str(entries))
        expect("the entry names the engine job the master's bytes identify",
               entries and entries[0].get("sunolocal_job_id") == job_id, str(entries))
        expect("the bytes are attributed to the engine's own copy, not the master",
               entries and entries[0].get("artifact") == str(art), str(entries))
        expect("the entry carries the plan's own facts",
               entries and entries[0].get("genre") == "chill-lounge"
               and entries[0].get("bpm_requested") == 72, str(entries))
        counters = {k: v for k, v in json.loads(ledger.read_text()).items()
                    if k != "renders"}
        expect("--record leaves every quota counter untouched",
               counters.get("standard_downloads_used") == 0
               and counters.get("standard_downloads_limit") == 60,
               str(counters))

        findings = check(plans, ledger, genres)
        expect("the check is GREEN after --record",
               check(plans, ledger, genres) == [], str(findings))

        # IDEMPOTENCE: the card's own condition - re-running must not double-record
        record(plans, ledger, [stem], store, jobs_db, card=None, dry_run=False)
        entries = json.loads(ledger.read_text())["renders"]
        expect("re-running --record does NOT double-record", len(entries) == 1,
               str(entries))
        expect("the refresh preserved the curated card field",
               entries and entries[0].get("card") == "t_selftest", str(entries))
        expect("still green after the second record",
               check(plans, ledger, genres) == [], "")

        # THE final-round SHAPE (the live one): a delivered render whose engine
        # copy is gone. It must still be recordable, and the entry must not
        # invent an artifact it cannot point at.
        gone = "selftest-noenginecopy"
        (plans / f"{gone}.json").write_text(json.dumps(
            {"title": "Gone", "bpm": 72, "duration": 30,
             "_meta": {"genre": "chill-lounge"}}))
        (plans / f"{gone}.rendered").write_text("")
        rc = record(plans, ledger, [gone], store, jobs_db, card=None, dry_run=False)
        entries = json.loads(ledger.read_text())["renders"]
        rec_gone = next((e for e in entries if e.get("name") == gone), None)
        expect("a render with no surviving engine copy is still recordable",
               rc == OK and rec_gone is not None and len(entries) == 2, str(entries))
        expect("...and its entry invents no artifact and no job id",
               bool(rec_gone) and not rec_gone.get("artifact")
               and not rec_gone.get("sunolocal_job_id"), str(rec_gone))
        findings = check(plans, ledger, genres)
        expect("the check flags that thin entry as a NOTE, and nothing is RED",
               not [m for lvl, m in findings if lvl == "RED"]
               and any("records no artifact" in m
                       for lvl, m in findings if lvl == "NOTE"),
               str(findings))

        # drift: the master is replaced under the recorded sha
        master.write_bytes(b"fLaC" + b"\x01" * 4096)
        findings = check(plans, ledger, genres)
        expect("a replaced master is a NOTE, not a silent pass",
               not [m for lvl, m in findings if lvl == "RED"]
               and any("sha256" in m for lvl, m in findings if lvl == "NOTE"),
               str(findings))

        # an entry with no marker left is a NOTE (the log is ahead of the rail)
        (plans / f"{stem}.rendered").unlink()
        findings = check(plans, ledger, genres)
        expect("an entry with no marker is a NOTE",
               any("no " in m and "rendered" in m for lvl, m in findings
                   if lvl == "NOTE"), str(findings))

        # REFUSED, not a pass: a check that cannot check must not report success
        try:
            check(plans, root / "no-such-ledger.json", genres)
            expect("a missing ledger is not a silent pass", False, "no exception")
        except (OSError, ValueError) as exc:
            expect("a missing ledger is not a silent pass", True, exc.__class__.__name__)
        try:
            check(root / "no-such-plans", ledger, genres)
            expect("an ABSENT plans dir is not a silent pass (no markers is not 'in "
                   "step')", False, "no exception")
        except CannotCheck:
            expect("an ABSENT plans dir is not a silent pass (no markers is not 'in "
                   "step')", True, "")

    bad = 0
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  [{detail}]"))
        bad += 0 if ok else 1
    if bad:
        print(f"\n{len(checks) - bad}/{len(checks)} behaviours")
        print(f"BROKEN: {bad} behaviour(s) misbehaved")
        return 1
    print(f"\nOK: {len(checks)} behaviours (a delivered render with no entry is RED, "
          f"a refusal needs no entry, --record derives the entry from live state, and "
          f"re-running it cannot double-record)")
    return 0


# ── cli ─────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(
        description="a delivered render must be in the render log (card t_d6b0cb36)")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--plans", default=DEFAULT_PLANS)
    ap.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    ap.add_argument("--genres", default=str(DEFAULT_GENRES))
    ap.add_argument("--jobs-db", default=DEFAULT_JOBS_DB)
    ap.add_argument("--store", default=DEFAULT_STORE)
    ap.add_argument("--stem", default=None)
    ap.add_argument("--card", default=None,
                    help="the card that queued this render, recorded as provenance")
    ap.add_argument("--note", action="append", default=None,
                    help="evidence the recorder cannot measure, stored in the entry "
                         "(repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    modes = [args.check, args.record, args.backfill, args.selftest]
    if sum(1 for m in modes if m) != 1:
        print("usage: pick exactly one of --check, --record, --backfill, --selftest",
              file=sys.stderr)
        return USAGE

    plans = Path(args.plans)
    ledger_file = Path(args.ledger)

    if args.selftest:
        return selftest()

    if args.check:
        if not ledger_file.is_file():
            print(f"FAIL check_render_ledger: no ledger at {ledger_file}", file=sys.stderr)
            return REFUSED
        try:
            findings = check(plans, ledger_file, Path(args.genres))
        except CannotCheck as exc:
            print(f"FAIL check_render_ledger: cannot check: {exc}", file=sys.stderr)
            return REFUSED
        except OSError as exc:
            print(f"FAIL check_render_ledger: cannot read the live state ({exc})",
                  file=sys.stderr)
            return REFUSED
        except ValueError as exc:
            print(f"FAIL check_render_ledger: {ledger_file} will not parse ({exc})",
                  file=sys.stderr)
            return REFUSED
        reds = [m for lvl, m in findings if lvl == "RED"]
        if args.json:
            print(json.dumps({"plans": str(plans), "ledger": str(ledger_file),
                              "findings": [{"level": l, "detail": m} for l, m in findings],
                              "red": len(reds)}, indent=2))
        else:
            for level, message in findings:
                print(f"  {level} {message}")
        if reds:
            print(f"FAIL check_render_ledger: {len(reds)} delivered render(s) are not in "
                  f"{ledger_file.name} ({len(findings) - len(reds)} note(s))")
            return RED
        print(f"PASS check_render_ledger: every delivered render in {plans} is in "
              f"{ledger_file.name} ({len(findings)} note(s))")
        return OK

    stems = [args.stem] if args.record else None
    if args.record and not args.stem:
        print("usage: --record needs --stem", file=sys.stderr)
        return USAGE
    if args.backfill:
        if not ledger_file.is_file():
            print(f"FAIL check_render_ledger: no ledger at {ledger_file}", file=sys.stderr)
            return REFUSED
        logged = {str(e.get("name")) for e in ledger_renders(ledger_file)}
        genres = registered_genres(Path(args.genres))
        stems = []
        for rec in finished_renders(plans):
            if rec["kind"] != "finished" or rec["stem"] in logged:
                continue
            facts = plan_facts(plans, rec["stem"])
            if not facts.get("genre") or facts["genre"] not in genres:
                print(f"  SKIP  {rec['stem']}: genre {facts.get('genre')!r} is not in "
                      f"{Path(args.genres).name} - not a plan the pipeline wrote")
                continue
            stems.append(rec["stem"])
        print(f"check_render_ledger: backfilling {len(stems)} delivered render(s): "
              f"{', '.join(stems) if stems else '(none)'}")
    return record(plans, ledger_file, stems, Path(args.store), Path(args.jobs_db),
                  args.card, args.dry_run, args.note)


if __name__ == "__main__":
    sys.exit(main())
