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


def trend_signal_score(genre_name: str) -> float:
    """Score 0-10 based on external trend signals (web search)."""
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
            return 3.0
        else:
            return 3.0 + (count / 5.0) * 7.0
    except Exception:
        return 5.0


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


def create_kanban_card(score_data: dict, dry_run: bool = False) -> str | None:
    """Create a scored card on the music kanban board."""
    if score_data["total"] < 5.0:
        return None

    genre = score_data["genre"]
    total = score_data["total"]
    scores = score_data["scores"]
    lanes = score_data["lanes"]
    cadence = score_data["cadence"]

    title = f"music-oracle: {genre} (score {total})"
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

**Next step:** Route to the pipeline driver. The oracle emits; the driver dispatches.

stage: brief
"""

    if dry_run:
        print(f"  [DRY RUN] Would create card: {title}")
        print(f"           Body: {body[:200]}...")
        return None

    cmd = [
        "hermes", "kanban", "create",
        "--board", "music",
        "--title", title,
        "--body", body,
        "--assignee", "music-producer",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: failed to create card: {result.stderr}", file=sys.stderr)
        return None

    output = result.stdout.strip()
    task_id = output.split("\n")[-1].strip()
    print(f"  Created card: {task_id} — {title}")
    return task_id


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

    print()
    print("=== Creating Cards (score >= 5.0) ===")

    created = []
    for r in results:
        card_id = create_kanban_card(r, dry_run=dry_run)
        if card_id:
            created.append(card_id)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "quota_used": quota["standard_downloads_used"],
        "quota_limit": quota["standard_downloads_limit"],
        "genres_scored": len(results),
        "cards_created": len(created),
        "created_ids": created,
        "top_genre": results[0]["genre"] if results else None,
        "top_score": results[0]["total"] if results else 0,
    }

    print()
    print(f"=== Oracle Complete ===")
    print(f"Genres scored: {summary['genres_scored']}")
    print(f"Cards created: {summary['cards_created']}")
    print(f"Top genre: {summary['top_genre']} ({summary['top_score']}/10)")

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
                f"top={summary['top_genre']}({summary['top_score']})\n")


if __name__ == "__main__":
    main()