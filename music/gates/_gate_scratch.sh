# shellcheck shell=bash
# Fixture scratch for the gate suite: PRIVATE per run, and owned by the run.
#
# Source this file; do not execute it.
#
# INCIDENT (2026-10-16, card t_075cb010, measured during t_69cab80b).
# `bash music/gates/check_gate_suite.sh` took its fixture directory from the
# fixed default `/tmp/music-gate-fixtures`, and the suite rebuilds every fixture
# under that directory as it runs. Two overlapping runs therefore read each
# other's half-written trees, and the suite reported a healthy gate as BROKEN:
#
#     BAD   generator-built pack passes (pack mode) (expected exit 0, got 1)
#             FAIL gate_sync_ready
#               - no manifest.json
#               - no loop_points.json ...
#     BROKEN: 2 check(s) misbehaved
#
# while that same directory was fully populated a moment later and the same
# suite was green with a private directory (`GATE_SCRATCH=<private dir>`). The
# lane repo is ONE working tree shared by concurrent cards, so overlapping hand
# runs are likely, not exotic. A false BROKEN is worse than no check: the
# matrix's failure path posts to the alert feed and files a card.
#
# RULES
#   1. No GATE_SCRATCH in the environment -> this run gets its OWN directory
#      (`mktemp -d`), removed when the run ends. Two runs can never share it.
#   2. An explicit GATE_SCRATCH is honoured, because the scheduled matrix wants
#      a durable directory that it prunes itself (`music/scripts/
#      run_gate_matrix.sh`). There the run takes an exclusive lock on the
#      directory and REFUSES (rc 2) when another LIVE run holds that lock, or
#      when the directory already holds entries that no live run owns. A
#      refusal is never a check failure: the run stops before it reads anything.
#
# The lock lives BESIDE the directory (`<dir>.owner.d`), never inside it, so a
# caller that prunes the directory cannot erase a live run's ownership.
#
# Boundary: this lock guards the SUITE. A caller that PRUNES an explicit
# directory (`music/scripts/run_gate_matrix.sh` does, to rebuild the durable
# fixtures) removes trees, not locks, so it must not prune a directory a live
# run owns. The matrix prunes and then starts the suite, which takes the lock;
# a hand run no longer touches the matrix's directory at all (its default is
# private).
#
# Usage:
#   . "$GATES/_gate_scratch.sh"
#   gate_scratch_resolve || exit 2          # sets GATE_SCRATCH_RESOLVED
#   SCRATCH="$GATE_SCRATCH_RESOLVED"
#   gate_scratch_acquire || exit 2          # rc 2 = REFUSED, never a check failure
#   trap gate_scratch_release EXIT
#
# Environment:
#   GATE_SCRATCH             explicit fixture directory (durable; locked)
#   GATE_SCRATCH_KEEP        "1" = keep a private directory for inspection

GATE_SCRATCH_RESOLVED=""
GATE_SCRATCH_PRIVATE=0
GATE_SCRATCH_LOCK=""
GATE_SCRATCH_LOCK_OWNED=0

# The boot-relative start time of a pid: field 22 of /proc/<pid>/stat. It tells
# a live holder from a recycled pid - a lock left behind by a killed run names a
# pid that a later, unrelated process may have taken. Empty/rc 1 when the pid
# has no /proc entry (gone, or not Linux).
_gate_scratch_proc_start() { # pid -> start ticks
  local line rest
  [ -r "/proc/$1/stat" ] || return 1
  IFS= read -r line < "/proc/$1/stat" || return 1
  rest="${line#*) }"        # drop "pid (comm) ", so $1 is field 3 (state)
  # shellcheck disable=SC2086
  set -- $rest
  [ -n "${20:-}" ] || return 1
  printf '%s' "${20}"        # field 3 + 19 = field 22
}

_gate_scratch_holder_alive() { # pid, recorded start ticks
  local cur
  [ -n "${1:-}" ] || return 1
  [ "$1" = "$$" ] && return 0
  if cur="$(_gate_scratch_proc_start "$1")"; then
    # /proc answers for every user, so a holder owned by ANOTHER user (the root
    # run of the daily matrix) counts as live. `kill -0` cannot say that: EPERM
    # reads as "gone" and we would take over a live root run's directory.
    [ -z "${2:-}" ] && return 0
    [ "$cur" = "$2" ] && return 0
    return 1
  fi
  # No /proc (not Linux): fall back to the signal check, which cannot see
  # another user's process. Documented limit, Linux is the lane's only platform.
  kill -0 "$1" 2>/dev/null
}

