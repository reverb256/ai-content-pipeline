#!/usr/bin/env bash
# test_git_commit_fence.sh — planted-defect suite for the shared-tree commit
# fence (kanban t_6d0b7dd7). Every case builds a throwaway fixture repo that
# mirrors the lane layout (music/scripts/git_commit_fence.sh + .githooks/
# pre-commit, both COPIED VERBATIM from this repo) and drives real `git commit`
# calls through the shipped pair. A case asserts the exit status AND the line
# the fence printed — an exit code alone cannot say WHICH decision was taken.
#
# The case list is the defect's decision table:
#   1  the incident's own command (`git add <own> <sibling>; git commit`)    REFUSE
#   2  the same, with the sibling's staged work intact afterwards            (post-condition)
#   3  `git commit -m M -- <own>` in the shared tree                         ALLOW, own paths only
#   4  a sibling's staged work survives a named-paths commit                 (post-condition)
#   5  `git commit -a` in the shared tree (stages every tracked edit)        REFUSE
#   6  a commit in a LINKED WORKTREE (private index)                         ALLOW
#   7  the writer lock is held (hermes-svc-lock, fresh)                      ALLOW
#   8  the writer lock is STALE (older than TTL)                             REFUSE
#   9  the lock is found by the DEFAULT service name (repo@host)             ALLOW
#  10  KANBAN_COMMIT_FENCE=off (documented override)                         ALLOW
#  11  no repository to measure (fence run outside a worktree)               ALLOW, NOTE
#
# Usage: bash music/scripts/test_git_commit_fence.sh
# Exit 0 = every case behaved; 1 = a case misbehaved; 2 = fixtures unusable.
set -uo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FENCE_SRC="$SRC/music/scripts/git_commit_fence.sh"
HOOK_SRC="$SRC/.githooks/pre-commit"
FIX="$(mktemp -d "${TMPDIR:-/tmp}/commit-fence-test.XXXXXX")" || exit 2
MAIN="$FIX/fencefix-repo"          # the "shared" primary worktree
WT="$FIX/fencefix-wt"              # a linked worktree of it
LOCKS="$FIX/locks"
SVC="fencefix@test"

fails=0
cases=0
cleanup() { rm -rf -- "$FIX"; }
trap cleanup EXIT

[ -f "$FENCE_SRC" ] || { echo "FATAL: no fence at $FENCE_SRC"; exit 2; }
[ -f "$HOOK_SRC" ] || { echo "FATAL: no hook at $HOOK_SRC"; exit 2; }

# --- fixtures ---------------------------------------------------------------
fresh() { # a primary tree with two files, both committed, fence+hook copied in
  rm -rf -- "$MAIN" "$WT" "$LOCKS"
  mkdir -p "$MAIN/music/scripts" "$MAIN/.githooks" "$LOCKS"
  cp "$FENCE_SRC" "$MAIN/music/scripts/git_commit_fence.sh"
  cp "$HOOK_SRC" "$MAIN/.githooks/pre-commit"
  chmod +x "$MAIN/music/scripts/git_commit_fence.sh" "$MAIN/.githooks/pre-commit"
  git -C "$MAIN" init -q -b main
  git -C "$MAIN" config user.email fence@test
  git -C "$MAIN" config user.name fence
  git -C "$MAIN" config core.hooksPath .githooks
  printf 'mine v1\n' > "$MAIN/music/mine.txt"
  printf 'theirs v1\n' > "$MAIN/music/theirs.txt"
  git -C "$MAIN" add -A
  # the seed commit names its paths (private index) so the fence allows it;
  # its hook output is captured so the case lines below stay readable, and a
  # seed that cannot commit is fatal (a case would otherwise run against a tree
  # that was never seeded).
  if ! git -C "$MAIN" commit -q -m seed -- . > "$FIX/seed.log" 2>&1; then
    echo "FATAL: fixture seed commit failed:" >&2
    sed 's/^/        /' "$FIX/seed.log" >&2
    exit 2
  fi
}

