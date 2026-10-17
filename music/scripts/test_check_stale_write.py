#!/usr/bin/env python3
"""test_check_stale_write — planted-defect suite for the shared-tree stale-write
guard (kanban t_8dadd6cb).

Every case builds a throwaway fixture repo that mirrors this repo's layout
(`music/scripts/check_stale_write.py`, `.githooks/pre-commit` and
`.githooks/pre-push`, all COPIED VERBATIM from this repo) and drives real
`git commit` / `git push` calls through the shipped pair. A case asserts the
exit status AND the line the guard printed: an exit code alone cannot say WHICH
decision was taken.

Each case starts from a clean, known state (`git reset --hard <rev>` first), so
a case cannot be decided by the previous case's leftovers. The fence
(`music/scripts/git_commit_fence.sh`) is deliberately NOT copied in: this suite
guards the CONTENT rule, the fence has its own suite
(`music/scripts/test_git_commit_fence.sh`), and leaving the fence out exercises
the hook's documented "no fence here — NOTE and allow" path.

The cases are the defect's decision table. RED marks the control that shows
TODAY'S BEHAVIOUR — the guard bypassed — losing the committed bytes:

   1  a sibling commits section 13, then a stale writer rewrites the file from
      the pre-section-13 bytes: the edeef61 shape                        REFUSE
   1b   ... and the refusal names the origin commit, its card, and the bytes
   1d   ... and a refusal writes nothing: HEAD is still the sibling's commit
   2  RED control: the same stale write with KANBAN_STALE_WRITE=off        ships
   2b   ... and the committed bytes really lost the marker (grep count 1 -> 0)
  13-16 the audit finds the same loss after it landed (--rev / --range / --since)
   4  an override that does NOT name the flagged origin                    REFUSE
   3  the same stale write DECLARED by the origin sha the guard named       ALLOW
   5  a legitimate edit that keeps every committed line                      ALLOW
   6  a card rewording the line IT committed last: the measured false-positive
      class of the provenance rule — refused, and declared to proceed      REFUSE
   6b   ... the same edit declared                                          ALLOW
   7  a named-paths commit does NOT measure a sibling's staged write         ALLOW
   7b   ... and the sibling's staged work is still staged afterwards
   8  content that is EXACTLY an older revision of the path                 REFUSE
   9  a binary path rolled back to an older revision                        REFUSE
  10  a brand-new file                                                       ALLOW
  11  a whole-file rewrite with no line in common (cannot measure)            ALLOW
  12  --staged with nothing staged                                            ALLOW
  17  --rev on a revision that does not exist                                 rc=3
  18  no mode given                                                           rc=2
  19  --push refuses a stale write that bypassed commit-time arming           REFUSE
  19b  ... and origin received nothing (the loss never published)
  20  --push allows a clean branch and origin receives it                     ALLOW
  21  --armed with core.hooksPath `.githooks` and both hooks                 rc=0
  22  --armed with core.hooksPath unset (a disarmed guard)                   rc=3

Usage:  /usr/bin/python3 music/scripts/test_check_stale_write.py [--keep]
Exit 0 = every case behaved; 1 = a case misbehaved; 2 = fixtures unusable.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent      # the lane repo
GUARD = SRC / "music" / "scripts" / "check_stale_write.py"
HOOKS = [SRC / ".githooks" / "pre-commit", SRC / ".githooks" / "pre-push"]

PASS = 0
FAIL = 0
CASES = 0

MARKER = "planner regression suite"          # the bytes edeef61 dropped


def run(cmd, cwd, env=None, stdin=None):
    e = dict(os.environ)
    for k in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
        e.pop(k, None)
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, stdin=stdin)


def git(*args, cwd, env=None, stdin=None):
    return run(["git", *args], cwd, env=env, stdin=stdin)


def case(name, want_rc, needle, res, extra=None):
    """Assert a case's exit status and the line the guard printed."""
    global PASS, FAIL, CASES
    CASES += 1
    got = res.stdout.decode("utf-8", "replace") + res.stderr.decode("utf-8", "replace")
    ok = res.returncode == want_rc and (needle is None or needle in got)
    if ok and extra is not None:
        ok = extra()
    report(name, ok, f"wanted rc={want_rc} and {needle!r}; got rc={res.returncode}", got)


def check(name, ok, detail=""):
    """A post-condition on the fixture, not on the guard's own output."""
    global PASS, FAIL, CASES
    CASES += 1
    report(name, bool(ok), detail, "")


