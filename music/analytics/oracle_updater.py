"""Oracle weight updater — feeds ROI results back into genre registry cadence.

A genre that earns gets more cadence. One that doesn't gets paused.
This is an oracle-style weight update: it proposes changes to genres.yaml
cadence values based on measured ROI, but does NOT apply them without
human approval (RULINGS.md rule: proposed playbook changes wait for approval).

Weight formula:
  - revenue_per_1k_streams > $3.00 → cadence +1 (max 7/wk)
  - revenue_per_1k_streams $1.00-$3.00 → cadence unchanged
  - revenue_per_1k_streams < $1.00 → cadence -1 (min 0/wk = paused)
  - unmeasured tracks → no change (insufficient data)
  - under_threshold tracks → flag for review, no cadence change
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

from .track_record import TrackRegistry
from .roi_calculator import compute_roi_summary


def parse_cadence(cadence_str: str) -> int:
    """Parse '3/wk' -> 3."""
    m = re.match(r"(\d+)/wk", cadence_str)
    if not m:
        raise ValueError(f"Cannot parse cadence: {cadence_str}")
    return int(m.group(1))


def format_cadence(n: int) -> str:
    """Format 3 -> '3/wk'."""
    return f"{n}/wk"


def compute_oracle_updates(registry: TrackRegistry) -> list[dict]:
    """Compute proposed cadence updates based on ROI.

    Returns:
        list of {
            "genre": str,
            "current_cadence": str,
            "proposed_cadence": str,
            "reason": str,
            "evidence": dict,
            "action": "increase|decrease|pause|hold"
        }
    """
    summary = compute_roi_summary(registry)
    updates = []

    for genre, roi in summary["by_genre"].items():
        if roi["measured_count"] == 0:
            updates.append({
                "genre": genre,
                "current_cadence": "unknown",
                "proposed_cadence": "unknown",
                "reason": "no measured tracks — insufficient data",
                "evidence": {"measured_count": 0, "total_tracks": roi["track_count"]},
                "action": "hold",
            })
            continue

        rpk = roi.get("revenue_per_1k_streams")
        if rpk is None:
            updates.append({
                "genre": genre,
                "current_cadence": "unknown",
                "proposed_cadence": "unknown",
                "reason": "no streams measured",
                "evidence": roi,
                "action": "hold",
            })
            continue

        # Get current cadence from genres.yaml
        current = _get_genre_cadence(genre)
        if current is None:
            current_str = "unknown"
            current_n = 0
        else:
            current_str = format_cadence(current)
            current_n = current

        if rpk >= 3.0:
            proposed_n = min(current_n + 1, 7)
            action = "increase"
            reason = f"revenue/1k streams ${rpk:.2f} >= $3.00 threshold"
        elif rpk >= 1.0:
            proposed_n = current_n
            action = "hold"
            reason = f"revenue/1k streams ${rpk:.2f} in $1.00-$3.00 band"
        else:
            proposed_n = max(current_n - 1, 0)
            action = "decrease" if proposed_n > 0 else "pause"
            reason = f"revenue/1k streams ${rpk:.2f} < $1.00 threshold"

        updates.append({
            "genre": genre,
            "current_cadence": current_str,
            "proposed_cadence": format_cadence(proposed_n),
            "reason": reason,
            "evidence": roi,
            "action": action,
        })

    return updates


def _get_genre_cadence(genre: str) -> Optional[int]:
    """Read current cadence from genres.yaml."""
    genres_path = Path(__file__).resolve().parents[2] / "music" / "genres.yaml"
    if not genres_path.is_file():
        return None
    doc = yaml.safe_load(genres_path.read_text(encoding="utf-8"))
    if not doc or "genres" not in doc:
        return None
    entry = doc["genres"].get(genre)
    if not entry:
        return None
    return parse_cadence(entry.get("cadence", "0/wk"))


def apply_oracle_updates(updates: list[dict], dry_run: bool = True) -> dict:
    """Apply or simulate cadence updates to genres.yaml.

    Args:
        updates: from compute_oracle_updates()
        dry_run: if True, only report what would change

    Returns:
        dict with: applied, skipped, changes
    """
    genres_path = Path(__file__).resolve().parents[2] / "music" / "genres.yaml"
    if not genres_path.is_file():
        return {"applied": 0, "skipped": len(updates), "changes": [],
                "error": "genres.yaml not found"}

    doc = yaml.safe_load(genres_path.read_text(encoding="utf-8"))
    changes = []

    for upd in updates:
        genre = upd["genre"]
        if genre not in doc.get("genres", {}):
            continue

        old_cadence = doc["genres"][genre].get("cadence", "unknown")
        new_cadence = upd["proposed_cadence"]

        if old_cadence == new_cadence:
            continue

        change = {
            "genre": genre,
            "old": old_cadence,
            "new": new_cadence,
            "action": upd["action"],
            "reason": upd["reason"],
        }

        if not dry_run:
            doc["genres"][genre]["cadence"] = new_cadence

        changes.append(change)

    if not dry_run and changes:
        genres_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    return {
        "applied": len(changes) if not dry_run else 0,
        "skipped": len(updates) - len(changes),
        "changes": changes,
        "dry_run": dry_run,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python3 -m music.analytics.oracle_updater <registry.json> [--apply]")
        return 2

    registry_path = Path(argv[1])
    if not registry_path.is_file():
        print(f"FAILED: registry not found: {registry_path}")
        return 1

    dry_run = "--apply" not in argv

    registry = TrackRegistry(registry_path)
    if not registry.tracks:
        print(f"FAILED: no tracks in registry: {registry_path}")
        return 1

    updates = compute_oracle_updates(registry)
    result = apply_oracle_updates(updates, dry_run=dry_run)

    print(f"Oracle weight update ({'DRY RUN' if dry_run else 'APPLIED'}):")
    print(f"  Genres evaluated: {len(updates)}")
    print(f"  Changes proposed: {len(result['changes'])}")
    print(f"  Skipped: {result['skipped']}")

    for change in result["changes"]:
        print(f"  {change['genre']}: {change['old']} → {change['new']} "
              f"({change['action']}) — {change['reason']}")

    if dry_run and result["changes"]:
        print("\n  Re-run with --apply to write changes to genres.yaml")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
