#!/usr/bin/env python3
"""check_scheduler_units — the INSTALLED music units must equal the repo copies,
and every path they name must resolve inside a checkout that carries music/.

Why this exists
---------------
Measured 2026-10-16 (card t_41f354be). All four installed units in
`~/.config/systemd/user/` named `/home/j_kro/Projects/ai-content-pipeline/...`,
a SECOND clone of the same origin that has no `music/` tree at all:

    Oct 16 08:00:00 nexus python3[185521]: /usr/bin/python3: can't open file
      '/home/j_kro/Projects/ai-content-pipeline/music/oracle.py': [Errno 2] No such file or directory
    Oct 16 08:00:00 nexus systemd[1895]: music-oracle.service: Failed with result 'exit-code'.

So the daily 08:00 oracle emitted nothing (no oracle card after 2026-10-09), and
`music-pipeline-driver.service` reported "Finished" every 30 min while running the
OTHER checkout's driver, which hardcodes `BOARD=faceless-youtube` and silently
ignores `--board music`.

The path fix (commit b042b79, 2026-10-09) was ALREADY in the repo copies of the
units. Nothing installed it — and, the real defect, nothing in the tree compared the
repo copies against the installed ones. "Already fixed upstream" and "working on the
host" drifted apart for a week with no signal. This is that comparison.

Operational trap, measured this run: `systemd-run --user` on nexus does NOT forward
the caller's environment, so the proof command
`DRY_RUN=1 systemd-run --user ... pipeline-driver.sh --board music` runs the driver
LIVE. Pass the gate explicitly:

    systemd-run --user --wait --pipe --setenv=DRY_RUN=1 -p Environment=HOME=/home/j_kro \
      /bin/bash /home/j_kro/ai-content-pipeline/scripts/automation/pipeline-driver.sh --board music

Rules enforced (FAIL)
---------------------
1. Every `music/scheduler/music-*.{service,timer}` must exist in the install
   directory (`~/.config/systemd/user`) and be byte-identical to the repo copy.
2. Every absolute path named by an installed unit's `ExecStart=` or
   `WorkingDirectory=` must exist. This is the exact oracle failure above.
3. These are `music-*` units for the music lane, so any such path that lands inside
   a git checkout must land inside one that carries `music/oracle.py`. A checkout
   without the music tree is a WRONG CHECKOUT — the root cause here — not a missing
   file, and the fix differs (reinstall from the right clone, not restore a file).

Printed, not enforced: the state of the live-dispatch gate
(`Environment=DRY_RUN=1` on `music-pipeline-driver.service`). t_41f354be section 4 is
an open j_kro decision — this driver (music/stages.yaml routes per stage) versus the
generic kanban dispatcher (every oracle card is assigned `music-producer`) — and
until it is answered the gate must stay. When the decision lands and the line is
deleted, this script reports the new mode instead of failing; arming live dispatch is
a decision, not a regression.

Deliberately NOT checked: whether the timers are enabled or the units are loaded.
That is runtime state (`systemctl --user list-timers 'music-*'`), not file state.

Usage:
  python3 music/scripts/check_scheduler_units.py [--repo DIR] [--install-dir DIR]
  python3 music/scripts/check_scheduler_units.py --selftest

Exit codes: 0 = installed units match and every named path resolves,
1 = at least one divergence, 2 = usage error.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

SRC_REL = "music/scheduler"
PATTERNS = ("music-*.service", "music-*.timer")
MUSIC_MARKER = "music/oracle.py"  # a checkout that carries the music lane
GATE_UNIT = "music-pipeline-driver.service"
GATE_PREFIX = "Environment=DRY_RUN="

# Only treat a token as a path when it starts at a real filesystem root. Without
# this the prose inside the policy-watch prompt ("music/gates/ logs") yields
# fragments like "/gates" and "/weekly/music-YYYY-WW.md" — false positives.
ROOTS = ("/home/", "/usr/", "/bin/", "/sbin/", "/opt/", "/etc/", "/var/",
         "/run/", "/data/", "/srv/", "/mnt/", "/tmp/")
TOKEN_RE = re.compile(r"/[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*")
PATH_LINE_RE = re.compile(r"^(ExecStart|WorkingDirectory)=(.*)$")


def clean(tok: str) -> str:
    return tok.rstrip(".,;:)`'\"\\")


def unit_paths(text: str) -> list[str]:
    """Absolute paths named by ExecStart=/WorkingDirectory= lines of a unit."""
    found: list[str] = []
    for line in text.splitlines():
        m = PATH_LINE_RE.match(line.strip())
        if not m:
            continue
        for tok in TOKEN_RE.findall(m.group(2)):
            tok = clean(tok)
            if tok.endswith("/") or not any(tok.startswith(r) for r in ROOTS):
                continue
            if tok not in found:
                found.append(tok)
    return found


def checkout_root(path: Path) -> Path | None:
    """Nearest ancestor carrying a .git entry, or None."""
    cur = path if path.is_dir() else path.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def run(repo: Path, install_dir: Path) -> tuple[list[str], list[str]]:
    """Return (problems, notes). problems non-empty => exit 1."""
    problems: list[str] = []
    notes: list[str] = []

    src = repo / SRC_REL
    files: list[Path] = []
    for pat in PATTERNS:
        files.extend(sorted(src.glob(pat)))
    if not files:
        return [f"no music units found in {src}"], notes

    for repo_file in files:
        name = repo_file.name
        installed = install_dir / name
        if not installed.exists():
            problems.append(f"{name}: NOT INSTALLED (absent from {install_dir})")
            continue
        if installed.read_bytes() != repo_file.read_bytes():
            problems.append(
                f"{name}: installed copy differs from the repo copy "
                f"({src / name}) — reinstall it"
            )
            continue
        # Only service units name paths; timers do not.
        if not name.endswith(".service"):
            continue
        for p in unit_paths(installed.read_text(errors="replace")):
            path = Path(p)
            if not path.exists():
                problems.append(f"{name}: names {p}, which does not exist")
                continue
            root = checkout_root(path)
            if root is not None and not (root / MUSIC_MARKER).exists():
                problems.append(
                    f"{name}: names {p}, inside the checkout {root}, which has no "
                    f"{MUSIC_MARKER} — that is the wrong checkout for a music unit"
                )

    # Informational: which mode is the live-dispatch gate in?
    gate = install_dir / GATE_UNIT
    gate_text = gate.read_text(errors="replace") if gate.exists() else ""
    line = next((ln.strip() for ln in gate_text.splitlines()
                 if ln.strip().startswith(GATE_PREFIX)), None)
    if line is None:
        notes.append(
            f"{GATE_UNIT}: live-dispatch gate ABSENT — the driver will DISPATCH bots. "
            f"t_41f354be section 4 must be answered before this is intentional."
        )
    else:
        notes.append(f"{GATE_UNIT}: {line} (driver walks in dry-run; section 4 open)")

    return problems, notes


def selftest() -> int:
    """Prove the check fires on each failure class it claims to catch."""
    tmp = Path(tempfile.mkdtemp(prefix="check-scheduler-units."))
    try:
        repo = tmp / "repo"
        install = tmp / "install"
        (repo / SRC_REL).mkdir(parents=True)
        install.mkdir()

        good = tmp / "good-checkout"
        (good / "music").mkdir(parents=True)
        (good / MUSIC_MARKER).write_text("# stub\n")
        (good / ".git").mkdir()

        # Case A: identical copies, path exists in a checkout carrying music/.
        body = (f"[Service]\nExecStart=/bin/echo {MUSIC_MARKER}\n"
                f"WorkingDirectory={repo}\n")
        (repo / SRC_REL / "music-a.service").write_text(body)
        (install / "music-a.service").write_text(body)
        problems, _ = run(repo, install)
        if problems:
            print(f"SELFTEST FAIL case A (clean tree reported {problems})")
            return 1

        # Case B: installed copy diverges from the repo copy.
        (install / "music-a.service").write_text(body + "Nice=10\n")
        problems, _ = run(repo, install)
        if not any("differs from the repo copy" in p for p in problems):
            print(f"SELFTEST FAIL case B (divergence not caught: {problems})")
            return 1
        (install / "music-a.service").write_text(body)

        # Case C: names a path that EXISTS, but inside a checkout without music/.
        # (Case D below covers the missing path; the real incident was both at once.)
        wrong = tmp / "wrong-checkout"
        (wrong / "scripts" / "automation").mkdir(parents=True)
        (wrong / "scripts" / "automation" / "pipeline-driver.sh").write_text("#!/bin/bash\n")
        (wrong / ".git").mkdir()
        (repo / SRC_REL / "music-c.service").write_text(
            f"[Service]\nExecStart=/bin/bash {wrong}/scripts/automation/pipeline-driver.sh\n"
            f"WorkingDirectory={wrong}\n")
        (install / "music-c.service").write_text(
            (repo / SRC_REL / "music-c.service").read_text())
        problems, _ = run(repo, install)
        if not any("wrong checkout" in p for p in problems):
            print(f"SELFTEST FAIL case C (wrong checkout not caught: {problems})")
            return 1
        (repo / SRC_REL / "music-c.service").unlink()
        (install / "music-c.service").unlink()

        # Case D: names a path that does not exist at all.
        (repo / SRC_REL / "music-d.service").write_text(
            "[Service]\nExecStart=/bin/echo /home/j_kro/does-not-exist/x.py\n")
        (install / "music-d.service").write_text(
            (repo / SRC_REL / "music-d.service").read_text())
        problems, _ = run(repo, install)
        if not any("does not exist" in p for p in problems):
            print(f"SELFTEST FAIL case D (missing path not caught: {problems})")
            return 1

        print("PASS --selftest: divergence, wrong-checkout and missing-path all caught")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--install-dir",
                    default=str(Path.home() / ".config/systemd/user"))
    ap.add_argument("--selftest", action="store_true",
                    help="prove the check fires on each failure class")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    repo, install_dir = Path(args.repo).resolve(), Path(args.install_dir).resolve()
    if not (repo / SRC_REL).is_dir():
        print(f"FAIL check_scheduler_units: no {SRC_REL} under {repo}")
        return 2

    problems, notes = run(repo, install_dir)
    if problems:
        print(f"FAIL check_scheduler_units: {len(problems)} problem(s)")
        for p in problems:
            print(f"  {p}")
        print(f"  Fix: install -m 0644 {repo}/{SRC_REL}/music-*.* "
              f"{install_dir}/ && systemctl --user daemon-reload")
        return 1

    n_units = len([f for f in (repo / SRC_REL).glob("music-*")])
    print(f"PASS check_scheduler_units: {n_units} unit file(s) match {install_dir} "
          f"and every path they name resolves")
    for note in notes:
        print(f"  NOTE {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
