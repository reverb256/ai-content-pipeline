# A stale write reverts a shipped change — the guard is the CONTENT of the commit

Decision record for kanban **t_8dadd6cb** (2026-10-16). Measured on nexus; every
number below came from a command in that run. Companion to
`music/docs/SHARED-TREE.md` (t_6d0b7dd7), which fences the commit's SCOPE. This
one fences its CONTENT. Both are needed, and neither subsumes the other.

## The defect, measured

`/home/j_kro/ai-content-pipeline` is ONE git working tree that every concurrently
running music card writes to. A card that reads a file, edits it, and writes it
back **whole** puts back content another card has already committed. Nothing
fails, and the check whose bytes were lost simply stops running.

Three incidents, all on 2026-10-16, all in this one checkout:

| commit | what happened |
|---|---|
| `29f0c19` (card t_3497b627) | **A sibling's commit shipped another card's in-flight edit.** Section 6 of `music/tests/test_planner.py`, written minutes earlier by card t_96dfc521 and not yet committed, landed inside this card's commit, adapted to its own `ctx_g()` helper. `git show 29f0c19:music/tests/test_planner.py` carries it. |
| `9082ce3` → `edeef61` → `a31deb2` (cards t_96dfc521, t_69cab80b) | **A shipped change was reverted and the check stopped running.** `9082ce3` added section 13 to `music/gates/check_gate_suite.sh`, wiring the planner regression suite into the daily matrix. `edeef61` rewrote that file from a stale copy and the section was gone from HEAD. Re-landed as `a31deb2`. Measured, not inferred: `git show 9082ce3:music/gates/check_gate_suite.sh \| grep -c 'planner regression suite'` → `1`; `git show HEAD:…` → `0`. |
| `5cb2e3d` (card t_7a528617) | **The working tree was rolled back under a committed change.** It committed from this shared tree while the tree still held pre-change copies of card t_450e7f39's files and reverted that card's landing `6eb5a23` seven seconds after it landed. A bare `git add -A` in that tree would have reverted three more files whose content was already on `main`. |

`29f0c19` was caught only because a card re-read the file. `edeef61` cost real
work: the check it dropped ran nowhere for as long as it took a card to notice.

## The decision