def report(name, ok, detail, got):
    global PASS, FAIL
    print(f"{'PASS' if ok else 'FAIL'} {name}")
    if ok:
        PASS += 1
        return
    FAIL += 1
    if detail:
        print(f"     {detail}")
    for line in got.strip().splitlines()[:12]:
        print(f"     | {line}")


class Fixture:
    """A primary tree with the shipped guard + both hooks, plus a bare origin."""

    seed = ""
    sibling_sha = ""

    def __init__(self, root: Path):
        self.root = root
        self.main = root / "lane"
        self.origin = root / "origin.git"
        self.sibling = root / "sibling-wt"

    def build(self):
        (self.main / "music" / "scripts").mkdir(parents=True)
        (self.main / ".githooks").mkdir(parents=True)
        shutil.copy(GUARD, self.main / "music" / "scripts" / GUARD.name)
        os.chmod(self.main / "music" / "scripts" / GUARD.name, 0o755)
        for h in HOOKS:
            shutil.copy(h, self.main / ".githooks" / h.name)
            os.chmod(self.main / ".githooks" / h.name, 0o755)
        g = lambda *a, **k: git(*a, cwd=self.main, **k)
        g("init", "-q", "-b", "main", ".")
        g("config", "user.email", "stale@test")
        g("config", "user.name", "stale")
        g("config", "core.hooksPath", ".githooks")
        (self.main / "music" / "suite.sh").write_text(
            "#!/usr/bin/env bash\n"
            "# section 1\n"
            'say "one"\n'
            'pass "one" run_one.sh\n'
            "\n"
            "# ---------------------------------------------------------------\n"
            'say "done"\n')
        g("add", "music/suite.sh")
        r = g("commit", "-q", "-m", "seed (t_00000001)")
        if r.returncode != 0:
            raise SystemExit("fixture seed failed: "
                             + r.stderr.decode("utf-8", "replace"))
        self.seed = g("rev-parse", "HEAD").stdout.decode().strip()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)],
                       capture_output=True)
        g("remote", "add", "origin", str(self.origin))
        g("push", "-q", "origin", "main")
        return self

    # --- helpers ------------------------------------------------------------
    def head(self):
        return git("rev-parse", "HEAD", cwd=self.main).stdout.decode().strip()

    def path(self):
        return self.main / "music" / "suite.sh"

    def reset_hard(self, rev="HEAD"):
        git("reset", "-q", "--hard", rev, cwd=self.main)

    def clean(self):
        """A clean start: index and worktree exactly at HEAD."""
        self.reset_hard("HEAD")
        for f in ("music/brand-new.md", "music/clean.md", "music/art.png"):
            p = self.main / f
            if p.exists() and not git("ls-files", "--error-unmatch", f,
                                      cwd=self.main).returncode == 0:
                p.unlink()

    # --- the sibling card: lands section 13 (the 9082ce3 shape) -------------
    def sibling_lands_section_13(self):
        text = self.path().read_text()
        self.path().write_text(text.replace(
            "# ---------------------------------------------------------------\n"
            'say "done"\n',
            "# ---------------------------------------------------------------\n"
            "# section 13 — the planner's own regression suite (card t_00000013)\n"
            "# a rail regression was found only when a card ran it by hand\n"
            'say "' + MARKER + ' (music/tests/test_planner.py)"\n'
            'pass "planner: the duration rail (t_00000013)" run_planner.sh\n'
            "\n"
            "# ---------------------------------------------------------------\n"
            'say "done"\n'))
        r = git("commit", "-q", "-m",
                "music: section 13 wires the planner suite (t_00000013)",
                "--", "music/suite.sh", cwd=self.main)
        if r.returncode != 0:
            raise SystemExit("fixture section-13 commit failed: "
                             + r.stderr.decode("utf-8", "replace"))
        return self.head()

    # --- the stale writer: writes the PRE-section-13 bytes + its own section -
    def stale_write(self, rev="HEAD~1"):
        pre = git("show", f"{rev}:music/suite.sh", cwd=self.main).stdout.decode()
        pre = pre.replace("# section 1\n", "# section 1 (edited by the stale writer)\n")
        pre = pre.replace(
            'say "done"\n',
            "# ---------------------------------------------------------------\n"
            "# section 20 — the writer's own new check (card t_00000020)\n"
            'say "twenty"\n'
            'say "done"\n')
        self.path().write_text(pre)

    def stage(self, *paths):
        git("add", *(paths or ("music/suite.sh",)), cwd=self.main)

    def commit(self, msg, env=None, pathspec=None):
        cmd = ["commit", "-q", "-m", msg]
        if pathspec:
            cmd += ["--", *pathspec]
        return git(*cmd, cwd=self.main, env=env)

    def marker_count(self, rev="HEAD"):
        out = git("show", f"{rev}:music/suite.sh", cwd=self.main).stdout.decode()
        return out.count(MARKER)

    def guard(self, *args, env=None, stdin=None, cwd=None):
        return run([sys.executable, str(self.main / "music" / "scripts" / GUARD.name),
                    *args], cwd or self.main, env=env, stdin=stdin)

    def named_origin(self):
        """The origin sha the guard names for the current staged set."""
        out = self.guard("--staged").stderr.decode("utf-8", "replace")
        for part in out.split("introduced by:")[1:2]:
            return part.split()[0].strip()
        return ""


