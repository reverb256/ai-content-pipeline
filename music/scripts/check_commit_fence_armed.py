#!/usr/bin/env python3
"""check_commit_fence_armed — the shared-tree commit fence must be ARMED, on
both lane repos, and its two copies must be one implementation.

Why this exists
---------------
Measured 2026-10-16 (card t_6d0b7dd7, incident card t_42bc85ba).
`/home/j_kro/ai-content-pipeline` is ONE git working tree that every
concurrently running music card commits to (8 cards were `running` on the music
board at 18:13 CDT). A sibling card had four files STAGED and not yet committed
in that shared index; a card ran

    git add music/sunolocal && git commit -m '...'

and commit 545faa3 carried the sibling's four files. The same hazard cost real
work the same day: commit 5cb2e3d committed from the shared tree while it still
held pre-change copies of card t_450e7f39's three files and reverted that
card's landing 6eb5a23 seven seconds after it landed.

`music/scripts/git_commit_fence.sh` refuses a whole-index commit in a primary
worktree and is installed as `.githooks/pre-commit` with
`git config core.hooksPath .githooks`. A hook is FILE STATE plus one LOCAL
CONFIG key, and neither is versioned with the tree: a fresh clone, a
`git config --unset`, a copied repo or a hook that is not executable silently
disarms it. This check is what makes a disarmed fence visible on the schedule —
the same role `helm/charts/music-pipeline/check-payload-sync.sh` plays for the
planner payload, in the repo whose tree it guards.

Rules enforced (FAIL, exit 1)
-----------------------------
1. `music/scripts/git_commit_fence.sh` (the lane = SOURCE OF RECORD) exists and
   is executable.
2. `core.hooksPath` is `.githooks` in BOTH repos.
3. `.githooks/pre-commit` exists, is executable, and names the fence path it is
   supposed to exec.
4. The mining-k8s copy at `scripts/git_commit_fence.sh` is BYTE-IDENTICAL to the
   lane's (one implementation; a copy that drifts is a second, weaker fence).
5. The fence's own planted-defect suite passes (`music/scripts/
   test_git_commit_fence.sh`, 15 cases) — unless `--skip-selftest` is passed.

Exit codes: 0 = armed on both repos, 1 = at least one divergence,
3 = cannot measure (a repo is absent, or not a git worktree). 3 is reported, never
read as a pass — the same convention as the gate-matrix legs (t_3d84acfe).

Usage:
  /usr/bin/python3 music/scripts/check_commit_fence_armed.py
  /usr/bin/python3 music/scripts/check_commit_fence_armed.py --repo DIR --other-repo DIR2
  /usr/bin/python3 music/scripts/check_commit_fence_armed.py --selftest
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FENCE_REL = "music/scripts/git_commit_fence.sh"      # source of record (lane)
FENCE_MIRROR_REL = "scripts/git_commit_fence.sh"     # mining-k8s copy
SELFTEST_REL = "music/scripts/test_git_commit_fence.sh"
HOOK_REL = ".githooks/pre-commit"
GUARD_REL = "music/scripts/check_stale_write.py"      # source of record (lane)
GUARD_MIRROR_REL = "scripts/check_stale_write.py"     # mining-k8s copy
GUARD_SELFTEST_REL = "music/scripts/test_check_stale_write.py"
HOOKS_PATH = ".githooks"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


def hooks_path(repo: Path) -> str:
    return git(repo, "config", "--local", "--get", "core.hooksPath").stdout.strip()


def fence_problems(lane: Path, other: Path | None, mirror_rel: str,
                   fence_rel: str, skip_selftest: bool) -> list[str]:
    """Every reason the fence is not armed, for one lane repo (+ its copy)."""
    problems: list[str] = []

    fence = lane / fence_rel
    if not fence.exists():
        problems.append(f"MISSING {fence} — the fence is not in the tree")
        return problems
    if not os.access(fence, os.X_OK):
        problems.append(f"NOT-EXECUTABLE {fence} — git runs a hook with exec; chmod +x it")

    hp = hooks_path(lane)
    if hp != HOOKS_PATH:
        problems.append(f"HOOKSPATH {lane}: core.hooksPath={hp or '(unset)'} "
                        f"(want {HOOKS_PATH}) — run: git -C {lane} config core.hooksPath {HOOKS_PATH}")

    hook = lane / HOOK_REL
    if not hook.exists():
        problems.append(f"MISSING {hook} — the hook file is not in the tree")
    else:
        if not os.access(hook, os.X_OK):
            problems.append(f"NOT-EXECUTABLE {hook} — git never runs a non-executable hook")
        if fence_rel not in hook.read_text(encoding="utf-8", errors="replace"):
            problems.append(f"HOOK-DOES-NOT-NAME {hook} never mentions {fence_rel}")

    if other is not None:
        mirror = other / mirror_rel
        if not mirror.exists():
            problems.append(f"MISSING {mirror} — the copy is absent")
        elif sha256(mirror) != sha256(fence):
            problems.append(f"DRIFT {mirror} differs from {fence} "
                            f"({sha256(mirror)[:12]} != {sha256(fence)[:12]}) — "
                            f"one implementation, copied: cp {fence} {mirror}")
        mhp = hooks_path(other)
        if mhp != HOOKS_PATH:
            problems.append(f"HOOKSPATH {other}: core.hooksPath={mhp or '(unset)'} "
                            f"(want {HOOKS_PATH})")
        mhook = other / HOOK_REL
        if not mhook.exists():
            problems.append(f"MISSING {mhook} — the hook file is not in the tree")
        else:
            if not os.access(mhook, os.X_OK):
                problems.append(f"NOT-EXECUTABLE {mhook}")
            if mirror_rel not in mhook.read_text(encoding="utf-8", errors="replace"):
                problems.append(f"HOOK-DOES-NOT-NAME {mhook} never mentions {mirror_rel}")

    if not skip_selftest:
        suite = lane / SELFTEST_REL
        if not suite.exists():
            problems.append(f"MISSING {suite} — the fence has no planted-defect suite")
        else:
            run = subprocess.run(["bash", str(suite)], capture_output=True, text=True)
            if run.returncode != 0:
                tail = (run.stdout or run.stderr).strip().splitlines()[-4:]
                problems.append("SELFTEST the planted-defect suite failed "
                                f"(rc={run.returncode}): " + " | ".join(tail))
    return problems


def content_guard_problems(lane: Path, other: Path | None, mirror_rel: str,
                           guard_rel: str, skip_selftest: bool) -> list[str]:
    """Every reason the content guard is not armed, for one lane repo (+ its copy)."""
    problems: list[str] = []

    guard = lane / guard_rel
    if not guard.exists():
        problems.append(f"MISSING {guard} — the content guard is not in the tree")
        return problems
    if not os.access(guard, os.X_OK):
        problems.append(f"NOT-EXECUTABLE {guard} — git runs a hook with exec; chmod +x it")

    hp = hooks_path(lane)
    if hp != HOOKS_PATH:
        problems.append(f"HOOKSPATH {lane}: core.hooksPath={hp or '(unset)'} "
                        f"(want {HOOKS_PATH}) — run: git -C {lane} config core.hooksPath {HOOKS_PATH}")

    hook = lane / HOOK_REL
    if not hook.exists():
        problems.append(f"MISSING {hook} — the hook file is not in the tree")
    else:
        if not os.access(hook, os.X_OK):
            problems.append(f"NOT-EXECUTABLE {hook} — git never runs a non-executable hook")
        if guard_rel not in hook.read_text(encoding="utf-8", errors="replace"):
            problems.append(f"HOOK-DOES-NOT-NAME {hook} never mentions {guard_rel}")

    if other is not None:
        mirror = other / mirror_rel
        if not mirror.exists():
            problems.append(f"MISSING {mirror} — the copy is absent")
        elif sha256(mirror) != sha256(guard):
            problems.append(f"DRIFT {mirror} differs from {guard} "
                            f"({sha256(mirror)[:12]} != {sha256(guard)[:12]}) — "
                            f"one implementation, copied: cp {guard} {mirror}")
        mhp = hooks_path(other)
        if mhp != HOOKS_PATH:
            problems.append(f"HOOKSPATH {other}: core.hooksPath={mhp or '(unset)'} "
                            f"(want {HOOKS_PATH})")
        mhook = other / HOOK_REL
        if not mhook.exists():
            problems.append(f"MISSING {mhook} — the hook file is not in the tree")
        else:
            if not os.access(mhook, os.X_OK):
                problems.append(f"NOT-EXECUTABLE {mhook}")
            if guard_rel not in mhook.read_text(encoding="utf-8", errors="replace"):
                problems.append(f"HOOK-DOES-NOT-NAME {mhook} never mentions {guard_rel}")

    if not skip_selftest:
        suite = lane / GUARD_SELFTEST_REL
        if not suite.exists():
            problems.append(f"MISSING {suite} — the content guard has no planted-defect suite")
        else:
            run = subprocess.run(["bash", str(suite)], capture_output=True, text=True)
            if run.returncode != 0:
                tail = (run.stdout or run.stderr).strip().splitlines()[-4:]
                problems.append(f"SELFTEST the planted-defect suite failed "
                                f"(rc={run.returncode}): " + " | ".join(tail))
    return problems


def measurable(repo: Path) -> str | None:
    """None when the repo is measurable, else the reason it is not."""
    if not repo.exists():
        return f"{repo} does not exist"
    inside = git(repo, "rev-parse", "--absolute-git-dir")
    if inside.returncode != 0:
        return f"{repo} is not a git worktree ({inside.stderr.strip().splitlines()[-1:]})"
    common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common.returncode != 0 or not (common.stdout.strip()):
        return f"{repo}: git-common-dir is unreadable"
    return None


# --------------------------------------------------------------------------
# selftest: prove this check FIRES on each failure class (a check nobody can
# fail is the state the fence was in before this card)
# --------------------------------------------------------------------------
def selftest() -> int:
    me = Path(__file__).resolve()
    lane = Path(__file__).resolve().parents[2]
    fence_src = lane / FENCE_REL
    hook_src = lane / HOOK_REL
    if not fence_src.exists() or not hook_src.exists():
        print(f"selftest cannot run: {fence_src} / {hook_src} missing")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="fence-armed-selftest."))
    cases: list[tuple[str, int, int, list[str]]] = []

    def build(root: Path, hook_body: str, fence_from: Path | None,
              mirror_from: Path | None) -> tuple[Path, Path]:
        lane_d, other_d = root / "lane", root / "other"
        for d, rel, src in ((lane_d, FENCE_REL, fence_from), (other_d, FENCE_MIRROR_REL, mirror_from)):
            (d / Path(rel).parent).mkdir(parents=True, exist_ok=True)
            (d / HOOK_REL).parent.mkdir(parents=True, exist_ok=True)
            if src is not None:
                shutil.copy(src, d / rel)
                os.chmod(d / rel, 0o755)
            (d / HOOK_REL).write_text(hook_body.format(fence=rel), encoding="utf-8")
            os.chmod(d / HOOK_REL, 0o755)
            subprocess.run(["git", "-C", str(d), "init", "-q", "-b", "main"], check=True)
            subprocess.run(["git", "-C", str(d), "config", "core.hooksPath", HOOKS_PATH], check=True)
            d.joinpath(SELFTEST_REL).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(lane / SELFTEST_REL, lane_d / SELFTEST_REL)
        return lane_d, other_d

    hook_ok = "#!/usr/bin/env bash\nexec \"$(git rev-parse --show-toplevel)/{fence}\"\n"

    def run_case(name: str, want: int, lane_d: Path, other_d: Path) -> None:
        run = subprocess.run([sys.executable, str(me), "--repo", str(lane_d),
                              "--other-repo", str(other_d), "--skip-selftest",
                              "--fence-rel", FENCE_REL, "--mirror-rel", FENCE_MIRROR_REL],
                             capture_output=True, text=True)
        cases.append((name, run.returncode, want, run.stdout.strip().splitlines()[:1]))

    # 0. clean fixture -> PASS
    clean = tmp / "clean"
    lane_d, other_d = build(clean, hook_ok, fence_src, fence_src)
    run_case("clean fixture (fence armed on both)", 0, lane_d, other_d)

    # 1. core.hooksPath unset on the lane -> FAIL
    d = tmp / "no-hookspath"
    lane_d, other_d = build(d, hook_ok, fence_src, fence_src)
    subprocess.run(["git", "-C", str(lane_d), "config", "--unset", "core.hooksPath"], check=True)
    run_case("hooksPath unset", 1, lane_d, other_d)

    # 2. the hook file is not executable -> FAIL
    d = tmp / "hook-not-exec"
    lane_d, other_d = build(d, hook_ok, fence_src, fence_src)
    os.chmod(lane_d / HOOK_REL, 0o644)
    run_case("hook not executable", 1, lane_d, other_d)

    # 3. the hook does not name the fence -> FAIL
    d = tmp / "hook-names-nothing"
    lane_d, other_d = build(d, "#!/usr/bin/env bash\nexit 0\n", fence_src, fence_src)
    run_case("hook never names the fence", 1, lane_d, other_d)

    # 4. the mirror copy has drifted by one byte -> FAIL
    d = tmp / "mirror-drift"
    lane_d, other_d = build(d, hook_ok, fence_src, fence_src)
    mirror = other_d / FENCE_MIRROR_REL
    mirror.write_bytes(mirror.read_bytes() + b"\n# drifted\n")
    run_case("mirror copy drifted", 1, lane_d, other_d)

    # 5. the fence is missing from the tree -> FAIL
    d = tmp / "no-fence"
    lane_d, other_d = build(d, hook_ok, None, fence_src)
    run_case("fence missing from the tree", 1, lane_d, other_d)

    # 6. a repo that is not a git worktree -> cannot measure (3)
    notarepo = tmp / "not-a-repo"
    notarepo.mkdir()
    run_case("repo is not a worktree", 3, notarepo, other_d)

    shutil.rmtree(tmp, ignore_errors=True)

    bad = 0
    for name, got, want, first in cases:
        if got == want:
            print(f"PASS [{name}]: rc={got} as expected")
        else:
            bad += 1
            print(f"BAD  [{name}]: expected rc={want}, got rc={got} ({first})")
    print(f"RESULT: {'pass' if not bad else 'FAIL'} ({len(cases)} cases)")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--other-repo", default="/home/j_kro/mining-k8s")
    ap.add_argument("--fence-rel", default=FENCE_REL)
    ap.add_argument("--mirror-rel", default=FENCE_MIRROR_REL)
    ap.add_argument("--skip-selftest", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    lane = Path(args.repo).expanduser().resolve()
    other = Path(args.other_repo).expanduser().resolve() if args.other_repo else None

    reason = measurable(lane)
    if reason:
        print(f"CANNOT-MEASURE check_commit_fence_armed: {reason}")
        return 3
    if other is not None:
        reason = measurable(other)
        if reason:
            print(f"CANNOT-MEASURE check_commit_fence_armed: {reason} "
                  f"(the fence's copy lives there; pass --other-repo '' to check the lane alone)")
            return 3

    fence_probs = fence_problems(lane, other, args.mirror_rel, args.fence_rel, args.skip_selftest)
    guard_probs = content_guard_problems(lane, other, args.mirror_rel, GUARD_MIRROR_REL, GUARD_REL, args.skip_selftest)
    problems = fence_probs + guard_probs
    if problems:
        print(f"FAIL check_commit_fence_armed: {len(problems)} problem(s) — shared-tree guards NOT armed, "+
              f"so a whole-index commit in the shared tree is allowed again")
        for p in problems:
            print(f"  {p}")
        print("  The fence: music/scripts/git_commit_fence.sh")
        print("  The content guard: music/scripts/check_stale_write.py")
        return 1

    hp = hooks_path(lane)
    print(f"PASS check_commit_fence_armed: guards armed on {lane.name} "+
          f"(core.hooksPath={hp}, hook {HOOK_REL})"+
          + (f" and {other.name} (fence copy {args.mirror_rel} byte-identical, guard copy {GUARD_MIRROR_REL} byte-identical)" if other else ""))
    print(f"  fence: {lane / args.fence_rel}")
    print(f"  guard: {lane / GUARD_REL}")
    print(f"  fence suite: {"skipped (--skip-selftest)" if args.skip_selftest else "planted-defect suite passed"}")
    print(f"  guard suite: {"skipped (--skip-selftest)" if args.skip_selftest else "planted-defect suite passed"}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
