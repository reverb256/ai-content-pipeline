#!/usr/bin/env python3
"""Two runs of the gate suite never share one fixture directory.

Run: python3 music/tests/test_gate_scratch_ownership.py
     GATE_SCRATCH_SLOW=1 python3 music/tests/test_gate_scratch_ownership.py

REGRESSION (2026-10-16, card t_075cb010; incident measured during t_69cab80b).
`bash music/gates/check_gate_suite.sh` took its fixture directory from the fixed
default `/tmp/music-gate-fixtures`, and the suite REBUILDS every fixture under
that directory as it runs. Two overlapping runs therefore read each other's
half-written trees, and the suite reported a healthy gate as broken:

    BAD   generator-built pack passes (pack mode) (expected exit 0, got 1)
            FAIL gate_sync_ready
              - no manifest.json
              - no loop_points.json ...
    BROKEN: 2 check(s) misbehaved

while that directory was fully populated a moment later, and the same suite was
green with a private directory. A false BROKEN is worse than no check: the gate
matrix posts its failure to the alert feed and files a board card, so two
workers debug a phantom gate failure.

The suite now (a) gives itself a PRIVATE directory per run when GATE_SCRATCH is
not set, and (b) takes an exclusive lock on an explicit GATE_SCRATCH and refuses
(rc 2, never a check failure) when another LIVE run owns it, or when the tree is
not one this run built.

These checks DRIVE THE SUITE ITSELF - it is the artifact that misreported - so
they need no fixture and no ffmpeg. Each inner run is stopped as soon as it has
announced its fixture directory (or has refused), which is before any check
runs, so a nested run can never re-enter this test. The slow case runs the whole
suite; it stays out of the matrix (`GATE_SUITE_RUN` is set by the suite) and
beats on the LEGACY shared path only, never on a live run's directory. It
asserts the incident's signature (a pack case reporting a false BAD) and, when
the tree is otherwise green, the whole verdict - a tree that is red for an
unrelated reason is reported, not relabelled.
"""

import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
SUITE = REPO / "music" / "gates" / "check_gate_suite.sh"
LEGACY = pathlib.Path("/tmp/music-gate-fixtures")   # the pre-fix default
BASH = shutil.which("bash") or "/bin/bash"

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def proc_start_ticks(pid: int) -> str:
    """Field 22 of /proc/<pid>/stat (boot-relative start time)."""
    try:
        line = pathlib.Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return ""
    rest = line.split(") ", 1)[-1].split()
    return rest[19] if len(rest) > 19 else ""


