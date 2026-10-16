#!/usr/bin/env python3
"""music/oracle.py — daily music opportunity oracle.

Scans lane performance, genre ROI, platform policy signals, and trend
signals. Emits scored cards to the `music` kanban board.

Design pattern basis (researched 2026-10-09):
  - kanban-python (Zaloog): single load module, fail-loud validation,
    scan-to-create-task pattern.
  - johal.in kanban automation: weighted-sum scoring Score = Σ w_j·f_j(i),
    threshold-based auto-move.
  - musyn.io: multi-dimensional scoring (6 dimensions) composited into
    one ranked signal; daily intelligence briefs with recommendations.

Data sources (all live reads — no vibes):
  - music/quota-ledger.json        → quota consumption
  - music/registry.py              → genre + lane registry (fail-loud)
  - brain/research/music-monetization-2026.md  → platform research
  - performance/weekly/            → lane performance (analyst digests)
  - performance/oracle-watchlist.md → existing oracle signals
  - music/lanes.yaml               → lane surfaces and gates

Scoring rubric (data-driven, weighted — musyn 6-dimension model):
  Each genre gets a composite score from:
    - quota_headroom   (25%): remaining quota before hard_stop
    - lane_coverage   (20%): viable (non-banned) lanes opened
    - revenue_potential(20%): lane revenue bands from research
    - cadence_fit     (15%): cadence vs remaining days in period
    - policy_risk     (10%): banned-surface penalty
    - trend_signal    (10%): external trend heat (web search)

  Score range: 0-10. Cards >= 5 get created on the board.

Stage positioning (card t_6599927d): every card body carries exactly ONE
`stage:` marker — the card's route, which the driver routes on. It is resolved by
music/stage_state.py from the genre's artifacts: a card starts at the first stage
of music/stages.yaml with no artifact on disk, so a re-emitted genre does not
re-run a stage that is already delivered (all 14 genres' briefs were on disk on
2026-10-16 while 13 cards were queued back through `brief`). A resolver failure
creates NO cards — fail closed, exactly like an unreadable board.
"""

import json
import re
import sys
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# Resolve REPO from this file's location: music/oracle.py is always at
# <repo>/music/oracle.py, so the repo root is the parent of this dir.
MUSIC_DIR = Path(__file__).resolve().parent
REPO = MUSIC_DIR.parent
PERF_DIR = REPO / "performance"

# ── Where a new card starts (card t_6599927d) ───────────────────────────────
# A card's body marker is the card's ROUTE (the driver reads the last
# `stage:` match and dispatches that stage). This emitter used to write one
# fixed marker, `stage: brief`, so a re-emitted card re-entered the brief stage
# although the genre's brief was already on disk — measured 2026-10-16: all 14
# genres, 13 music-producer runs of the 14:05 wave. The rule that replaced it
# lives in ONE place, music/stage_state.py, and reads the stage ORDER from
# music/stages.yaml (the file that declares it). music/ is not a package, so put
# the lane dir on sys.path — the pattern music/scripts/check_video_shapes.py uses.
if str(MUSIC_DIR) not in sys.path:
    sys.path.insert(0, str(MUSIC_DIR))
import stage_state  # noqa: E402  (needs sys.path set first)

# ── Scoring weights (sum to 1.0) ────────────────────────────────────────────
WEIGHTS = {
    "quota_headroom": 0.25,
    "lane_coverage": 0.20,
    "revenue_potential": 0.20,
    "cadence_fit": 0.15,
    "policy_risk": 0.10,
    "trend_signal": 0.10,
}

# ── Revenue bands per lane surface (from research doc §5, §8) ───────────────
REVENUE_BANDS = {
    "youtube": 500,
    "distributor": 200,
    "songtradr": 800,
    "audiosparx": 800,
    "itch.io": 300,
    "unity-asset-store": 300,
    "gamedev-market": 300,
    "patreon": 100,
    "ko-fi": 100,
    "own-site": 400,
    "loudly": 150,
    "soundraw": 150,
    "musicapi": 150,
}

# ── Banned surfaces (from RULINGS.md + architecture §10.3) ─────────────────
BANNED_SURFACES = {
    "pond5", "audiojungle", "envato", "artlist", "epidemic-sound",
    "soundstripe", "premiumbeat", "musicbed", "bandcamp", "beatport", "cd-baby",
}

