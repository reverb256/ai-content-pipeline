#!/usr/bin/env bash
# Weekly performance review ritual (Reflect->Evolve closing step).
#   1) Gather REAL metrics into performance/weekly/<date>.md.
#      Every metric fails LOUDLY — a digest that cannot measure must say so.
#      (The 2026-09-28 run measured an empty directory and reported false zeros;
#      never let that recur.)
#   2) If the gather is clean, dispatch the editor review (async). The editor
#      writes performance/weekly/<date>-review.md and files the
#      'weekly review <date>' card on the media board.
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
BOARD="${BOARD:-media}"
HERMES="${HERMES_BIN:-$HOME/.local/bin/hermes}"
DATE=$(date +%F)
OUT="$REPO/performance/weekly/$DATE.md"
LOG="$REPO/performance/weekly-reviews.log"
mkdir -p "$REPO/performance/weekly"

cd "$REPO"
NOW=$(date -Is)
FAILS=()

# --- git metric: read the real clone; a missing .git is a loud failure --------
if [ -d .git ]; then
  GIT_COMMITS=$(git log --oneline --since="7 days ago" 2>/dev/null | wc -l | tr -d ' ')
  GIT_HEAD=$(git log -1 --format='%h %s' 2>/dev/null || echo none)
else
  GIT_COMMITS="FAILED"; GIT_HEAD="FAILED"
  FAILS+=("git metric: no .git in $REPO — refusing to report 0 by construction")
fi

# --- kanban metric: --board is a GLOBAL flag; non-zero exit fails loudly ------
KANBAN_STATS_MD=""
for B in "$BOARD" faceless-youtube; do
  if S=$("$HERMES" kanban --board "$B" stats 2>&1); then
    KANBAN_STATS_MD="$KANBAN_STATS_MD"$'\n'"### $B"$'\n''```'$'\n'"$S"$'\n''```'
  else
    KANBAN_STATS_MD="$KANBAN_STATS_MD"$'\n'"### $B — FAILED"
    FAILS+=("kanban metric ($B): stats failed: $S")
  fi
done

# --- artifact scan walks brain/, performance/ AND campaigns/ ------------------
ARTIFACTS=$(find brain performance campaigns -type f \( -name '*.md' -o -name '*.txt' -o -name 'metadata.json' -o -name 'lessons.json' \) 2>/dev/null | wc -l | tr -d ' ')

