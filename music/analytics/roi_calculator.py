"""ROI calculator — computes per-genre and per-lane ROI metrics.

Anti-pattern exposed: spraying tracks with no campaign earns ~$0.
Under ~1,000 streams in a rolling 12 months, Spotify pays nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from .track_record import TrackRecord, TrackRegistry


def compute_genre_roi(tracks: list[TrackRecord]) -> dict:
    """Aggregate ROI metrics for a genre.

    Returns:
        dict with: genre, track_count, total_streams, total_revenue,
        revenue_per_1k_streams, revenue_per_credit, revenue_per_hour,
        measured_count, unmeasured_count, under_threshold_count
    """
    measured = [t for t in tracks if t.is_measured]
    unmeasured = [t for t in tracks if not t.is_measured]
    under_threshold = [t for t in measured if t.is_under_threshold]

    total_streams = sum(t.streams or 0 for t in measured)
    total_revenue = sum(t.effective_revenue for t in measured)
    total_credits = sum(t.credits_used for t in tracks)
    total_hours = sum(t.generation_hours for t in tracks)

    return {
        "genre": tracks[0].genre if tracks else "unknown",
        "track_count": len(tracks),
        "measured_count": len(measured),
        "unmeasured_count": len(unmeasured),
        "under_threshold_count": len(under_threshold),
        "total_streams": total_streams,
        "total_revenue_usd": round(total_revenue, 2),
        "revenue_per_1k_streams": round((total_revenue / total_streams) * 1000, 4)
            if total_streams > 0 else None,
        "revenue_per_credit": round(total_revenue / total_credits, 4)
            if total_credits > 0 else None,
        "revenue_per_hour": round(total_revenue / total_hours, 4)
            if total_hours > 0 else None,
        "avg_retention_30s": round(
            sum(t.retention_30s or 0 for t in measured) / len(measured), 4
        ) if measured else None,
        "avg_ctr": round(
            sum(t.ctr or 0 for t in measured if t.ctr is not None) /
            len([t for t in measured if t.ctr is not None]), 4
        ) if any(t.ctr is not None for t in measured) else None,
    }


def compute_lane_roi(tracks: list[TrackRecord]) -> dict:
    """Aggregate ROI metrics for a lane."""
    return compute_genre_roi(tracks)  # Same logic, different grouping key


def compute_roi_summary(registry: TrackRegistry) -> dict:
    """Full ROI summary across all tracks, grouped by genre and lane."""
    all_tracks = registry.all()

    # By genre
    genres = {}
    for t in all_tracks:
        genres.setdefault(t.genre, []).append(t)
    genre_roi = {g: compute_genre_roi(ts) for g, ts in genres.items()}

    # By lane
    lanes = {}
    for t in all_tracks:
        lanes.setdefault(t.lane, []).append(t)
    lane_roi = {l: compute_lane_roi(ts) for l, ts in lanes.items()}

    # By genre x lane
    genre_lane = {}
    for t in all_tracks:
        key = f"{t.genre}×{t.lane}"
        genre_lane.setdefault(key, []).append(t)
    genre_lane_roi = {k: compute_genre_roi(ts) for k, ts in genre_lane.items()}

    # Totals
    total_tracks = len(all_tracks)
    measured = [t for t in all_tracks if t.is_measured]
    total_streams = sum(t.streams or 0 for t in measured)
    total_revenue = sum(t.effective_revenue for t in measured)

    return {
        "summary": {
            "total_tracks": total_tracks,
            "measured_tracks": len(measured),
            "unmeasured_tracks": total_tracks - len(measured),
            "total_streams": total_streams,
            "total_revenue_usd": round(total_revenue, 2),
            "under_threshold_tracks": len([t for t in measured if t.is_under_threshold]),
        },
        "by_genre": genre_roi,
        "by_lane": lane_roi,
        "by_genre_lane": genre_lane_roi,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python3 -m music.analytics.roi_calculator <registry.json>")
        return 2

    registry_path = Path(argv[1])
    if not registry_path.is_file():
        print(f"FAILED: registry not found: {registry_path}")
        return 1

    registry = TrackRegistry(registry_path)
    if not registry.tracks:
        print(f"FAILED: no tracks in registry: {registry_path}")
        return 1

    summary = compute_roi_summary(registry)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