# stage a modification of BOTH files: mine.txt is this card's work,
# theirs.txt is the sibling card's staged-and-uncommitted work.
stage_pair() {
  printf 'mine v2\n' > "$MAIN/music/mine.txt"
  printf 'theirs v2\n' > "$MAIN/music/theirs.txt"
  git -C "$MAIN" add -- music/mine.txt music/theirs.txt
}

env_fx() { # run a command inside the fixture with the fence's own knobs pinned
  env -u GIT_INDEX_FILE -u GIT_DIR -u GIT_WORK_TREE \
      HERMES_LOCK_ROOT="$LOCKS" KANBAN_COMMIT_FENCE_SERVICE="$SVC" "$@"
}

check() { # label, expectation(rc int|nonzero), fence-line substring, then cmd
  local label="$1" want="$2" line="$3"; shift 3
  local out rc ok=1
  out="$("$@" 2>&1)"; rc=$?
  cases=$((cases+1))
  if [ "$want" = "nonzero" ]; then
    [ "$rc" -ne 0 ] || ok=0
  else
    [ "$rc" = "$want" ] || ok=0
  fi
  if [ -n "$line" ] && ! printf '%s' "$out" | grep -qF -- "$line"; then ok=0; fi
  if [ "$ok" = 1 ]; then
    printf 'PASS [%s]: rc=%s (said "%s")\n' "$label" "$rc" "$line"
  else
    printf 'BAD  [%s]: expected rc=%s saying "%s", got rc=%s\n' "$label" "$want" "$line" "$rc"
    printf '%s\n' "$out" | sed 's/^/        /'
    fails=$((fails+1))
  fi
}

assert() { # label, then a test expression evaluated by the caller's `[`
  local label="$1"; shift
  cases=$((cases+1))
  if "$@" >/dev/null 2>&1; then
    printf 'PASS [%s]\n' "$label"
  else
    printf 'BAD  [%s] (post-condition not met)\n' "$label"
    fails=$((fails+1))
  fi
}

echo "fixture: $FIX   fence: $FENCE_SRC   hook: $HOOK_SRC"
echo

# --- 1+2. the incident's own command shape ----------------------------------
fresh
stage_pair
before="$(git -C "$MAIN" rev-parse HEAD)"
check "incident: git add both, then whole-index commit" nonzero "REFUSE" \
      env_fx git -C "$MAIN" commit -m "mine only (incident shape)"
after="$(git -C "$MAIN" rev-parse HEAD)"
assert "incident: nothing was committed (HEAD unchanged)" test "$before" = "$after"
assert "incident: both files are still staged, the sibling's work intact" \
       test "$(git -C "$MAIN" diff --cached --name-only | sort | tr '\n' ' ')" = "music/mine.txt music/theirs.txt "

# --- 3+4. the named-paths commit: allowed, and it carries only my paths -----
check "named paths: git commit -m M -- music/mine.txt" 0 "ALLOW" \
      env_fx git -C "$MAIN" commit -m "mine only, named" -- music/mine.txt
assert "named paths: the commit carries ONLY music/mine.txt" \
       test "$(git -C "$MAIN" show --pretty='' --name-only HEAD | sed '/^$/d' | tr '\n' ' ')" = "music/mine.txt "
assert "named paths: the sibling's file is STILL staged after my commit" \
       test "$(git -C "$MAIN" diff --cached --name-only)" = "music/theirs.txt"
assert "named paths: the sibling's staged CONTENT is untouched" \
       test "$(git -C "$MAIN" show :music/theirs.txt)" = "theirs v2"

# --- 5. git commit -a (stages every tracked edit in the shared tree) --------
fresh
b5="$(git -C "$MAIN" rev-parse HEAD)"
printf 'mine v2\n' > "$MAIN/music/mine.txt"
printf 'theirs v2\n' > "$MAIN/music/theirs.txt"
check "commit -a in the shared tree" nonzero "REFUSE" \
      env_fx git -C "$MAIN" commit -a -m "all tracked edits"
