#!/usr/bin/env python3
"""check_fleet_route_probe_scheduled — SOMETHING must run the fleet routing probe
on a schedule, and its last run must be recent.

Why this exists
---------------
Measured 2026-10-16 (card t_7d75bafd). `scripts/fleet-route.py probe` — a live
1-call probe of every model in every profile primary and fallback chain — already
existed, and:

    $ ls ~/.hermes/state/fleet-route/
    ls: cannot access '/home/j_kro/.hermes/state/fleet-route/': No such file or directory

nothing ran it. The same day, 29 of 32 profiles had a primary that answers
HTTP 400 MissingSessionID, 14 chains named a provider with no credential at all,
and 5 profiles had no fallback — and no signal anywhere said so. This script is
the assertion that the probe has a home, the way
`music/scripts/check_gate_matrix_scheduled.py` asserts it for the gate matrix
(card t_b16b9046) and `check_scheduler_units.py` asserts repo/installed parity for
the music units (card t_41f354be). An unrun check is inert: that is the incident
this whole family of checks exists for (t_049c6a26, t_41f354be).

Rules enforced (FAIL)
---------------------
1. `scripts/scheduler/fleet-route-probe.{service,timer}` exist in the repo and are
   byte-identical to the installed copies in ~/.config/systemd/user.
2. The service's `ExecStart=` names a runner that exists.
3. If that path lands inside a git checkout, the checkout must carry
   `scripts/fleet-route.py`. A checkout without it is the WRONG CHECKOUT — the
   exact root cause of t_41f354be, where all four music units ran a second clone
   that had no music/ tree, and the daily oracle emitted nothing for a week.
4. The timer fires at least daily and is `Persistent=true` (a missed tick after
   downtime must still run).
5. The timer is `enabled` and `active` in the user manager. The music check
   deliberately does not test enablement ("runtime state, not file state") — this
   one must, because "the unit exists but is disabled" IS the incident here: the
   user-scope `fleet-verify.timer` was disabled/inactive/NTriggers=0 while four
   cards wired their regression checks into it (t_049c6a26). Use `--offline` in a
   sandbox or a container where no user manager is reachable.
6. The last status file exists and is fresh (default: 7 hours — the timer ticks
   every 3). Its `rc` is printed as a NOTE, not enforced: a red probe is already
   signalled three ways (the unit's own failed state, the fleet alert feed, and
   the status JSON), and this check guards the EXISTENCE of the schedule, not the
   health of the fleet. `--allow-missing-status` skips rule 6 for the runner's own
   first write.

Usage:
  python3 scripts/check_fleet_route_probe_scheduled.py [--repo DIR]
      [--install-dir DIR] [--status FILE] [--max-age-hours N]
      [--offline] [--allow-missing-status] [--selftest]

Exit codes: 0 = wired, enabled and fresh; 1 = at least one problem; 2 = usage
error (no repo, no scheduler dir).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_REPO = "/home/j_kro/ai-content-pipeline"
SRC_REL = "scripts/scheduler"
UNITS = ("fleet-route-probe.service", "fleet-route-probe.timer")
RUNNER_REL = "scripts/fleet-route-probe.sh"
ROUTER_REL = "scripts/fleet-route.py"
STATUS_REL = "performance/fleet-route-probe.status.json"
TIMER_NAME = "fleet-route-probe.timer"


def unit_paths(text: str) -> list[str]:
    """Absolute paths named by ExecStart=/WorkingDirectory= lines of a unit."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("ExecStart=", "ExecStartPre=", "WorkingDirectory=")):
            _, _, value = line.partition("=")
            for token in value.split():
                if token.startswith("/") and not token.startswith("/bin/") \
                        and not token.startswith("/usr/"):
                    out.append(token.split(":")[0])
            if value.startswith("/"):
                out.append(value.split()[0].split(":")[0])
    return out