# --- previous week's actions --------------------------------------------------
PREV=$(ls -1 performance/weekly/*.md 2>/dev/null | grep -v "/$DATE" | sort | tail -1 || true)
PREV_ACTIONS="(no previous digest found)"
if [ -n "${PREV:-}" ]; then
  PREV_ACTIONS=$(awk 'tolower($0) ~ /^#+ *([0-9]+[.)]? *)?(actions|next actions|proposed actions)/ {f=1; next} /^#+ / {f=0} f' "$PREV" | sed '/^[[:space:]]*$/d' | head -15)
  [ -z "$PREV_ACTIONS" ] && PREV_ACTIONS="($(basename "$PREV") has no Actions section)"
fi

# --- assets in the human gate, deduped, real ages (E1/E2 fixes) ----------------
GATE=$(python3 - "$REPO" <<'PY'
import re, sys, glob, os, datetime, subprocess
repo = sys.argv[1]
now = datetime.date.today()

def git_date(p):
    try:
        out = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%cs", "--", p],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return datetime.date.fromisoformat(out) if out else None
    except Exception:
        return None

def content_date(t):
    for pat in (r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})",
                r"\*\*Uploaded:\*\*\s*(\d{4}-\d{2}-\d{2})"):
        m = re.search(pat, t)
        if m:
            return datetime.date.fromisoformat(m.group(1))
    return None

rows = {}
def add(key, path, day, label):
    if key not in rows or day < rows[key][0]:   # keep the OLDEST = true gate start
        rows[key] = (day, path, label)

def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return None

# 1) private/unlisted uploads (the publish gate)
for p in sorted(glob.glob(f"{repo}/campaigns/**/*.md", recursive=True)):
    t = read(p)
    if not t or not re.search(r"\*\*Visibility:\*\*\s*(Private|Unlisted)", t, re.I):
        continue
    day = content_date(t) or git_date(p) or datetime.date.fromtimestamp(os.path.getmtime(p))
    vid = re.search(r"\*\*Video ID:\*\*\s*(\S+)", t)
    add(f"video:{vid.group(1)}" if vid else p, p, day, f"video {vid.group(1)}" if vid else "upload")

# 2) angle / other human-approval gates recorded in campaign records
for p in sorted(glob.glob(f"{repo}/campaigns/**/*.md", recursive=True)):
    t = read(p)
    if not t:
        continue
    m = re.search(r"\*\*Status:\*\*\s*([^|\n]*awaiting human approval[^|\n]*)", t, re.I)
    if m:
        day = content_date(t) or git_date(p) or datetime.date.fromtimestamp(os.path.getmtime(p))
        add(f"angle:{os.path.dirname(p)}", p, day, m.group(1).strip())

# 3) content.lan sidecars awaiting approval
for p in sorted(glob.glob("/opt/content-site/media/**/*.md", recursive=True)):
    t = read(p)
    if t and "status: awaiting-approval" in t:
        add(f"lan:{p}", p, datetime.date.fromtimestamp(os.path.getmtime(p)), "awaiting-approval")

if rows:
    for key, (day, path, label) in sorted(rows.items(), key=lambda kv: kv[1][0]):
        print(f"- {path} (gated {(now - day).days}d) — {label}")
else:
    print("(none detected)")
PY
)

# --- write the digest ---------------------------------------------------------
{
  echo "# Weekly Review $DATE"
  echo
  echo "**Generated:** $NOW by \`scripts/automation/weekly-review.sh\` (tree: $REPO)"
  echo "**Git HEAD:** $GIT_HEAD"
  echo
  echo "## Metrics"
  echo "- Git commits (7d): $GIT_COMMITS"
  echo "- Review artifacts (brain/, performance/, campaigns/): $ARTIFACTS"
  echo "- Kanban boards:"
  echo "$KANBAN_STATS_MD"
  echo
  echo "## Previous week's actions"
  echo "$PREV_ACTIONS"
  echo
  echo "## Assets in the human gate"
  echo "$GATE"
  echo
  echo "## Editor judgment"
  echo "(filled in by the editor review — decision: keep / test / stop)"
  if [ "${#FAILS[@]}" -gt 0 ]; then
    echo
    echo "## FAILED metrics"
    for f in "${FAILS[@]}"; do echo "- $f"; done
  fi
} > "$OUT"

echo "$NOW — digest written: $OUT (commits=$GIT_COMMITS artifacts=$ARTIFACTS fails=${#FAILS[@]})" | tee -a "$LOG"

# --- editor dispatch (only on a clean gather) ---------------------------------
if [ "${#FAILS[@]}" -gt 0 ]; then
  echo "$NOW — gather FAILED; editor review NOT dispatched (fix the metrics first)" | tee -a "$LOG"
  exit 1
fi

if [ "${SKIP_EDITOR:-0}" = "1" ]; then
  echo "$NOW — editor review dispatch skipped (SKIP_EDITOR=1)" | tee -a "$LOG"
  exit 0
fi

nohup "$HERMES" -p editor chat -q "Run the weekly review ritual for $DATE. Digest: $OUT. Read it, check the counts against live state (git, kanban board '$BOARD', campaigns/), decide keep/test/stop, and file the result as a 'weekly review $DATE' card on the '$BOARD' board (assignee: editor). Write your review to performance/weekly/$DATE-review.md. Do not fix metrics yourself; if the digest looks wrong, say so in the card." --oneshot -Q >> "$LOG" 2>&1 &
echo "$NOW — editor review dispatched (async; log: $LOG)" | tee -a "$LOG"
