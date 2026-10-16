#!/usr/bin/env python3
"""check_gate_matrix_scheduled — SOMETHING must run the music gate acceptance
matrix on a schedule, with an interpreter that can `import yaml`, and its last
run must be recent.

Why this exists
---------------
Measured 2026-10-16 (card t_b16b9046). `music/gates/check_gate_suite.sh` is the
acceptance matrix for all 10 music gates, and two documents told operators to
run it by hand:

    music/gates/README.md:34            bash music/gates/check_gate_suite.sh
    brain/runbooks/music-game-assets.md  "Run the full gate matrix"

Nothing ran it:

    $ ls .github/workflows            -> No such file or directory
    $ grep -rn check_gate_suite scripts/ performance/   -> no hits
    $ ls scripts/automation/          -> advance-stage, oracle-run, pipeline-driver,
                                         scout-run, spoc-standup, weekly-review

and the music units ran the pipeline and the render, never the gates. So a
regression in the gate library surfaced only when a human happened to run the
suite — which is how the PyYAML false-BAD was found (t_d3b9e218): the suite
called bare `python3`, a worker shell resolved the Hermes bundled interpreter
(no PyYAML), and two HEALTHY gates were reported BROKEN.

The suite's own interpreter resolution stops the false BAD, but it does not stop
"nobody runs it". This script is that missing assertion. It fails when:

1. no scheduler entry (a music-* systemd unit, or an /etc/cron.d entry) runs the
   matrix — the exact state measured above;
2. the entry names a runner that does not exist;
3. the runner does not pin a yaml-capable interpreter — the t_d3b9e218 trap is
   that the environment, not the gate, decides which python3 runs;
4. the last run's status file is missing (the schedule was installed but has
   never run) or stale (the timer is disabled/stopped, or the unit dies before
   it writes — i.e. the schedule silently stopped, which is the same incident
   one layer down).

The last run's rc is printed as a NOTE, deliberately not enforced: a red matrix
is already signalled three ways — the unit's own failed state
(`systemctl --user status music-gate-matrix.service`), the fleet alert feed, and
the failure card the runner files on the music board. This check guards the
existence of the schedule, not the health of the gates.

Usage:
  python3 music/scripts/check_gate_matrix_scheduled.py [--repo DIR]
                                 [--install-dir DIR] [--status FILE]
                                 [--max-age-hours N]
  python3 music/scripts/check_gate_matrix_scheduled.py --selftest

Exit codes: 0 = wired, fresh, interpreter pinned, 1 = at least one problem,
2 = usage error.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RUNNER_REL = "music/scripts/run_gate_matrix.sh"
SUITE_REL = "music/gates/check_gate_suite.sh"
STATUS_REL = "performance/music-gate-matrix.status.json"
DEFAULT_MAX_AGE_HOURS = 48.0  # 2x the daily cadence of music-gate-matrix.timer

# A scheduler entry counts as wiring when it runs the runner, or runs the suite
# itself while pinning an interpreter. `PY=` covers the pinned-interpreter form.
ENTRY_RUNNER = "run_gate_matrix.sh"
ENTRY_SUITE = "check_gate_suite.sh"
ENTRY_PY_PIN = re.compile(r"(^|\s)PY=/usr/\S*python3")
PY_DEFAULT_RE = re.compile(r'^PY="?\$\{PY:-([^}"]+)\}"?.*$', re.M)


def scheduler_entries(install_dir: Path, include_system: bool = True) -> list[tuple[str, str]]:
    """(label, text) for every place a schedule could run the matrix.

    `include_system=False` keeps the selftest hermetic: a real /etc/cron.d entry
    on the host must not make the "no scheduler entry" case pass.
    """
    entries: list[tuple[str, str]] = []
    for pat in ("*.service", "*.timer"):
        for f in sorted(install_dir.glob(pat)):
            try:
                entries.append((str(f), f.read_text(errors="replace")))
            except OSError:
                continue
    if not include_system:
        return entries
    for f in sorted(Path("/etc/cron.d").glob("*")) if Path("/etc/cron.d").is_dir() else []:
        try:
            entries.append((str(f), f.read_text(errors="replace")))
        except OSError:
            continue
    for f in (Path("/etc/crontab"), Path("/var/spool/cron/j_kro"),
              Path("/var/spool/cron/crontabs/j_kro")):
        try:
            entries.append((str(f), f.read_text(errors="replace")))
        except OSError:
            continue
    return entries


def interpreter_ok(interp: str) -> bool:
    """True when `interp` can import yaml (the t_d3b9e218 requirement)."""
    try:
        return subprocess.run([interp, "-c", "import yaml"], capture_output=True,
                              timeout=20).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def active_text(text: str) -> str:
    """Drop comment lines.

    A unit's header comments NAME the paths it runs ("runs
    music/scripts/run_gate_matrix.sh daily"), so matching paths across the whole
    file resolves relative mentions like `/scripts/run_gate_matrix.sh` and
    reports a path that does not exist — a false FAIL measured 2026-10-16 on the
    first live run of this check.
    """
    return "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith("#"))


def wiring(install_dir: Path, repo: Path,
           include_system: bool = True) -> tuple[list[str], list[str], int]:
    """Return (problems, notes, n_entries)."""
    problems: list[str] = []
    notes: list[str] = []
    entries = scheduler_entries(install_dir, include_system=include_system)
    hits: list[tuple[str, str]] = []
    for label, text in entries:
        text = active_text(text)
        names_runner = ENTRY_RUNNER in text
        names_suite = ENTRY_SUITE in text
        if not (names_runner or names_suite):
            continue
        # A unit that runs the runner is wiring. A bare cron line that calls the
        # suite itself is wiring only when it pins an interpreter.
        if names_runner or ENTRY_PY_PIN.search(text):
            hits.append((label, text))

    if not hits:
        problems.append(
            f"nothing runs {SUITE_REL} — no scheduler entry under {install_dir} "
            f"(or /etc/cron.d) names {ENTRY_RUNNER}, or names {ENTRY_SUITE} while "
            f"pinning a python3. That is the incident this check exists for "
            f"(card t_b16b9046): the matrix is documented in two places and "
            f"executed by nothing."
        )
        return problems, notes, 0

    for label, text in hits:
        notes.append(f"schedule: {label}")
        # Rule 2/3: a named runner must exist and pin a yaml-capable interpreter.
        for m in re.finditer(r"(/[A-Za-z0-9_./+-]*%s)" % re.escape(ENTRY_RUNNER), text):
            runner = Path(m.group(1))
            if not runner.exists():
                problems.append(f"{label} names {runner}, which does not exist")
                continue
            body = active_text(runner.read_text(errors="replace"))
            dm = PY_DEFAULT_RE.search(body)
            if not dm:
                problems.append(
                    f"{runner} does not pin an interpreter (no `PY=\"${{PY:-<interp>}}\"` "
                    f"default). The t_d3b9e218 trap is that `python3` resolves to the "
                    f"Hermes bundled interpreter, which has no PyYAML, so a healthy "
                    f"gate is reported BAD."
                )
                continue
            interp = dm.group(1)
            if not interpreter_ok(interp):
                problems.append(
                    f"{runner} defaults to {interp}, which cannot `import yaml` — "
                    f"gate_lyrics_original would report a false BAD (t_d3b9e218)"
                )
            else:
                notes.append(f"interpreter pinned: {interp} (imports yaml)")
        # A bare cron line may call the suite directly; then the pin must be there.
        for m in re.finditer(r"(/[A-Za-z0-9_./+-]*%s)" % re.escape(ENTRY_SUITE), text):
            suite = Path(m.group(1))
            if not suite.exists():
                problems.append(f"{label} names {suite}, which does not exist")
    return problems, notes, len(hits)


def freshness(status: Path, max_age_hours: float) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    notes: list[str] = []
    if not status.exists():
        problems.append(
            f"{status} does not exist — the schedule has never produced a run "
            f"(installed but never started, or the unit dies before reporting)"
        )
        return problems, notes
    age_h = (time.time() - status.stat().st_mtime) / 3600.0
    if age_h > max_age_hours:
        problems.append(
            f"{status} is {age_h:.1f} h old (> {max_age_hours:.0f} h = 2x the daily "
            f"cadence) — the timer is disabled/stopped or the unit fails early"
        )
    else:
        notes.append(f"last status {age_h:.1f} h old")
    try:
        import json

        st = json.loads(status.read_text())
        notes.append(
            "last run rc=%s state=%s (log: %s)"
            % (st.get("rc"), st.get("state"), st.get("log_file"))
        )
        if st.get("rc") not in (0, None):
            notes.append(
                "NOTE: the last scheduled matrix run was RED — that signal lives in "
                "the unit state, the fleet alert feed and the music-board card, not here"
            )
    except Exception as exc:  # unreadable JSON is a wiring problem, not a gate problem
        problems.append(f"{status} is not readable JSON: {exc}")
    return problems, notes


def run(repo: Path, install_dir: Path, status: Path, max_age_hours: float,
        include_system: bool = True) -> int:
    problems: list[str] = []
    notes: list[str] = []
    runner = repo / RUNNER_REL
    suite = repo / SUITE_REL
    if not runner.exists():
        problems.append(f"{runner} does not exist")
    if not suite.exists():
        problems.append(f"{suite} does not exist")

    p, n, count = wiring(install_dir, repo, include_system=include_system)
    problems += p
    notes += n
    p, n = freshness(status, max_age_hours)
    problems += p
    notes += n

    if problems:
        print(f"FAIL check_gate_matrix_scheduled: {len(problems)} problem(s)")
        for prob in problems:
            print(f"  - {prob}")
    else:
        print(f"PASS check_gate_matrix_scheduled: {count} scheduler entr"
              f"{'y runs' if count == 1 else 'ies run'} {RUNNER_REL} with a "
              f"yaml-capable interpreter")
    for note in notes:
        print(f"  NOTE {note}")
    return 1 if problems else 0


def selftest() -> int:
    """Prove each failure class fires. A check nobody can fail is decoration."""
    tmp = Path(tempfile.mkdtemp(prefix="check-gate-matrix."))
    try:
        repo = tmp / "repo"
        install = tmp / "install"
        (repo / "music/scripts").mkdir(parents=True)
        (repo / "music/gates").mkdir(parents=True)
        (repo / "performance").mkdir(parents=True)
        install.mkdir()
        (repo / SUITE_REL).write_text("#!/bin/bash\nexit 0\n")
        runner = repo / RUNNER_REL
        runner.write_text('#!/usr/bin/env bash\nPY="${PY:-/usr/bin/python3}"\nexit 0\n')
        unit = install / "music-gate-matrix.service"
        # The comment names the runner RELATIVELY, exactly like the real unit's
        # header does: matching inside comments resolved `/scripts/run_gate_matrix.sh`
        # and produced a false FAIL on the first live run (2026-10-16).
        unit.write_text(
            "# runs music/scripts/run_gate_matrix.sh daily at 06:20\n"
            "[Service]\nExecStart=/bin/bash %s\n" % runner
        )
        status = repo / STATUS_REL
        status.write_text('{"rc": 0, "state": "OK", "log_file": "x"}\n')

        rc = run(repo, install, status, DEFAULT_MAX_AGE_HOURS, include_system=False)
        if rc != 0:
            print("SELFTEST FAIL case A (clean wiring reported problems)")
            return 1

        # Case B: no scheduler entry at all — the incident state.
        unit.unlink()
        if run(repo, install, status, DEFAULT_MAX_AGE_HOURS, include_system=False) == 0:
            print("SELFTEST FAIL case B (no scheduler entry not caught)")
            return 1
        unit.write_text("[Service]\nExecStart=/bin/bash %s\n" % runner)

        # Case C: entry names a runner that does not exist.
        runner.unlink()
        if run(repo, install, status, DEFAULT_MAX_AGE_HOURS, include_system=False) == 0:
            print("SELFTEST FAIL case C (missing runner not caught)")
            return 1
        runner.write_text('#!/usr/bin/env bash\nPY="${PY:-/usr/bin/python3}"\nexit 0\n')

        # Case D: runner does not pin an interpreter (the t_d3b9e218 trap).
        runner.write_text("#!/usr/bin/env bash\npython3 music/gates/check_gate_suite.sh\n")
        if run(repo, install, status, DEFAULT_MAX_AGE_HOURS, include_system=False) == 0:
            print("SELFTEST FAIL case D (unpinned interpreter not caught)")
            return 1
        runner.write_text('#!/usr/bin/env bash\nPY="${PY:-/usr/bin/python3}"\nexit 0\n')

        # Case E: status file missing — installed but never ran.
        status.unlink()
        if run(repo, install, status, DEFAULT_MAX_AGE_HOURS, include_system=False) == 0:
            print("SELFTEST FAIL case E (missing status not caught)")
            return 1

        # Case F: status stale — the schedule silently stopped.
        status.write_text('{"rc": 0, "state": "OK", "log_file": "x"}\n')
        old = time.time() - 5 * 86400
        import os

        os.utime(status, (old, old))
        if run(repo, install, status, DEFAULT_MAX_AGE_HOURS, include_system=False) == 0:
            print("SELFTEST FAIL case F (stale status not caught)")
            return 1

        print("SELFTEST OK: all 5 failure classes fire (B unwired, C missing runner, "
              "D unpinned interpreter, E never ran, F stale) while a healthy entry "
              "with a comment naming the runner relatively stays PASS (A)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(
        description="The music gate acceptance matrix must be scheduled, "
                    "interpreter-pinned, and fresh (card t_b16b9046).")
    ap.add_argument("--repo", default=str(here.parent.parent.parent))
    ap.add_argument("--install-dir", default=str(Path.home() / ".config/systemd/user"))
    ap.add_argument("--status", default=None)
    ap.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    install = Path(args.install_dir).expanduser()
    if not install.is_dir():
        print(f"FAIL check_gate_matrix_scheduled: no install dir {install}")
        return 1
    status = Path(args.status).expanduser() if args.status else repo / STATUS_REL
    return run(repo, install, status, args.max_age_hours)


if __name__ == "__main__":
    sys.exit(main())