assert "commit -a: nothing was committed (HEAD unchanged, still one commit)" \
       test "$(git -C "$MAIN" rev-parse HEAD)" = "$b5"

# --- 6. a linked worktree has a private index -------------------------------
fresh
git -C "$MAIN" worktree add -q "$WT" -b wt
printf 'wt work\n' > "$WT/music/mine.txt"
git -C "$WT" add -- music/mine.txt
check "linked worktree: whole-index commit is scoped to that worktree" 0 "ALLOW" \
      env_fx git -C "$WT" commit -m "worktree work"

# --- 7+8+9. the writer lock -------------------------------------------------
fresh
stage_pair
mkdir -p "$LOCKS/$SVC.lock.d"
{ echo "service=$SVC"; echo "holder=someone:else"; echo "host=$(hostname -s)"; echo "pid=1";
  echo "started=now"; echo "epoch=$(( $(date +%s) - 60 ))"; } > "$LOCKS/$SVC.lock.d/holder"
check "writer lock held (fresh): commit freely" 0 "ALLOW" \
      env_fx git -C "$MAIN" commit -m "while holding the lock"

fresh
stage_pair
mkdir -p "$LOCKS/$SVC.lock.d"
{ echo "service=$SVC"; echo "holder=long-gone:stale"; echo "epoch=$(( $(date +%s) - 9000 ))"; } \
      > "$LOCKS/$SVC.lock.d/holder"
check "writer lock STALE (older than TTL): still refused" nonzero "REFUSE" \
      env_fx git -C "$MAIN" commit -m "under a stale lock"

fresh
stage_pair
DEFSVC="$(basename "$MAIN")@$(hostname -s)"
mkdir -p "$LOCKS/$DEFSVC.lock.d"
{ echo "service=$DEFSVC"; echo "holder=someone:else"; echo "epoch=$(( $(date +%s) - 30 ))"; } \
      > "$LOCKS/$DEFSVC.lock.d/holder"
check "default service name (repo@host) finds the lock" 0 "ALLOW" \
      env -u KANBAN_COMMIT_FENCE_SERVICE -u GIT_INDEX_FILE -u GIT_DIR -u GIT_WORK_TREE \
          HERMES_LOCK_ROOT="$LOCKS" \
          git -C "$MAIN" commit -m "lock found by default service key"

# --- 10. the documented override -------------------------------------------
fresh
stage_pair
check "KANBAN_COMMIT_FENCE=off" 0 "override set" \
      env KANBAN_COMMIT_FENCE=off HERMES_LOCK_ROOT="$LOCKS" KANBAN_COMMIT_FENCE_SERVICE="$SVC" \
          git -C "$MAIN" commit -m "override"

# --- 11. no repository to measure (fail-open, with a NOTE) ------------------
out="$(cd "$FIX" && env -u GIT_DIR -u GIT_INDEX_FILE -u GIT_WORK_TREE bash "$FENCE_SRC" 2>&1)"; rc=$?
cases=$((cases+1))
if [ "$rc" = 0 ] && printf '%s' "$out" | grep -qF "no-measure" && printf '%s' "$out" | grep -qF "ALLOW"; then
  printf 'PASS [outside a repository: fail-open with a NOTE]: rc=0 (said "%s")\n' \
         "$(printf '%s' "$out" | head -1)"
else
  printf 'BAD  [outside a repository]: expected rc=0 + no-measure, got rc=%s\n' "$rc"
  printf '%s\n' "$out" | sed 's/^/        /'
  fails=$((fails+1))
fi

echo
if [ "$fails" -eq 0 ]; then
  echo "RESULT: pass ($cases cases) — the fence refuses the incident's commit shape, keeps a"
  echo "        sibling's staged work staged, and allows every documented escape"
  exit 0
fi
echo "RESULT: FAIL ($fails of $cases cases misbehaved)"
exit 1