class SuiteRun:
    """One `bash check_gate_suite.sh` run, read line by line by a thread."""

    def __init__(self, env_extra: dict | None = None, tmpdir: pathlib.Path | None = None):
        env = os.environ.copy()
        for key in ("GATE_SCRATCH", "GATE_SCRATCH_LOCK_TOKEN", "GATE_SCRATCH_KEEP", "PY"):
            env.pop(key, None)
        if tmpdir is not None:
            env["TMPDIR"] = str(tmpdir)
        if env_extra:
            env.update(env_extra)
        self.proc = subprocess.Popen(
            [BASH, str(SUITE)], cwd=str(REPO), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, start_new_session=True)
        self.lines: list[str] = []
        self.found = threading.Event()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.rstrip("\n")
            self.lines.append(line)
            if line.startswith("scratch: "):
                self.found.set()

    def text(self) -> str:
        return "\n".join(self.lines)

    def wait_started(self, timeout: float = 60.0) -> bool:
        """True when the run announced its fixture directory (or False on exit)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.found.wait(0.2):
                return True
            if self.proc.poll() is not None:
                break
        self.reader.join(timeout=5)
        return self.found.is_set()

    def wait_exit(self, timeout: float = 60.0) -> int:
        try:
            rc = self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.stop()
            return -999
        self.reader.join(timeout=5)
        return rc

    def scratch_dir(self) -> str:
        for line in self.lines:
            if line.startswith("scratch: "):
                return line.split("scratch: ", 1)[1].split(" ", 1)[0]
        return ""

    def stop(self, sig: int = signal.SIGTERM, timeout: float = 20.0) -> int:
        if self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), sig)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                self.proc.wait(timeout=10)
        self.reader.join(timeout=5)
        return self.proc.returncode


def write_lock(dirpath: pathlib.Path, pid: int, start_ticks: str) -> pathlib.Path:
    lock = pathlib.Path(str(dirpath) + ".owner.d")
    lock.mkdir(parents=True, exist_ok=True)
    (lock / "pid").write_text(f"{pid}\n")
    (lock / "start_ticks").write_text(f"{start_ticks}\n")
    (lock / "started").write_text("2026-10-16T00:00:00-05:00\n")
    (lock / "host").write_text("nexus\n")
    (lock / "dir").write_text(f"{dirpath}\n")
    return lock


def no_check_verdict(run: SuiteRun) -> bool:
    t = run.text()
    return not any(line.startswith("BAD ") or line.startswith("BROKEN") or line.startswith("FATAL")
                   for line in t.splitlines())


def wait_gone(path: pathlib.Path, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not path.exists():
            return True
        time.sleep(0.1)
    return not path.exists()


def main() -> int:
    if not SUITE.is_file():
        print(f"FATAL: no gate suite at {SUITE}")
        return 2
    probe = pathlib.Path(tempfile.mkdtemp(prefix="_tgs-"))
    print(f"probe TMPDIR: {probe}")
    try:
        # ------------------------------------------------------------------
        print()
        print("1. with no GATE_SCRATCH, two CONCURRENT runs get two private directories")
        # The incident needs two runs at once: start the second only once the
        # first has announced its directory and is still alive.
        a = SuiteRun(tmpdir=probe)
        started_a = a.wait_started()
        check("the first run announces the fixture directory it will use", started_a,
              f"rc={a.proc.returncode} lines={a.lines[-3:]}")
        path_a = pathlib.Path(a.scratch_dir())
        check("...and the directory exists", path_a.is_dir(), repr(str(path_a)))
        check("...and it is NOT the fixed shared path of the incident",
              path_a != LEGACY, repr(str(path_a)))
        check("...and it lives under TMPDIR (this run's own, unique name)",
              path_a.parent == probe and path_a.name.startswith("music-gate-fixtures."),
              repr(str(path_a)))

        b = SuiteRun(tmpdir=probe)
        started_b = b.wait_started()
        path_b = pathlib.Path(b.scratch_dir())
        check("a second concurrent run announces its own directory", started_b,
              f"rc={b.proc.returncode} lines={b.lines[-3:]}")
        check("the two runs do NOT share a fixture directory",
              path_a and path_b and path_a != path_b, f"{path_a} vs {path_b}")
        check("...and both directories hold fixtures at the same time (the runs overlap)",
              a.proc.poll() is None and b.proc.poll() is None and path_a.is_dir() and path_b.is_dir(),
              f"a_alive={a.proc.poll() is None} b_alive={b.proc.poll() is None}")

        rc_a = a.stop()
        rc_b = b.stop()
        check("a private directory is removed when its run ends",
              wait_gone(path_a) and wait_gone(path_b),
              f"rc_a={rc_a} rc_b={rc_b} a={path_a.exists()} b={path_b.exists()}")

        # ------------------------------------------------------------------
        print()
        print("2. an explicit GATE_SCRATCH: the second run REFUSES, and never reports a check")
        shared = probe / "shared-fixtures"
        shared.mkdir()
        holder = SuiteRun(env_extra={"GATE_SCRATCH": str(shared)})
        check("the first run on an explicit GATE_SCRATCH announces it", holder.wait_started(),
              f"rc={holder.proc.returncode} lines={holder.lines[-3:]}")
        check("...and says the explicit directory is kept",
              "explicit GATE_SCRATCH, kept" in holder.text(),
              holder.lines[-1] if holder.lines else "")
        check("...and takes the exclusive lock beside it (not inside it)",
              pathlib.Path(str(shared) + ".owner.d").is_dir()
              and not (shared / ".gate-suite-owner").exists(), "lock missing")

        second = SuiteRun(env_extra={"GATE_SCRATCH": str(shared)})
        rc2 = second.wait_exit(timeout=60)
        check("a second run on the same directory exits with rc 2 (refused, not broken)",
              rc2 == 2, f"rc={rc2}")
        check("...and names the live owner and this card",
              "REFUSED: another run of the gate suite owns" in second.text()
              and "t_075cb010" in second.text(), second.text()[-400:])
        check("...and reports NO misbehaving check (no BAD / BROKEN / FATAL)",
              no_check_verdict(second), second.text()[-400:])
        check("...and leaves the first run's directory untouched",
              shared.is_dir() and holder.proc.poll() is None,
              f"dir={shared.is_dir()} holder_rc={holder.proc.returncode}")

        holder.stop()
        check("the holder's lock is released when its run ends",
              wait_gone(pathlib.Path(str(shared) + ".owner.d")), "lock still there")
        check("...and the explicit (durable) directory is KEPT", shared.is_dir(), repr(str(shared)))

        # ------------------------------------------------------------------
        print()
        print("3. a lock left by a DEAD run does not block the next one (empty tree)")
        stale = probe / "stale-fixtures"
        stale.mkdir()
        dead = subprocess.Popen(["/bin/sh", "-c", "exit 0"])
        dead.wait()
        write_lock(stale, dead.pid, "")
        third = SuiteRun(env_extra={"GATE_SCRATCH": str(stale)})
        check("a dead holder's lock is taken over, not honoured", third.wait_started(),
              f"rc={third.proc.returncode} lines={third.lines[-3:]}")
        check("...and the takeover is announced", "took over the stale lock" in third.text(),
              third.text()[-300:])
        third.stop()

        # ------------------------------------------------------------------
        print()
        print("4. a RECYCLED pid is not accepted as a live holder")
        # The lock names THIS process (alive) but not this process's start time:
        # pid recycling. A holder is live only when pid AND start time match.
        recycled = probe / "recycled-fixtures"
        recycled.mkdir()
        write_lock(recycled, os.getpid(), "0")
        fourth = SuiteRun(env_extra={"GATE_SCRATCH": str(recycled)})
        check("a lock naming a live pid with a DIFFERENT start time is stale",
              fourth.wait_started() and "took over the stale lock" in fourth.text(),
              f"rc={fourth.proc.returncode} lines={fourth.lines[-3:]}")
        fourth.stop()

        live = probe / "live-fixtures"
        live.mkdir()
        write_lock(live, os.getpid(), proc_start_ticks(os.getpid()))
        fifth = SuiteRun(env_extra={"GATE_SCRATCH": str(live)})
        rc5 = fifth.wait_exit(timeout=60)
        check("a lock naming a live pid with the SAME start time is refused",
              rc5 == 2 and "REFUSED: another run of the gate suite owns" in fifth.text(),
              f"rc={rc5} {fifth.text()[-300:]}")
        check("...and that refusal reports no misbehaving check",
              no_check_verdict(fifth), fifth.text()[-300:])

        # ------------------------------------------------------------------
        print()
        print("5. a tree no live run owns is refused (its files are another run's)")
        leftover = probe / "leftover-fixtures"
        (leftover / "pack").mkdir(parents=True)
        (leftover / "pack" / "manifest.json").write_text("{}\n")
        sixth = SuiteRun(env_extra={"GATE_SCRATCH": str(leftover)})
        rc6 = sixth.wait_exit(timeout=60)
        check("a non-empty unowned GATE_SCRATCH exits rc 2", rc6 == 2, f"rc={rc6}")
        check("...naming the tree and the fix",
              "already holds entries and no live run owns it" in sixth.text(),
              sixth.text()[-400:])
        check("...and reports no misbehaving check", no_check_verdict(sixth), sixth.text()[-400:])
        check("...and does not touch the files it refused to use",
              (leftover / "pack" / "manifest.json").is_file(), "file gone")

        # ------------------------------------------------------------------
        if os.environ.get("GATE_SCRATCH_SLOW") == "1" and not os.environ.get("GATE_SUITE_RUN"):
            print()
            print("6. SLOW: a full run stays green while a foreign writer beats the LEGACY path")
            # The pre-fix default path, beaten on by a foreign writer: this is
            # the incident. The run must not read it, so its verdict stands.
            stop_writing = threading.Event()
            wrote = [0]

            def foreign_writer() -> None:
                while not stop_writing.is_set():
                    for name in ("manifest.json", "loop_points.json"):
                        target = LEGACY / "pack" / name
                        try:
                            target.unlink()
                        except OSError:
                            pass
                        try:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text("{}\n")
                            wrote[0] += 1
                        except OSError:
                            pass
                    time.sleep(0.05)

            writer = threading.Thread(target=foreign_writer, daemon=True)
            writer.start()
            full = SuiteRun(tmpdir=probe)
            rc_full = full.wait_exit(timeout=900)
            stop_writing.set()
            writer.join(timeout=5)
            declared = pathlib.Path(full.scratch_dir())
            check("the full run used its OWN directory, not the legacy shared path",
                  declared.name.startswith("music-gate-fixtures.") and declared != LEGACY
                  and declared.parent == probe, str(declared))
            pack_bads = [line for line in full.text().splitlines()
                         if line.startswith("BAD ") and "pack" in line]
            check("...and no pack case reported a false BAD while that path was destroyed",
                  not pack_bads, str(pack_bads))
            if rc_full == 0:
                check("...and the whole suite is green (rc 0, no BAD/BROKEN)",
                      no_check_verdict(full), full.text()[-600:])
            else:
                # A tree that is red for a reason this card does not own must not
                # make this check lie in either direction: report the verdict and
                # the failures, so the reader can see which defect is which.
                print(f"  note: the run is rc={rc_full} on this tree; failures are not"
                      f" this card's unless they name the pack cases above")
                print(f"        verdict: {full.lines[-1] if full.lines else '(none)'}")
                for line in full.text().splitlines():
                    if line.startswith("BAD "):
                        print(f"        {line}")
            check("...and its private directory is removed at exit",
                  not declared.exists(), str(declared))
            check("the foreign writer really did write (the driver is not a no-op)",
                  wrote[0] > 0, str(wrote[0]))
        else:
            print()
            print("6. SLOW case skipped (set GATE_SCRATCH_SLOW=1 to run the whole suite)")
    finally:
        shutil.rmtree(probe, ignore_errors=True)

    print()
    if fails:
        print(f"FAILED: {len(fails)} check(s)")
        for name in fails:
            print(f"  - {name}")
        return 1
    print("OK: the gate suite never shares a fixture directory with another run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