# ── Card identity ───────────────────────────────────────────────────────────
# The board this oracle emits to, and the title grammar every card carries.
# BOTH live here: the dedupe guard parses the titles create_kanban_card writes,
# so the two must never drift apart.
BOARD = "music"
CARD_TITLE_PREFIX = "music-oracle: "

# Statuses that mean "this card is still in flight". A card in one of these
# states already owns the genre's stage chain; a second card for the same
# genre duplicates that whole chain.
OPEN_STATUSES = frozenset({
    "triage", "todo", "scheduled", "ready", "running", "blocked", "review",
})


def card_title(genre: str, total: float) -> str:
    """The title of the card for a genre. Single source of truth."""
    return f"{CARD_TITLE_PREFIX}{genre} (score {total})"


def genre_from_title(title: str) -> str | None:
    """Return the genre named by an oracle card title, else None.

    'music-oracle: chill-lounge (score 8.9)' -> 'chill-lounge'
    Any other title -> None.
    """
    if not title.startswith(CARD_TITLE_PREFIX):
        return None
    rest = title[len(CARD_TITLE_PREFIX):]
    genre = rest.split(" (score ")[0].strip()
    return genre or None


def open_oracle_genres(board: str = BOARD) -> dict[str, str] | None:
    """Map genre -> open card id for every genre already carrying an open card.

    WHY: the oracle runs daily and scores are live (trend_signal does a web
    fetch), so an unguarded run re-creates a card for every genre above the
    threshold. On 2026-10-09 two runs 10 minutes apart produced 28 cards for
    14 genres (performance/music-oracle-runs.log), and each duplicate put a
    whole stage chain in flight.

    Returns None when the board cannot be read. The caller MUST treat None as
    "create nothing" — a failed read must never become duplicate cards.
    """
    cmd = ["hermes", "kanban", "--board", board, "list", "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: cannot list cards on board '{board}': "
              f"{result.stderr.strip() or result.stdout.strip()}", file=sys.stderr)
        return None
    try:
        tasks = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        print(f"ERROR: board '{board}' list --json is not JSON: {exc}", file=sys.stderr)
        return None
    if not isinstance(tasks, list):
        print(f"ERROR: board '{board}' list --json is not a list", file=sys.stderr)
        return None

    open_cards: dict[str, str] = {}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if str(task.get("status", "")) not in OPEN_STATUSES:
            continue
        genre = genre_from_title(str(task.get("title", "")))
        if genre and genre not in open_cards:
            open_cards[genre] = str(task.get("id", ""))
    return open_cards


def load_quota() -> dict:
    """Load the quota ledger."""
    data = json.loads((MUSIC_DIR / "quota-ledger.json").read_text())
    return data


