"""Track record data model for lane ROI analytics.

Each track record holds:
  - track metadata (id, title, genre, lane, campaign)
  - generation cost (credits, hours)
  - performance metrics (streams, revenue, views, retention)
  - derived ROI metrics

A track record with no performance data is NOT a zero-earning track.
It is an UNKNOWN track. The system must distinguish these.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class TrackRecord:
    """One track's full lifecycle data."""

    track_id: str
    title: str
    genre: str
    lane: str
    campaign: str = ""

    # Generation cost
    credits_used: int = 0
    generation_hours: float = 0.0
    studio_exports: int = 0

    # Performance — None means "not measured", NOT zero
    streams: Optional[int] = None
    revenue_usd: Optional[float] = None
    youtube_views: Optional[int] = None
    youtube_revenue_usd: Optional[float] = None
    retention_30s: Optional[float] = None  # 0.0-1.0
    ctr: Optional[float] = None  # 0.0-1.0

    # Source tracking
    sources: dict = field(default_factory=dict)
    # e.g. {"distrokid_tsv": "path/to/file.tsv", "youtube_api": "queried 2026-10-09"}

    # Flags
    is_exported: bool = False
    is_published: bool = False
    human_gate_pending: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TrackRecord":
        return cls(**data)

    @property
    def is_measured(self) -> bool:
        """True if at least one performance metric has been measured."""
        return any(v is not None for v in [
            self.streams, self.revenue_usd,
            self.youtube_views, self.youtube_revenue_usd
        ])

    @property
    def is_under_threshold(self) -> bool:
        """True if streams are known and under 1,000 (Spotify pays nothing)."""
        if self.streams is None:
            return False
        return self.streams < 1000

    @property
    def effective_revenue(self) -> float:
        """Total revenue from all measured sources. Unknown = 0.0 (not false)."""
        total = 0.0
        if self.revenue_usd is not None:
            total += self.revenue_usd
        if self.youtube_revenue_usd is not None:
            total += self.youtube_revenue_usd
        return total

    @property
    def revenue_per_1k_streams(self) -> Optional[float]:
        """Revenue per 1,000 streams. None if streams unknown or zero."""
        if self.streams is None or self.streams == 0:
            return None
        return (self.effective_revenue / self.streams) * 1000

    @property
    def revenue_per_credit(self) -> Optional[float]:
        """Revenue per Suno credit. None if credits unknown."""
        if self.credits_used == 0:
            return None
        return self.effective_revenue / self.credits_used

    @property
    def revenue_per_hour(self) -> Optional[float]:
        """Revenue per generation hour. None if hours unknown."""
        if self.generation_hours == 0:
            return None
        return self.effective_revenue / self.generation_hours


class TrackRegistry:
    """Collection of track records, persisted to JSON."""

    def __init__(self, path: Path):
        self.path = path
        self.tracks: dict[str, TrackRecord] = {}
        self._load()

    def _load(self):
        if self.path.is_file():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for tid, tdata in data.get("tracks", {}).items():
                self.tracks[tid] = TrackRecord.from_dict(tdata)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "tracks": {tid: t.to_dict() for tid, t in self.tracks.items()}
        }
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def add(self, track: TrackRecord):
        self.tracks[track.track_id] = track

    def get(self, track_id: str) -> Optional[TrackRecord]:
        return self.tracks.get(track_id)

    def by_genre(self, genre: str) -> list[TrackRecord]:
        return [t for t in self.tracks.values() if t.genre == genre]

    def by_lane(self, lane: str) -> list[TrackRecord]:
        return [t for t in self.tracks.values() if t.lane == lane]

    def all(self) -> list[TrackRecord]:
        return list(self.tracks.values())
