#!/usr/bin/env bash
# git_commit_fence.sh — refuse a WHOLE-INDEX commit in a SHARED working tree.
#
# Incident this exists for (t_6d0b7dd7, measured 2026-10-16, card t_42bc85ba):
#
#   /home/j_kro/ai-content-pipeline is ONE git working tree that every
#   concurrently running music card commits to. A sibling card had four files
#   STAGED and not yet committed in that shared index. A card ran
#       git add music/sunolocal && git commit -m '...'
#   and the commit (545faa3) carried the sibling's four files:
#       music/briefs/commentary-beds.md, music/gates/check_gate_suite.sh,
#       music/planner/planner.py, music/tests/test_planner.py
#   It was reset and re-made with a pathspec by luck (the stat was read).
#   The same hazard later DID cost work: commit 5cb2e3d (t_7a528617) committed
#   from this shared tree while it still held pre-change copies of card
#   t_450e7f39's three files and reverted that card's landing 6eb5a23 seven
#   seconds after it landed.
#
# The mechanism of the defect, not the convention:
#   * a commit that uses the SHARED index (`.git/index`) commits EVERYTHING
#     staged in it, whatever card staged it;
#   * `git commit -a` is worse — it stages every tracked modification in the
#     tree before committing it;
#   * a commit that names its paths (`git commit -m M -- <paths>`) uses a
#     PRIVATE temporary index (`<git-dir>/next-index-*.lock`), so it carries
#     only those paths and leaves every other card's staged work staged.
#
# So the fence reads two facts git already knows, and nothing else:
#   primary ?  absolute git dir == absolute common git dir
#              (a linked worktree has its own git dir -> private index -> safe)
#   index ?    $GIT_INDEX_FILE, which git sets for every commit. The SHARED
#              index is the one named `index` or `index.lock`; a pathspec /
#              --only commit gets `next-index-*.lock`.
#
# REFUSE = primary worktree AND shared index AND no documented escape.
# Escapes (both are real, both name the reason):
#   KANBAN_COMMIT_FENCE=off          — emergency override for a tree only you
#                                      are in; say why in your card.
#   the repo's writer lock is held   — hermes-svc-lock acquire <repo>@<host>
#                                      (service-writer-lock skill), which is
#                                      the sanctioned "one writer at a time".
#
# Exit codes: 0 allow | 1 refuse | 2 usage. Never 1 for an unreadable state:
# a fence that cannot measure prints NOTE and allows, and
# music/scripts/check_commit_fence_armed.py is what reports a broken fence on
# the schedule.
#
# Usage:  bash git_commit_fence.sh [--quiet]      (as a pre-commit hook)
#         bash git_commit_fence.sh --explain      (print the decision, always 0)
#
# Regression suite: music/scripts/test_git_commit_fence.sh (planted defects).
set -uo pipefail

quiet=0
explain=0
for arg in "$@"; do
  case "$arg" in
    --quiet) quiet=1 ;;
    --explain) explain=1 ;;
    -h|--help) sed -n '2,50p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "commit-fence: usage: git_commit_fence.sh [--quiet] [--explain]" >&2; exit 2 ;;
  esac
done

say() { [ "$quiet" = 1 ] && return 0; printf 'commit-fence: %s\n' "$1" >&2; }

# --- can we measure at all? -------------------------------------------------
gitdir="$(git rev-parse --absolute-git-dir 2>/dev/null)" || gitdir=""
common="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || common=""
if [ -z "$gitdir" ] || [ -z "$common" ] || [ ! -d "$common" ]; then
  say "ALLOW no-measure — 'git rev-parse' could not name this repository (not a worktree, or a bare repo). Not a shared-tree commit."
  exit 0
fi

# --- which index is this commit using? --------------------------------------
idx="${GIT_INDEX_FILE:-$gitdir/index}"
case "$idx" in
  /*) : ;;
  *) idx="$PWD/$idx" ;;
esac
# normalise without requiring coreutils realpath
idx_dir="$(cd "$(dirname "$idx")" 2>/dev/null && pwd -P)" || idx_dir=""
if [ -n "$idx_dir" ]; then idx="$idx_dir/$(basename "$idx")"; fi
idx_base="$(basename "$idx")"

primary=0
[ "$gitdir" = "$common" ] && primary=1

shared_index=0
case "$idx_base" in
  index|index.lock) shared_index=1 ;;
esac

repo="$(basename "$(dirname "$common")")"
host="$(hostname -s 2>/dev/null || echo host)"
svc="${KANBAN_COMMIT_FENCE_SERVICE:-$repo@$host}"

decide() {
  local verdict="$1" reason="$2"
  if [ "$explain" = 1 ]; then
    printf 'commit-fence: %s — %s\n' "$verdict" "$reason"
    printf '  repo=%s primary=%s index=%s\n' "$repo" "$primary" "$idx"
    exit 0
  fi
  if [ "$verdict" = "REFUSE" ]; then
    [ "$quiet" = 1 ] || printf 'commit-fence: REFUSE — %s\n' "$reason" >&2
    cat >&2 <<EOF

  This tree is shared by every concurrently running card, and this commit would
  use the SHARED index — it would carry whatever another card has staged, and
  \`git commit -a\` also stages every tracked edit in the tree first.
  Measured: 545faa3 swept four files card t_96dfc521 had staged (t_42bc85ba);
  5cb2e3d reverted card t_450e7f39's landing 6eb5a23 seven seconds after it landed.

  Commit your paths, or commit from your own worktree:

      git commit -m "<msg>" -- <your paths>     # only your paths; a sibling's staged work stays staged
      git worktree add ../$(basename "$PWD")-\$\$ -b <branch> && cd ../$(basename "$PWD")-\$\$

  Escapes (both are logged and both belong in your card):
      KANBAN_COMMIT_FENCE=off <your commit>                 # only when you are the only card here
      hermes-svc-lock acquire $svc --task "<what and why>"  # one writer at a time, then commit freely

  The rule, in one line: in the shared tree, name your paths — or leave the tree.
  Reference: kanban t_6d0b7dd7.
EOF
    exit 1
  fi
  say "$verdict — $reason"
  exit 0
}

[ "$primary" = 1 ] || decide ALLOW "linked worktree ($gitdir) — its index is private to this worktree."
[ "$shared_index" = 1 ] || decide ALLOW "private index $idx — this commit is scoped to the paths it names."

# --- escapes ----------------------------------------------------------------
if [ "${KANBAN_COMMIT_FENCE:-}" = "off" ]; then
  decide ALLOW "KANBAN_COMMIT_FENCE=off — override set. Name it in your card; the fence is off for this commit only."
fi

lock_root="${HERMES_LOCK_ROOT:-$HOME/.hermes/locks}"
ttl="${HERMES_LOCK_TTL:-7200}"
holder="$lock_root/$svc.lock.d/holder"
if [ -f "$holder" ]; then
  epoch="$(awk -F= '/^epoch=/{print $2; exit}' "$holder" 2>/dev/null)"
  who="$(awk -F= '/^holder=/{print $2; exit}' "$holder" 2>/dev/null)"
  now="$(date +%s)"
  if [ -n "$epoch" ] && [ "$epoch" -gt 0 ] 2>/dev/null && [ "$((now - epoch))" -lt "$ttl" ]; then
    decide ALLOW "writer lock $svc held by ${who:-?} ($((now - epoch))s of ${ttl}s TTL) — one writer at a time; commit freely."
  fi
fi

decide REFUSE "primary worktree of $repo + SHARED index ($idx), no writer lock on $svc and no override."