def main():
    keep = "--keep" in sys.argv
    root = Path(tempfile.mkdtemp(prefix="stale-write-test.",
                                 dir=os.environ.get("TMPDIR")))
    try:
        # ================= A: the incident, guarded =========================
        fx = Fixture(root / "a").build()
        fx.sibling_sha = fx.sibling_lands_section_13()
        fx.stale_write()
        fx.stage()
        res = fx.commit("music: my own new check (t_00000020)")
        case("1   a stale rewrite of a file a sibling just changed", 1,
             "drops content that landed in the branch later", res)
        case("1b  the refusal names the origin commit and its card", 1,
             "t_00000013", res)
        case("1c  the refusal names the dropped bytes", 1, MARKER, res)
        check("1d  a refusal writes nothing: HEAD is still the sibling's commit",
              fx.head() == fx.sibling_sha, f"HEAD={fx.head()[:8]} sibling={fx.sibling_sha[:8]}")

        # control: a refusal must not disturb a sibling's staged work
        fx.stage()
        case("1e  the refusal still leaves the staged bytes staged", 1,
             "drops content that landed in the branch later", fx.commit(
                 "music: retry after the refusal (t_00000020)"))
        check("1f  after a refusal the bytes are still staged",
              "music/suite.sh" in git("diff", "--cached", "--name-only", cwd=fx.main)
              .stdout.decode(), "the index lost the staged path")

        # ================= B: RED control — today's behaviour ===============
        before = fx.marker_count()
        res = fx.commit("music: my own new check (t_00000020)",
                        env={"KANBAN_STALE_WRITE": "off"})
        case("2   RED control: guard bypassed, the stale write SHIPS", 0,
             "ALLOW", res, extra=lambda: fx.marker_count() == 0)
        case("2b  RED control: the committed bytes really lost the marker", 0,
             None, res, extra=lambda: before == 1 and fx.marker_count() == 0)
        landed_stale = fx.head()

        # ================= C: the audit finds what shipped ==================
        res = fx.guard("--rev", landed_stale)
        case("13  audit --rev on the commit that lost the bytes", 1,
             "t_00000013", res)
        res = fx.guard("--rev", "HEAD^")
        case("14  audit --rev on the clean commit before it", 0, "PASS", res)
        res = fx.guard("--range", f"{fx.seed}..HEAD")
        case("15  audit --range over both", 1, "drops content that landed", res)
        res = fx.guard("--since", fx.seed)
        case("16  audit --since over the same range", 1, "drops content that landed", res)

        # a commit that DECLARES the bytes it drops is reported, not refused
        audit = fx.guard("--rev", "HEAD")
        origins = ""
        for part in audit.stderr.decode("utf-8", "replace").split("introduced by:")[1:2]:
            origins = part.split()[0].strip()
        check("16a the audit names an origin to declare", bool(origins), "no origin named")
        git("commit", "-q", "--amend", "-m",
            f"music: section 20, re-landed (t_00000020)\n\n"
            f"Stale-write-dropped: {origins}", cwd=fx.main)
        res = fx.guard("--rev", "HEAD")
        case("16b a commit that declares the origin bytes it drops", 0,
             "declared", res, extra=lambda: not fx.guard("--rev", "HEAD").returncode)
        res = fx.guard("--since", fx.seed)
        case("16c the same declaration clears the whole audit", 0, "PASS", res)
        git("commit", "-q", "--amend", "-m",
            "music: my own new check (t_00000020)", cwd=fx.main)
        res = fx.guard("--rev", "HEAD")
        case("16d removing the trailer brings the refusal back", 1,
             "drops content that landed", res)

        # ================= D: the declaration escape ========================
        fx.reset_hard("HEAD^")                      # back to the sibling's commit
        fx.stale_write()
        fx.stage()
        res = fx.commit("music: my own new check (t_00000020)",
                        env={"KANBAN_STALE_WRITE": "deadbeef"})
        case("4   an override that does NOT name the flagged origin", 1,
             "does not name the origin commit", res)
        named = fx.named_origin()
        res = fx.commit("music: my own new check, declared (t_00000020)",
                        env={"KANBAN_STALE_WRITE": named})
        case("3   the same stale write DECLARED by the origin sha", 0,
             "ALLOW", res, extra=lambda: fx.marker_count() == 0)

        # ================= E: legitimate work is not blocked ================
        fx2 = Fixture(root / "b").build()
        fx2.sibling_lands_section_13()
        text = fx2.path().read_text()
        fx2.path().write_text(text.replace('say "done"\n',
                                           'say "twenty-one"\nsay "done"\n'))
        fx2.stage()
        res = fx2.commit("music: a new section appended (t_00000021)")
        case("5   a legitimate edit that keeps every committed line", 0, "PASS", res)

        # the measured false-positive class: rewording the line you just committed
        fx2.clean()
        text = fx2.path().read_text()
        fx2.path().write_text(text.replace('say "twenty-one"',
                                           'say "twenty-one (renamed)"'))
        fx2.stage()
        res = fx2.commit("music: rewording my own line (t_00000021)")
        case("6   rewording the line this card committed last (FP class)", 1,
             "drops content that landed in the branch later", res)
        fx2.stage()
        declared = fx2.named_origin()
        res = fx2.commit("music: rewording my own line, declared (t_00000021)",
                         env={"KANBAN_STALE_WRITE": declared})
        case("6b  the same edit declared", 0, "ALLOW", res)

        # ================= F: a named-paths commit measures only its paths ===
        fx2.clean()
        # the sibling's work is STAGED AND UNCOMMITTED in the shared index
        (fx2.main / "music" / "sibling.txt").write_text("sibling v1\n")
        fx2.stage("music/sibling.txt")
        fx2.commit("music: sibling file lands (t_00000030)", pathspec=["music/sibling.txt"])
        (fx2.main / "music" / "sibling.txt").write_text("sibling v2\n")
        fx2.stage("music/sibling.txt")                  # staged, not committed
        text = fx2.path().read_text()
        fx2.path().write_text(text.replace('say "done"\n',
                                           'say "twenty-two"\nsay "done"\n'))
        fx2.stage("music/suite.sh")
        res = fx2.commit("music: only my path (t_00000031)",
                         pathspec=["music/suite.sh"])
        case("7   a named-paths commit does not measure a sibling's staged write", 0,
             "PASS", res)
        case("7b  the sibling's staged work is still staged afterwards", 0, None, res,
             extra=lambda: "music/sibling.txt" in
             git("diff", "--cached", "--name-only", cwd=fx2.main)
             .stdout.decode())

        # ================= G: exact rollbacks, text and binary ==============
        fx2.clean()
        prev = git("show", "HEAD~1:music/suite.sh", cwd=fx2.main).stdout
        fx2.path().write_bytes(prev)
        fx2.stage()
        res = fx2.commit("music: restore the old suite (t_00000022)")
        case("8   content that is EXACTLY an older revision of the path", 1,
             "is EXACTLY revision", res)
        fx2.clean()

        png = b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 8
        (fx2.main / "music" / "art.png").write_bytes(png)
        fx2.stage("music/art.png")
        fx2.commit("music: art v1 (t_00000023)", pathspec=["music/art.png"])
        (fx2.main / "music" / "art.png").write_bytes(png + b"tag")
        fx2.stage("music/art.png")
        fx2.commit("music: art v2 (t_00000023)", pathspec=["music/art.png"])
        (fx2.main / "music" / "art.png").write_bytes(png)
        fx2.stage("music/art.png")
        res = fx2.commit("music: art back to v1 (t_00000023)",
                         pathspec=["music/art.png"])
        case("9   a binary path rolled back to an older revision", 1,
             "is EXACTLY revision", res)

        # ================= H: the allow paths ===============================
        fx2.clean()
        (fx2.main / "music" / "brand-new.md").write_text("hello\n")
        fx2.stage("music/brand-new.md")
        res = fx2.commit("music: a new file (t_00000024)",
                         pathspec=["music/brand-new.md"])
        case("10  a brand-new file", 0, "PASS", res)

        fx2.clean()
        fx2.path().write_text("completely different\nlines\nhere\n")
        fx2.stage()
        res = fx2.commit("music: regenerate the suite (t_00000024)")
        case("11  a whole-file rewrite with no line in common", 0, "NOTE", res)

        fx2.clean()
        res = fx2.guard("--staged")
        case("12  --staged with nothing staged", 0, "no staged paths", res)

        # ================= I: cannot measure / usage ========================
        res = fx2.guard("--rev", "no-such-rev")
        case("17  --rev on a revision that does not exist", 3, None, res)
        res = fx2.guard()
        case("18  no mode given", 2, None, res)

        # ================= J: the publish boundary ==========================
        fx3 = Fixture(root / "c").build()
        fx3.sibling_lands_section_13()
        fx3.stale_write()
        fx3.stage()
        fx3.commit("music: bypassed at commit time (t_00000025)",
                   env={"KANBAN_STALE_WRITE": "off"})
        published = git("rev-parse", "origin/main", cwd=fx3.main).stdout.decode().strip()
        res = git("push", "-q", "origin", "main", cwd=fx3.main)
        case("19  --push refuses a stale write that bypassed commit-time arming", 1,
             "REFUSED this push", res)
        check("19b the refusal published nothing",
              git("rev-parse", "origin/main", cwd=fx3.main)
              .stdout.decode().strip() == published, "origin/main moved")

        # a clean branch publishes through the same hook (a fresh fixture, so the
        # stale commit above is not in the range: that is the state after a card
        # fixes its own commit)
        fx4 = Fixture(root / "d").build()
        fx4.sibling_lands_section_13()
        (fx4.main / "music" / "clean.md").write_text("clean\n")
        fx4.stage("music/clean.md")
        fx4.commit("music: a clean commit (t_00000026)", pathspec=["music/clean.md"])
        before_push = git("rev-parse", "origin/main", cwd=fx4.main).stdout.decode().strip()
        res = git("push", "-q", "origin", "main", cwd=fx4.main)
        case("20  --push allows a clean branch and origin receives it", 0, None, res)
        check("20b origin/main advanced",
              git("rev-parse", "origin/main", cwd=fx4.main)
              .stdout.decode().strip() != before_push, "origin/main did not move")
        check("20c the published bytes carry the sibling's section 13",
              git("show", "origin/main:music/suite.sh", cwd=fx4.main)
              .stdout.decode().count(MARKER) == 1, "the marker is not on origin/main")

        # git calls pre-push with an EMPTY ref list for an update it already
        # rejects (measured 2026-10-17 on a non-fast-forward push). Nothing to
        # judge must not block a push, and a guard that cannot measure must not
        # either: both fail OPEN here, because the daily leg is the detector.
        res = fx4.guard("--push", stdin=subprocess.DEVNULL)
        case("20d --push with an empty ref list (nothing to judge)", 0,
             "no ref lines on stdin", res)
        res = run([str(fx4.main / ".githooks" / "pre-push")], fx4.main,
                  stdin=subprocess.DEVNULL)
        case("20e the hook does not block a push it cannot see", 0,
             "no commit to judge", res)

        # ================= K: is the guard ARMED? ===========================
        res = fx3.guard("--armed", "--skip-selftest")
        case("21  --armed with core.hooksPath set and both hooks", 0, "ARMED", res)
        git("config", "--unset", "core.hooksPath", cwd=fx3.main)
        res = fx3.guard("--armed", "--skip-selftest")
        case("22  --armed with core.hooksPath unset (a disarmed guard)", 3,
             "DISARMED", res)

        print()
        print(f"RESULT: {'PASS' if FAIL == 0 else 'FAIL'} ({PASS}/{CASES} cases behaved)")
        if FAIL:
            print(f"        {FAIL} case(s) misbehaved")
        return 0 if FAIL == 0 else 1
    finally:
        if keep:
            print(f"fixture kept at {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