def systemctl_user(verb: str, unit: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["systemctl", "--user", verb, unit],
                           capture_output=True, text=True, timeout=15)
        return r.returncode, (r.stdout or r.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 127, f"systemctl unavailable: {type(exc).__name__}"


WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def oncalendar_hours(spec: str) -> float | None:
    """Hours between ticks for a systemd OnCalendar= spec, or None if unparsable.

    Handles the two shapes that matter: an hour list on every day
    (`*-*-* 00,03,…,21:40:00` -> 3 h) and a weekday-restricted event
    (`Mon *-*-* 06:00:00` -> 168 h). A weekday prefix is why a naive hour-count
    would read a weekly run as daily.
    """
    s = spec.strip()
    base = 24.0
    m = re.match(r"^([A-Za-z]{3}(?:-[A-Za-z]{3})?(?:,[A-Za-z]{3}(?:-[A-Za-z]{3})?)*)\s+", s)
    if m and m.group(1).lower()[:3] in WEEKDAYS:
        days: set[int] = set()
        for part in m.group(1).split(","):
            if "-" in part:
                a, b = (x.lower()[:3] for x in part.split("-"))
                i, j = WEEKDAYS.index(a), WEEKDAYS.index(b)
                days.update(range(i, j + 1) if i <= j
                            else list(range(i, 7)) + list(range(0, j + 1)))
            else:
                days.add(WEEKDAYS.index(part.lower()[:3]))
        base = 168.0 / (len(days) or 1)

    mh = re.search(r"(\d+(?:,\d+)*):", s)
    if not mh:
        return None
    hours = [int(h) for h in mh.group(1).split(",")]
    return base / max(len(hours), 1)


def run(repo: Path, install_dir: Path, status: Path, max_age_h: float,
        offline: bool, allow_missing_status: bool):
    problems: list[str] = []
    notes: list[str] = []
    src = repo / SRC_REL
    if not src.is_dir():
        return None, [f"no {SRC_REL} under {repo}"]

    for name in UNITS:
        repo_unit = src / name
        if not repo_unit.is_file():
            problems.append(f"{SRC_REL}/{name} is missing from {repo}")
            continue
        installed = install_dir / name
        if not installed.is_file():
            problems.append(f"{installed} is not installed "
                            f"(install -m 0644 {repo_unit} {install_dir}/ && "
                            f"systemctl --user daemon-reload)")
            continue
        if installed.read_bytes() != repo_unit.read_bytes():
            problems.append(f"{installed} differs from {repo_unit} — the installed "
                            f"copy is what runs; reinstall it")
            continue
        notes.append(f"{name}: repo and installed copies are byte-identical")

    svc = src / UNITS[0]
    if svc.is_file():
        text = svc.read_text(errors="replace")
        named = unit_paths(text)
        if not any(p.endswith(RUNNER_REL) for p in named):
            problems.append(f"{UNITS[0]} does not name {RUNNER_REL} in "
                            f"ExecStart= (names {named or 'nothing'})")
        for p in named:
            path = Path(p)
            if not path.exists():
                problems.append(f"{UNITS[0]} names {p}, which does not exist")
                continue
            root = _git_root(path if path.is_dir() else path.parent)
            if root is not None and not (root / ROUTER_REL).exists():
                problems.append(f"{UNITS[0]} names {p}, which is inside the checkout "
                                f"{root} — that checkout has no {ROUTER_REL}, so it "
                                f"is the WRONG CHECKOUT for this unit")

    tmr = src / UNITS[1]
    if tmr.is_file():
        text = tmr.read_text(errors="replace")
        m = re.search(r"(?m)^OnCalendar=(.+)$", text)
        if not m:
            problems.append(f"{UNITS[1]} has no OnCalendar= line")
        else:
            hours = oncalendar_hours(m.group(1).strip())
            if hours is None:
                problems.append(f"{UNITS[1]} OnCalendar={m.group(1).strip()} could "
                                f"not be parsed to an interval")
            elif hours > 24:
                problems.append(f"{UNITS[1]} fires every {hours:.0f} h — the fleet "
                                f"must be probed at least daily")
            else:
                notes.append(f"{UNITS[1]}: OnCalendar={m.group(1).strip()} "
                             f"(~{hours:.1f} h apart)")
        if not re.search(r"(?m)^Persistent=true$", text):
            problems.append(f"{UNITS[1]} is not Persistent=true — a tick missed "
                            f"during downtime must still run")

    if not offline:
        rc, out = systemctl_user("is-enabled", TIMER_NAME)
        if rc != 0 or "enabled" not in out:
            problems.append(f"{TIMER_NAME} is not enabled (systemctl --user "
                            f"is-enabled -> rc={rc} '{out}'); a unit that exists but "
                            f"is disabled is the t_049c6a26 incident")
        else:
            notes.append(f"{TIMER_NAME}: {out}")
        rc, out = systemctl_user("is-active", TIMER_NAME)
        if rc != 0 or out != "active":
            problems.append(f"{TIMER_NAME} is not active (systemctl --user is-active "
                            f"-> rc={rc} '{out}')")
        else:
            notes.append(f"{TIMER_NAME}: active")
    else:
        notes.append("--offline: enablement and freshness of the live timer not checked")

    if allow_missing_status:
        notes.append("--allow-missing-status: the status file was not required "
                     "(the runner is writing it now)")
    elif not status.is_file():
        problems.append(f"no status file at {status} — the schedule is installed but "
                        f"has never run")
    else:
        age_h = (time.time() - status.stat().st_mtime) / 3600
        if age_h > max_age_h:
            problems.append(f"{status} is {age_h:.1f} h old (limit {max_age_h} h) — "
                            f"the timer is stopped, disabled, or the unit dies before "
                            f"it writes")
        else:
            notes.append(f"{status}: {age_h:.1f} h old (limit {max_age_h} h)")
        try:
            st = json.loads(status.read_text())
            notes.append(f"last run rc={st.get('rc')} state={st.get('state')} "
                         f"audit_flagged={st.get('audit_flagged')} "
                         f"probe_fail={st.get('probe_fail')} (reported, not enforced)")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{status} is not valid JSON: {type(exc).__name__}: {exc}")

    return problems, notes


def _git_root(path: Path) -> Path | None:
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent
    return None


def selftest() -> int:
    """Prove the check fires on each failure class, and passes on a good tree."""
    fails = 0

    def say(ok: bool, msg: str) -> None:
        nonlocal fails
        print(f"  {'PASS' if ok else 'FAIL'}: {msg}")
        if not ok:
            fails += 1

    tmp = Path(tempfile.mkdtemp(prefix="check-fleet-route-probe."))
    try:
        def fire(*a, **kw) -> list:
            pr, _ = run(*a, **kw)
            return pr or []

        repo = tmp / "repo"
        install = tmp / "install"
        (repo / SRC_REL).mkdir(parents=True, exist_ok=True)
        (repo / "scripts").mkdir(parents=True, exist_ok=True)
        install.mkdir(parents=True)
        (repo / ROUTER_REL).write_text("# fleet-route.py placeholder\n")
        (repo / RUNNER_REL).write_text("#!/bin/bash\necho probe\n")
        good_status = repo / STATUS_REL
        good_status.parent.mkdir(parents=True, exist_ok=True)
        good_status.write_text(json.dumps({"rc": 0, "state": "ok", "audit_flagged": 0}))

        def write_units(exec_path: str = str(repo / RUNNER_REL),
                        oncalendar: str = "*-*-* 00,03,06,09,12,15,18,21:40:00",
                        persistent: bool = True) -> None:
            body_svc = (f"[Unit]\nDescription=x\n\n[Service]\nType=oneshot\n"
                        f"ExecStart=/bin/bash {exec_path}\n"
                        f"WorkingDirectory={repo}\n")
            body_tmr = (f"[Unit]\nDescription=x\n\n[Timer]\nOnCalendar={oncalendar}\n"
                        f"{'Persistent=true' if persistent else 'Persistent=false'}\n")
            (repo / SRC_REL / UNITS[0]).write_text(body_svc)
            (repo / SRC_REL / UNITS[1]).write_text(body_tmr)
            (install / UNITS[0]).write_text(body_svc)
            (install / UNITS[1]).write_text(body_tmr)

        write_units()
        problems = fire(repo, install, good_status, 7, True, False)
        say(not problems, f"a good tree passes (problems: {problems})")

        # 1. installed copy drifts from the repo copy
        (install / UNITS[1]).write_text("drift\n")
        problems = fire(repo, install, good_status, 7, True, False)
        say(any("differs from" in p for p in problems), "installed/repo drift fires")
        write_units()

        # 2. the unit names the WRONG CHECKOUT (a clone without fleet-route.py)
        other = tmp / "other-clone"
        (other / "scripts").mkdir(parents=True, exist_ok=True)
        (other / ".git").mkdir(exist_ok=True)
        (other / RUNNER_REL).write_text("#!/bin/bash\necho probe\n")
        write_units(exec_path=str(other / RUNNER_REL))
        problems = fire(repo, install, good_status, 7, True, False)
        say(any("WRONG CHECKOUT" in p for p in problems),
            "a runner inside a checkout without fleet-route.py fires")
        write_units()

        # 3. a weekly timer is too slow
        write_units(oncalendar="Mon *-*-* 06:00:00")
        problems = fire(repo, install, good_status, 7, True, False)
        say(any("at least daily" in p for p in problems), "a non-daily timer fires")
        write_units()

        # 4. not persistent
        write_units(persistent=False)
        problems = fire(repo, install, good_status, 7, True, False)
        say(any("Persistent" in p for p in problems), "Persistent=false fires")
        write_units()

        # 5. a stale status file
        old = time.time() - 40000
        import os
        os.utime(good_status, (old, old))
        problems = fire(repo, install, good_status, 7, True, False)
        say(any("old (limit" in p for p in problems), "a stale status file fires")
        os.utime(good_status, None)

        # 6. no status at all
        good_status.unlink()
        problems = fire(repo, install, good_status, 7, True, False)
        say(any("has never run" in p for p in problems), "a missing status file fires")
        problems = fire(repo, install, good_status, 7, True, True)
        say(not problems, "--allow-missing-status tolerates the runner's first write")

        # 7. an unparsable OnCalendar
        write_units(oncalendar="daily")
        problems = fire(repo, install, good_status, 7, True, True)
        say(any("could not be parsed" in p for p in problems),
            "an unparsable OnCalendar fires")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nselftest: {'OK' if fails == 0 else f'{fails} failure(s)'}")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--install-dir", default=str(Path.home() / ".config/systemd/user"))
    ap.add_argument("--status", default=None)
    ap.add_argument("--max-age-hours", type=float, default=7.0)
    ap.add_argument("--offline", action="store_true",
                    help="skip the live systemd enablement check (sandboxes, containers)")
    ap.add_argument("--allow-missing-status", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    status = Path(args.status) if args.status else repo / STATUS_REL
    problems, notes = run(repo, Path(args.install_dir).expanduser(), status,
                          args.max_age_hours, args.offline, args.allow_missing_status)
    if problems is None:
        print(f"FAIL check_fleet_route_probe_scheduled: {notes[0]}")
        return 2
    for n in notes:
        print(f"  NOTE {n}")
    if problems:
        print(f"FAIL check_fleet_route_probe_scheduled: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PASS check_fleet_route_probe_scheduled: the fleet routing probe is "
          "installed, enabled, at least daily, and its last run is recent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
