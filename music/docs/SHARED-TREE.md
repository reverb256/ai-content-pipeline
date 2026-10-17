# One working tree, many cards — where the fence is

Decision record for kanban **t_6d0b7dd7** (2026-10-16). Measured on nexus; every
number below came from a command in that run.

## The defect, measured

`/home/j_kro/ai-content-pipeline` is ONE git working tree that every concurrently
running card commits to. At 18:13 CDT, 8 cards were `running` on the music board
and every one of them committed into this tree (`hermes-worker-kanban-*` scopes
on nexus; `sqlite3 -readonly …/music/kanban.db "select status,count(*) …"` →
`running|8`).

Two measured incidents, same mechanism:

| commit | what happened |
|---|---|
| `545faa3` (card t_42bc85ba) | a sibling card had four files STAGED and not yet committed in the shared index; `git add music/sunolocal && git commit` carried them (`music/briefs/commentary-beds.md`, `music/gates/check_gate_suite.sh`, `music/planner/planner.py`, `music/tests/test_planner.py`). Caught by reading the stat; reset and re-made. |
| `5cb2e3d` (card t_7a528617) | committed from this shared tree while it still held pre-change copies of card t_450e7f39's three files, and **reverted that card's landing `6eb5a23` seven seconds after it landed**. Not caught; it cost work. |

The mechanism is not "a careless agent". It is that a commit using the SHARED
index commits everything staged in it — whatever card staged it — and
`git commit -a` stages every tracked edit in the tree first. What prevented it in
t_42bc85ba was a pathspec (`git commit -m M -- music/sunolocal`), i.e. a habit,
not a fence.

## The decision

**The fence is the index, per commit, in the shared tree.** Not one card at a
time (the lane is deliberately parallel: 8 workers), not worktree-only (worktrees
remain the tool for a card that needs one, but requiring them would leave the
common path — edit, `git add`, `git commit` — unprotected).

`music/scripts/git_commit_fence.sh`, armed as `.githooks/pre-commit`
(`git config core.hooksPath .githooks`), reads two facts git already knows and
nothing else:

* **primary ?** `git rev-parse --absolute-git-dir` ==
  `git rev-parse --path-format=absolute --git-common-dir` — a linked worktree has
  its own git dir, so its index is private and it is never blocked;
* **which index ?** `$GIT_INDEX_FILE`, which git sets for every commit. The SHARED
  index is the one named `index` or `index.lock`; a pathspec / `--only` commit gets
  `next-index-*.lock` (measured: `git commit -m M -- path` → `.git/next-index-<pid>.lock`,
  `git commit -a` → `.git/index.lock`).

REFUSE = primary worktree AND shared index AND no escape. Two escapes, both
logged: `KANBAN_COMMIT_FENCE=off`, or the repo's writer lock
(`hermes-svc-lock acquire ai-content-pipeline@nexus`, TTL 2 h; a STALE lock does
not lift the fence).

### Working in this tree now

    git commit -m "<msg>" -- <your paths>     # only your paths; a sibling's staged work stays staged
    git worktree add ../<name> -b <branch>    # your own index; commit freely there
    hermes-svc-lock acquire ai-content-pipeline@nexus --task "<what and why>"

A refused commit changes nothing: the fence exits before git writes anything, and
a sibling's staged files stay staged (both are asserted in the suite, cases
1–4).

## Where it is enforced (a rule nobody can fail on is not a fence)

| artifact | what it does |
|---|---|
| `music/scripts/git_commit_fence.sh` | the decision. Source of record. |
| `.githooks/pre-commit` (this repo and `~/mining-k8s`) | the arming. |
| `music/scripts/test_git_commit_fence.sh` | 15 planted-defect cases: the incident's own command shape is refused, the sibling's staged work survives a named-paths commit, `commit -a` is refused, a linked worktree and a held lock are allowed, a stale lock is not. |
| `music/scripts/check_commit_fence_armed.py` | asserts the fence EXISTS, is executable, the hook names it, `core.hooksPath` is set, and the mining-k8s copy is byte-equal (one implementation). Selftest: 7 cases, each proving it fires on one disarm class. |
| `music/scripts/run_gate_matrix.sh` leg **2e** | runs the armed check daily (06:20, `music-gate-matrix.timer`) and exits **6** when the fence is disarmed — distinct from a gate (1), panel (3), render-log (4) or media (5) defect. |

A hook is file state plus one LOCAL config key, and neither travels with the tree:
a fresh clone, a `git config --unset` or a lost exec bit disarms it silently. Leg
2e is the detector for exactly that, the same way
`music/scripts/check_scheduler_units.py` catches "fixed upstream, not installed"
(t_41f354be).

The mining-k8s copy lives at `scripts/git_commit_fence.sh` and is kept byte-equal
to this one (sha256) by the armed check; that repo is armed the same way.

## Answer to "is the parallel dispatch intended?"

Parallel is the dispatcher's designed behaviour, not a mis-set knob:
`kanban.max_in_progress` is unset in the gateway's config
(`HERMES_HOME=/home/j_kro/.hermes`, unit `hermes-gateway.service`), so the derived
cap applies — `clamp(MemTotal / 512 MiB, 2, 8)` =
`clamp(49232124 KiB / 1024 / 512 = 93, 2, 8)` = **8** (meminfo + the constants in
`hermes_cli/kanban_db_dispatch.py`), and 8 tasks were `running`. The music lane's
own `music-pipeline-driver.service` runs with `Environment=DRY_RUN=1`, so it
dispatches nothing; the generic gateway dispatcher does. The dispatcher has no
per-repo key at all, so it cannot be the fence. The fence belongs in the repo —
which is where it now is.

## Known residuals (measured, not fixed here)

* **The scheduled matrix reads the LIVE tree.** Proof: the same drill ran green at
  18:21 (`rc=0`, 47 PASS, 41 expected FAIL) and red at 18:24 (`rc=1`,
  `BROKEN: 3 check(s) misbehaved`) while `music/scripts/loop_close.py` sat with
  `+122 −20` uncommitted lines (mtime 18:24:45) — another card mid-edit. A verdict
  that depends on the instant it runs is not a verdict. Fix direction: run the
  suite from a per-run worktree or a snapshot, not the shared tree. Carded.
* `AGENTS.md` state it as a rule, and `AGENTS.md` is a protected file in this
  fleet: the human edit is pending (`j_kro`). Until then the rule reaches a card
  twice — this document and the refusal message, which prints the three commands
  at the moment of refusal.
* The fence blocks a whole-index commit; it cannot know which card OWNS a path.
  A card that deliberately lists a sibling's path in its pathspec is not caught.
  The fence is a fence, not a proof.
* `git rebase`, `git cherry-pick` and `git stash` do not run `pre-commit`; they
  also do not commit a shared INDEX entry, so the measured defect does not reach
  them.