gate_scratch_resolve() {
  if [ -n "${GATE_SCRATCH:-}" ]; then
    GATE_SCRATCH_RESOLVED="$GATE_SCRATCH"
    GATE_SCRATCH_PRIVATE=0
  else
    mkdir -p "${TMPDIR:-/tmp}" 2>/dev/null || return 2
    GATE_SCRATCH_RESOLVED="$(mktemp -d "${TMPDIR:-/tmp}/music-gate-fixtures.XXXXXXXX" 2>/dev/null)" || return 2
    GATE_SCRATCH_PRIVATE=1
  fi
  mkdir -p "$GATE_SCRATCH_RESOLVED" 2>/dev/null || return 2
  return 0
}

gate_scratch_acquire() { # rc 0 = this run owns the directory, rc 2 = refused
  local dir="${GATE_SCRATCH_RESOLVED:-}"
  local lock pid rec entries
  [ -n "$dir" ] || return 2
  lock="$dir.owner.d"
  GATE_SCRATCH_LOCK="$lock"

  if mkdir "$lock" 2>/dev/null; then       # atomic: the one winner takes it
    GATE_SCRATCH_LOCK_OWNED=1
  else
    pid="$(cat "$lock/pid" 2>/dev/null || true)"
    rec="$(cat "$lock/start_ticks" 2>/dev/null || true)"
    if _gate_scratch_holder_alive "$pid" "$rec"; then
      {
        echo "REFUSED: another run of the gate suite owns $dir"
        echo "         holder: pid $pid on $(cat "$lock/host" 2>/dev/null || echo '?'), started $(cat "$lock/started" 2>/dev/null || echo '?')"
        echo "         That run is building its fixtures there right now. Reading that"
        echo "         tree is how two overlapping runs reported a healthy gate as BROKEN"
        echo "         (2026-10-16, card t_075cb010)."
        echo "         Wait for it to finish, or unset GATE_SCRATCH for a private directory."
        # The last line is the run's verdict: run_gate_matrix.sh records it in
        # the status JSON as `verdict`, and no check has run at this point.
        echo "REFUSED: no gate was checked against $dir (rc 2)"
      } >&2
      return 2
    fi
    rm -rf "$lock" 2>/dev/null || return 2
    if ! mkdir "$lock" 2>/dev/null; then
      echo "REFUSED: cannot take the lock at $lock - another writer won the race" >&2
      return 2
    fi
    GATE_SCRATCH_LOCK_OWNED=1
    echo "note: took over the stale lock at $lock (holder pid ${pid:-unknown} is gone)" >&2
  fi

  printf '%s\n' "$$" > "$lock/pid"
  printf '%s\n' "$(_gate_scratch_proc_start "$$" 2>/dev/null || true)" > "$lock/start_ticks"
  date -Is > "$lock/started"
  hostname > "$lock/host"
  printf '%s\n' "$dir" > "$lock/dir"

  # Ownership is settled; now the tree itself. The suite builds its fixtures in
  # place and never prunes, so a non-empty tree this run did not build holds
  # another run's (or another revision's) files - and the pack gate counts the
  # files on disk. Refuse rather than read them as ours.
  entries="$(find "$dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" || entries="?"
  if [ -n "$entries" ]; then
    {
      echo "REFUSED: $dir already holds entries and no live run owns it"
      echo "         first entry: $entries"
      echo "         This suite builds its fixtures in place, so those files would be"
      echo "         read as THIS run's fixtures (card t_075cb010)."
      echo "         Fix: unset GATE_SCRATCH (default: a private directory), or clear that one."
      echo "REFUSED: no gate was checked against $dir (rc 2)"
    } >&2
    gate_scratch_release
    return 2
  fi
  return 0
}

gate_scratch_release() { # safe to call twice; never removes another run's lock
  local lock="${GATE_SCRATCH_LOCK:-}"
  if [ -n "$lock" ] && [ "${GATE_SCRATCH_LOCK_OWNED:-0}" = 1 ] && [ -d "$lock" ] \
     && [ "$(cat "$lock/pid" 2>/dev/null)" = "$$" ]; then
    rm -rf "$lock" 2>/dev/null || true
  fi
  GATE_SCRATCH_LOCK=""
  GATE_SCRATCH_LOCK_OWNED=0
  if [ "${GATE_SCRATCH_PRIVATE:-0}" = 1 ] && [ -n "${GATE_SCRATCH_RESOLVED:-}" ]; then
    if [ "${GATE_SCRATCH_KEEP:-0}" = 1 ]; then
      echo "note: keeping the private fixture directory $GATE_SCRATCH_RESOLVED (GATE_SCRATCH_KEEP=1)" >&2
    else
      rm -rf "$GATE_SCRATCH_RESOLVED" 2>/dev/null || true
    fi
  fi
  return 0
}