def load_registry() -> dict:
    """Load genre + lane registry via music/registry.py."""
    result = subprocess.run(
        [sys.executable, str(MUSIC_DIR / "registry.py"), "validate"],
        capture_output=True, text=True, cwd=str(REPO)
    )
    if result.returncode != 0:
        print(f"ERROR: registry validation failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(2)

    genres_doc = yaml.safe_load((MUSIC_DIR / "genres.yaml").read_text())
    lanes_doc = yaml.safe_load((MUSIC_DIR / "lanes.yaml").read_text())
    return {"genres": genres_doc["genres"], "lanes": lanes_doc["lanes"]}


def quota_headroom_score(quota: dict) -> float:
    """Score 0-10 based on remaining quota headroom."""
    used = quota["standard_downloads_used"]
    hard_stop = quota["hard_stop_at"]
    if hard_stop == 0:
        return 10.0
    score = 10.0 * (1.0 - used / hard_stop)
    return max(0.0, min(10.0, score))


def lane_coverage_score(genre_lanes: list, lanes: dict) -> float:
    """Score 0-10 based on how many viable (non-banned) lanes the genre opens."""
    viable = 0
    banned = 0
    for lane_name in genre_lanes:
        lane = lanes.get(lane_name, {})
        surface = lane.get("surface", "")
        is_banned = any(b in surface for b in BANNED_SURFACES)
        if is_banned:
            banned += 1
        else:
            viable += 1
    score = min(viable * 2, 10) - (banned * 2)
    return max(0.0, min(10.0, score))


def revenue_potential_score(genre_lanes: list, lanes: dict) -> float:
    """Score 0-10 based on revenue potential of the genre's lanes."""
    total = 0
    for lane_name in genre_lanes:
        lane = lanes.get(lane_name, {})
        surface = lane.get("surface", "")
        for s in surface.split(","):
            s = s.strip()
            for prefix, value in REVENUE_BANDS.items():
                if prefix in s:
                    total += value
                    break
    score = min(total / 200, 10.0)
    return max(0.0, min(10.0, score))


def cadence_fit_score(cadence_str: str) -> float:
    """Score 0-10 based on cadence vs remaining days in the quota period."""
    match = re.match(r"(\d+)/wk", cadence_str)
    if not match:
        return 5.0
    per_week = int(match.group(1))

    quota = load_quota()
    period = quota.get("period", "")
    days_remaining = 15
    if period:
        try:
            period_year, period_month = period.split("-")
            period_year = int(period_year)
            period_month = int(period_month)
            if period_month == 12:
                last_day = datetime(period_year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(period_year, period_month + 1, 1) - timedelta(days=1)
            today = datetime.now()
            days_remaining = (last_day - today).days
        except (ValueError, IndexError):
            days_remaining = 15

    weeks_remaining = max(days_remaining / 7, 0.5)
    expected_tracks = per_week * weeks_remaining

    if expected_tracks >= 8:
        return 10.0
    elif expected_tracks < 2:
        return 0.0
    else:
        return (expected_tracks - 2) / 6.0 * 10.0


def policy_risk_score(genre_lanes: list, lanes: dict) -> float:
    """Score 0-10 based on platform policy risk."""
    risk = 0
    for lane_name in genre_lanes:
        lane = lanes.get(lane_name, {})
        surface = lane.get("surface", "")
        for banned in BANNED_SURFACES:
            if banned in surface:
                risk += 5
    for lane_name in genre_lanes:
        if lane_name in ("youtube-gaming", "youtube-mix"):
            risk += 1
    score = 10.0 - risk
    return max(0.0, min(10.0, score))


# The trend component's floor: "fetched fine, observed no signal". A fetch that
# FAILS must score the same. The score is a property of the genre, not of the
# network. Until 2026-10-16 the except branch below returned 5.0 while this
# state returned 3.0, so every BROKEN run scored 0.2 ABOVE the working run on
# the 10-point total — and the higher-scoring card of each twin pair was the
# one whose web fetch broke (28 cards for 14 genres, card t_bf0e5edd).
# Regression checks: music/scripts/check_oracle_determinism.py (component),
# music/scripts/check_oracle_board.py (one open card per genre).
TREND_NO_SIGNAL = 3.0


def trend_signal_score(genre_name: str) -> float:
    """Score 0-10 based on external trend signals (web search).

    Three fetch outcomes, and none of them may outscore a working fetch:
    200 with >=5 snippets -> 10.0, 200 with 0 snippets -> TREND_NO_SIGNAL,
    200 with some snippets -> proportional, fetch raises -> TREND_NO_SIGNAL.
    """
    try:
        query = f"{genre_name} music trend 2026"
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        results = re.findall(r'class="result__snippet"', html)
        count = len(results)
        if count >= 5:
            return 10.0
        elif count == 0:
            return TREND_NO_SIGNAL
        else:
            return TREND_NO_SIGNAL + (count / 5.0) * 7.0
    except Exception as exc:
        # A failed probe is degraded signal, not a bonus. Report it so the
        # failure is visible in the journal, and score it as no signal.
        print(f"  warn: trend fetch failed for {genre_name} ({exc!r}); scoring it "
              f"as no signal ({TREND_NO_SIGNAL})", file=sys.stderr)
        return TREND_NO_SIGNAL


def score_genre(genre_name: str, genre_spec: dict, lanes: dict, quota: dict) -> dict:
    """Score a single genre. Returns dict with component scores and total."""
    genre_lanes = genre_spec.get("lanes", [])
    if isinstance(genre_lanes, str):
        genre_lanes = [genre_lanes]

    scores = {
        "quota_headroom": quota_headroom_score(quota),
        "lane_coverage": lane_coverage_score(genre_lanes, lanes),
        "revenue_potential": revenue_potential_score(genre_lanes, lanes),
        "cadence_fit": cadence_fit_score(genre_spec.get("cadence", "1/wk")),
        "policy_risk": policy_risk_score(genre_lanes, lanes),
        "trend_signal": trend_signal_score(genre_name),
    }

    total = sum(scores[k] * WEIGHTS[k] for k in scores)
    total = round(total, 2)

    return {
        "genre": genre_name,
        "scores": scores,
        "total": total,
        "lanes": genre_lanes,
        "cadence": genre_spec.get("cadence", ""),
        "family": genre_spec.get("family", ""),
    }


def genre_resume_stage(genre: str) -> tuple[str, str]:
    """(stage, note): the stage a new card for `genre` must start at.

    Delegates to music/stage_state.py, which walks the order declared by
    music/stages.yaml and stops at the first stage with no artifact on disk, so
    this emitter carries no stage list of its own (card t_6599927d).
    """
    stage, evidence = stage_state.resume_stage(REPO, genre)
    return stage, stage_state.resume_note(stage, evidence)


def create_kanban_card(score_data: dict, dry_run: bool = False,
                       skip_genres: dict | None = None,
                       resume_stage: str | None = None,
                       resume_note: str | None = None) -> str | None:
    """Create a scored card on the music board.

    skip_genres: genre -> open card id for genres that already carry an OPEN
    card. A genre in this mapping is skipped — one open card owns a genre's
    stage chain (see open_oracle_genres).

    resume_stage / resume_note: where the genre's chain actually stands, from
    genre_resume_stage(). Given neither, this function resolves them itself.
    """
    if score_data["total"] < 5.0:
        return None

    genre = score_data["genre"]
    total = score_data["total"]
    scores = score_data["scores"]
    lanes = score_data["lanes"]
    cadence = score_data["cadence"]

    if skip_genres and genre in skip_genres:
        print(f"  skip: {genre} already has an open card ({skip_genres[genre]})")
        return None

    if resume_stage is None:
        resume_stage, resume_note = genre_resume_stage(genre)

    title = card_title(genre, total)
    body = f"""# Music Oracle Card — {genre}

**Score:** {total}/10
**Cadence:** {cadence}
**Lanes:** {', '.join(lanes)}
**Family:** {score_data['family']}

## Score Breakdown

| Component | Score | Weight |
|---|---|---|
| Quota Headroom | {scores['quota_headroom']:.1f} | {WEIGHTS['quota_headroom']} |
| Lane Coverage | {scores['lane_coverage']:.1f} | {WEIGHTS['lane_coverage']} |
| Revenue Potential | {scores['revenue_potential']:.1f} | {WEIGHTS['revenue_potential']} |
| Cadence Fit | {scores['cadence_fit']:.1f} | {WEIGHTS['cadence_fit']} |
| Policy Risk | {scores['policy_risk']:.1f} | {WEIGHTS['policy_risk']} |
| Trend Signal | {scores['trend_signal']:.1f} | {WEIGHTS['trend_signal']} |

## Action

This genre scored {total}/10 — above the 5.0 threshold for production.

**Resume at `{resume_stage}`.** {resume_note}

**Next step:** Route to the pipeline driver. The oracle emits; the driver dispatches.

stage: {resume_stage}
"""

    if dry_run:
        print(f"  [DRY RUN] Would create card: {title}")
        print(f"           resume at: {resume_stage} — {resume_note}")
        print(f"           Body: {body[:200]}...")
        return None

    # --board is a TOP-LEVEL flag (hermes kanban --board music create ...),
    # not a create-subcommand flag. Body goes through --body-file so embedded
    # newlines survive shell quoting.
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(body)
        body_path = f.name

    try:
        # title is a POSITIONAL arg for `hermes kanban create`, not --title.
        cmd = [
            "hermes", "kanban", "--board", BOARD, "create",
            title,
            "--body-file", body_path,
            "--assignee", "music-producer",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: failed to create card: {result.stderr}", file=sys.stderr)
            return None

        output = result.stdout.strip()
        # hermes kanban create prints the task id as the last line
        task_id = output.split("\n")[-1].strip()
        print(f"  Created card: {task_id} — {title}")
        return task_id
    finally:
        import os
        try:
            os.unlink(body_path)
        except OSError:
            pass


def run_oracle(dry_run: bool = False) -> dict:
    """Run the full oracle scan. Returns summary dict."""
    print("=== Music Oracle Run ===")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    quota = load_quota()
    print(f"Quota: {quota['standard_downloads_used']}/{quota['standard_downloads_limit']} standard, "
          f"hard_stop at {quota['hard_stop_at']}")
    print()

    registry = load_registry()
    genres = registry["genres"]
    lanes = registry["lanes"]
    print(f"Registry: {len(genres)} genres, {len(lanes)} lanes")
    print()

    results = []
    for genre_name, genre_spec in sorted(genres.items()):
        score_data = score_genre(genre_name, genre_spec, lanes, quota)
        results.append(score_data)
        print(f"  {genre_name}: {score_data['total']}/10")

    results.sort(key=lambda x: x["total"], reverse=True)

    # ── Stage positioning (card t_6599927d) ─────────────────────────────────
    # The body marker is the card's route: this emitter used to write
    # `stage: brief` unconditionally, so a re-emitted card re-entered the brief
    # stage for a genre whose brief was already on disk. Resolve every genre's
    # resume stage BEFORE creating anything, and fail closed exactly like an
    # unreadable board — a card positioned at a delivered stage spends a whole
    # worker run re-doing work that already exists.
    resume_ok = True
    positioned: list[str] = []
    for r in results:
        if r["total"] < 5.0:
            continue
        try:
            r["resume_stage"], r["resume_note"] = genre_resume_stage(r["genre"])
        except Exception as exc:  # noqa: BLE001 — any failure here means NO cards
            print(f"ERROR: cannot resolve the resume stage for {r['genre']}: "
                  f"{type(exc).__name__}: {exc} — creating NO cards "
                  f"(a card at the wrong stage burns a run; card t_6599927d).",
                  file=sys.stderr)
            resume_ok = False
            break
        positioned.append(f"{r['genre']}={r['resume_stage']}")

    print()
    print("=== Creating Cards (score >= 5.0) ===")
    if resume_ok:
        print("Resume stages (music/stage_state.py, order from music/stages.yaml):")
        for item in positioned:
            print(f"  {item}")
    else:
        print("Resume stages: UNRESOLVED — no cards will be created.")

    # Dedupe: one OPEN card per genre. Without this guard a second run
    # re-creates a card for every genre above the threshold and puts a whole
    # second stage chain in flight (2026-10-09: 28 cards for 14 genres).
    open_cards = open_oracle_genres(BOARD) if not dry_run else {}
    board_read_ok = open_cards is not None
    if not board_read_ok:
        print("ERROR: the board could not be read — creating NO cards "
              "(a failed read must never become duplicate cards).", file=sys.stderr)
        open_cards = {}
    else:
        print(f"Open oracle cards on board '{BOARD}': {len(open_cards)} genre(s)")

    created = []
    skipped = []
    for r in results:
        # Fail closed: with no readable board, or no resolvable resume stage, we
        # cannot position a card correctly — so no card may be created.
        if not board_read_ok or not resume_ok:
            break
        card_id = create_kanban_card(r, dry_run=dry_run, skip_genres=open_cards,
                                     resume_stage=r["resume_stage"],
                                     resume_note=r["resume_note"])
        if card_id:
            created.append(card_id)
        elif not dry_run and r["genre"] in open_cards:
            skipped.append(r["genre"])

    summary = {
        "timestamp": datetime.now().isoformat(),
        "quota_used": quota["standard_downloads_used"],
        "quota_limit": quota["standard_downloads_limit"],
        "genres_scored": len(results),
        "cards_created": len(created),
        "created_ids": created,
        "skipped_existing": skipped,
        "board_read_ok": board_read_ok,
        "resume_ok": resume_ok,
        "resume_by_genre": {r["genre"]: r.get("resume_stage") for r in results
                            if r["total"] >= 5.0},
        "top_genre": results[0]["genre"] if results else None,
        "top_score": results[0]["total"] if results else 0,
    }

    print()
    print(f"=== Oracle Complete ===")
    print(f"Genres scored: {summary['genres_scored']}")
    print(f"Cards created: {summary['cards_created']}")
    print(f"Cards skipped (genre already open): {len(summary['skipped_existing'])}")
    print(f"Top genre: {summary['top_genre']} ({summary['top_score']}/10)")
    if not resume_ok:
        print("Resume stages UNRESOLVED — the run created nothing.", file=sys.stderr)

    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Music opportunity oracle")
    parser.add_argument("--dry-run", action="store_true", help="Score without creating cards")
    args = parser.parse_args()

    summary = run_oracle(dry_run=args.dry_run)

    log_path = PERF_DIR / "music-oracle-runs.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"{summary['timestamp']} — oracle run: "
                f"{summary['genres_scored']} scored, "
                f"{summary['cards_created']} created, "
                f"{len(summary['skipped_existing'])} skipped (open), "
                f"board_read_ok={summary['board_read_ok']}, "
                f"resume_ok={summary['resume_ok']}, "
                f"top={summary['top_genre']}({summary['top_score']})\n")

    # Fail loud: if the board could not be read, or a genre's resume stage could
    # not be resolved, no cards were created. That is a broken run, not a quiet
    # success (card t_6599927d added the second cause).
    if not summary["board_read_ok"] or not summary["resume_ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()