**The guard is the CONTENT of the commit, at the two boundaries where the bytes
leave the card: `git commit` and `git push`.** Not worktree-only: the lane is
deliberately parallel (8 workers on 2026-10-16; `SHARED-TREE.md` §"is the
parallel dispatch intended?" derives the cap of 8 from `max_in_progress`), and a
worktree requirement protects neither the common path nor a card that lands by
merge. Not a convention either — the sibling card's own doc records that what
prevented the sweep in t_42bc85ba was a pathspec, "i.e. a habit, not a fence".

The fence in `SHARED-TREE.md` reads **scope**: does this commit use the shared
index and would it therefore carry a sibling's staged files? It is right, and it
cannot see this defect. Measured on the real incident: `edeef61` named its paths,
so it used a private index (`next-index-*.lock`) and the fence ALLOWS exactly the
commit that dropped section 13. Scope and content are two different questions
about one commit, so they are two guards in one hook chain.

### The rule

`music/scripts/check_stale_write.py`. For a path P, with **A** = the bytes the
branch carries (HEAD, or a commit's parent) and **S** = the bytes being
committed:

    dropped = the substantive lines of A that the diff to S removes or replaces
    kept    = the substantive lines of A that S retains
    age(c)  = `git rev-list --count c..<base>`      0 = the base itself, larger = older
    REFUSE  when dropped is non-empty, kept is non-empty, and
            min age(dropped) < min age(kept)

i.e. the change drops a line YOUNGER than every line it kept, so the writer's
snapshot predates that line. That is a fact about provenance, not a guess about
intent: positional `git blame` at the base names the commit that introduced each
line, and the refusal prints it, its subject and its card id.

Two more facts complete the rule:

* **an exact rollback is refused outright.** If S is byte-equal to this path's
  content at any of the last 30 commits that touched it, that is not a rewrite,
  it is a rollback, and the refusal names the revision (`is EXACTLY revision
  <sha>`). This is blob-id based, so it works for media too — measured on a
  `.png`. It is what catches the third incident's shape.
* **the SUBSTANTIVE filter.** Blank lines and pure separator / comment-punctuation
  lines are ignored. A line like `# ---…---` or `#` occurs hundreds of times in
  this repo's gate suite, and blame re-attributes it wherever a hunk was
  inserted, so it must never decide a verdict.

### Why this rule and not a simpler one — measured over the last 150 commits

| rule variant | flags |
|---|---|
| dropped is a SUBSET of the newest change to the path | 133 (useless) |
| dropped INTERSECTS the newest change | 172 (useless) |
| dropped intersects ANY of the last 5 changes | 248 (useless) |
| provenance, **content-keyed** blame | **misses `edeef61`** |
| provenance, **positional** blame + substantive filter | **11** ← shipped |

Content-keyed blame is the trap: this repo's gate suite alone has ~150 blank
lines and a repeated separator comment, so "the origin of the text `#`" spans
dozens of commits and every comparison collapses — measured, it reports the
dropped lines and the kept separator lines sharing the youngest origin, and
`edeef61` is not flagged. Positional blame catches `edeef61` and names `9082ce3`.

The audit arm (`--rev`, `--range`, `--since`, `--push`) additionally refuses an
exact rollback, and over the last 150 commits reports 12 refusals in 13 s:
`5cb2e3d` ×3 (the recorded revert), `edeef61` (the recorded drop), `176b575` ×2
(the deliberate re-land of `6eb5a23`), and 5 small edits in brief files.

## Declaring a drop you MEANT

The rule cannot read intent, so the refusal is a request to declare, not a
wall. A card that really means to drop those bytes says so, twice:

    KANBAN_STALE_WRITE=<sha>[,<sha>]   # clears THIS commit (it names the origins)
    Stale-write-dropped: <sha>         # in the commit message, on its own line

The env var cannot mute the guard: the shas must be the ones the guard named.
The **trailer** is the durable half — `--rev/--range/--since/--push` read history
and not an environment, so a commit whose message declares the origin bytes it
drops is reported as `declared` and never refused. Without the trailer, a
legitimate rollback would make the daily leg red for a day. `KANBAN_STALE_WRITE=off`
remains as an emergency override that must be explained in the card.

## Where it is enforced (a rule nobody can fail on is not a check)

| artifact | what it does |
|---|---|
| `music/scripts/check_stale_write.py` | the decision. Modes `--staged` (pre-commit), `--rev`, `--range`, `--since`, `--push` (pre-push), `--armed`. |
| `.githooks/pre-commit` | the commit-time arming. Runs the SCOPE fence (t_6d0b7dd7) and then this guard's `--staged`. |
| `.githooks/pre-push` | the publish-time arming. Judged on the commits being pushed, so it also covers `git rebase`/`git cherry-pick`/`git stash pop`, which do not run `pre-commit` — the same gap `SHARED-TREE.md` lists as a known residual. |
| `music/scripts/test_check_stale_write.py` | 37 planted-defect cases, each a real `git commit` / `git push` through the copied-in guard and hooks: the incident shape is refused, the sibling's staged work survives a named-paths commit, a **RED control** commits the same stale write with the guard bypassed and asserts the marker is gone, the audit finds it, the trailer clears it, a binary rollback is refused, and `--armed` reports a disarmed guard. |
| `check_stale_write.py --armed` | asserts `.githooks/pre-push` or `pre-commit` runs the guard, that `core.hooksPath` is `.githooks`, and that both are executable. A hook is file state plus one LOCAL config key, and neither travels with the tree. |
| `music/scripts/run_gate_matrix.sh` leg **2f** | runs the daily audit (06:20, `music-gate-matrix.timer`) and exits **7** when the guard is disarmed or a stale write landed in the window — distinct from a gate (1), panel (3), render-log (4), media (5) or fence (6) defect. It reads COMMITS, never the working tree, so a sibling mid-edit cannot move its verdict. |

## What the demo and the drill measured (all real, all reproducible)

* **The refusal, on the incident's own bytes.** In a real clone: staged content
  built from `9082ce3^`'s copy plus the writer's own section, committed with an
  explicit pathspec, is REFUSED — and the SCOPE fence ALLOWED the same commit,
  so the content guard is doing work the fence cannot. The audit on the real
  incident commit names the real origin: `--rev edeef61` →
  "introduced by: 9082ce3d (card t_96dfc521)". The recorded rollback
  `--rev 5cb2e3d` is refused three times over (three paths, each byte-equal to an
  older revision), and the re-land `--rev a31deb2` is PASS.
* **A refusal writes nothing.** HEAD does not move and the writer's bytes stay
  staged; a sibling's staged work is untouched.
* **Two concurrent writers, ONE file, both changes on the origin afterwards.**
  Non-overlapping edits: git's 3-way merge keeps BOTH sides, and the merge
  publish goes through the armed pre-push guard (`origin/main` carries writer A's
  and writer B's sections and section 13). Overlapping edits: the merge
  CONFLICTS at the same lines — with a real base the loss is visible, it cannot
  be silent — and keeping both sides publishes both.
* **The leg is wired and red for the right reason.** The daily run in drill mode
  exits **7**, logs `stale-write guard: armed_rc=0 audit_rc=1`, lists the named
  commits in the failing-checks block, and writes `stale_write_rc` +
  `stale_write_verdict` into the status JSON. With the window shortened to one
  minute it exits 0, so it measures history and not a constant.
* **git calls a pre-push hook with an EMPTY ref list** for an update it already
  rejects (measured on a non-fast-forward push). Nothing to judge is not a
  failure, so `--push` exits 0 there, and the hook maps the guard's "cannot
  measure" (rc 3) to NOTE-and-allow. Neither can block a push for the wrong
  reason.
* **A relative `core.hooksPath` resolves against the linked worktree's own root**
  — a worktree needs its own `.githooks`, or an absolute `core.hooksPath`, for the
  hooks to run there at all. Measured while testing the push arm.

## Working in this tree now

    git commit -m "<msg>" -- <your paths>       # names your paths; a sibling's staged work stays staged
    git show HEAD:<path> > <path>               # the CURRENT bytes, then edit them — never an old copy
    git worktree add ../<name> -b <branch>      # your own index and your own HEAD

`SHARED-TREE.md` keeps the SCOPE half of this list; the content half is the
middle line and it is the one both incidents crossed.

## Residuals (measured, not hidden)

* **Deliberate restores are refused until declared.** `176b575` (the re-land of
  `6eb5a23`) and a card rewording the line it committed last are both flagged;
  both are the same shape as a stale write, and both are cleared by the trailer.
  Measured rate: 12 refusals per 150 commits (~8 %), all nameable.
* **A whole-file rewrite with no line in common is NOT refused** (reported as
  `REWRITE`, allowed). There is nothing in common to prove provenance from, and
  a legitimate regeneration looks identical. A path DELETED by the change is
  likewise not refused, for the same reason.
* **The audit's window is wall-clock** (`STALE_WRITE_WINDOW`, default 24 h) while
  the rule's age is commit-count. A quiet day ages a line out of the window
  before its provenance stops mattering; that is the intended, conservative
  direction.
* **`edeef61`, `5cb2e3d` and today's 5 declared-class commits are inside the
  first daily window**, so the first matrix run after this card lands reports
  rc=7 naming them — measured, in drill mode, at 18:48 CDT: `rc=7`, its log line
  "stale-write guard: armed_rc=0 audit_rc=1", 11 REFUSE lines naming
  `176b5757`, `5cb2e3d` ×3, `69bec15d`, `5aa5238f`, `d0e1d8de`, `edeef615`,
  `9e5f2afc`, `c0bd386e`. That is the detector working on real state, not a
  defect: the window clears itself as the commits age out. The 5 are the
  deliberate-restore class above; a future run can silence them the only way the
  design allows — by fixing them or by landing a commit that declares the drop.
* **`~/mining-k8s` is not armed.** The sibling card mirrored its fence there;
  this guard is armed in the lane repo only. Arming it there is the same three
  steps (`cp music/scripts/check_stale_write.py ~/mining-k8s/`, copy
  `.githooks/pre-push`, `git config core.hooksPath .githooks`), and the mining-k8s
  side of a shared-tree commit has the same content hazard.
* **The trailer is a convention until someone checks it.** Nothing yet fails
  when a card uses `KANBAN_STALE_WRITE=off` without writing the trailer; the
  refusal message asks for both, and the emergency override is deliberately
  cheap. The audit is the backstop: an undeclared drop stays red.
