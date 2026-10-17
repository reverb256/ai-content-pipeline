"""Weekly music digest generator.

Produces a markdown digest covering:
  - What shipped (new tracks published this week)
  - What earned (revenue, streams, ROI by genre and lane)
  - What is stuck on a human gate
  - Oracle weight update proposals
  - Anti-pattern exposure (under-threshold tracks paying $0)

Output: music/analytics/digest-<date>.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .track_record import TrackRegistry
from .roi_calculator import compute_roi_summary
from .oracle_updater import compute_oracle_updates


def generate_digest(registry: TrackRegistry, output_dir: Path) -> Path:
    """Generate the weekly digest markdown file.

    Returns:
        Path to the generated digest file.
    """
    summary = compute_roi_summary(registry)
    updates = compute_oracle_updates(registry)

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    lines = [
        f"# Music Digest — {today}",
        "",
        f"**Period:** {week_ago} to {today}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Total tracks:** {summary['summary']['total_tracks']}",
        f"- **Measured:** {summary['summary']['measured_tracks']}",
        f"- **Unmeasured:** {summary['summary']['unmeasured_tracks']}",
        f"- **Total streams:** {summary['summary']['total_streams']:,}",
        f"- **Total revenue:** ${summary['summary']['total_revenue_usd']:.2f}",
        f"- **Under-threshold tracks (pay $0):** {summary['summary']['under_threshold_tracks']}",
        "",
    ]

    # Anti-pattern exposure
    under_threshold = [t for t in registry.all()
                       if t.is_measured and t.is_under_threshold]
    if under_threshold:
        lines.extend([
            "## Anti-Pattern: Spraying Tracks With No Campaign",
            "",
            f"**{len(under_threshold)} tracks** are under 1,000 streams and pay $0.",
            "This is the failure mode: volume without campaign earns nothing.",
            "",
        ])
        for t in under_threshold:
            lines.append(f"- **{t.title}** ({t.genre}×{t.lane}): "
                        f"{t.streams} streams, ${t.effective_revenue:.2f}")
        lines.append("")

    # By genre
    lines.extend([
        "## Revenue by Genre",
        "",
        "| Genre | Tracks | Streams | Revenue | $/1k streams | $/credit | Action |",
        "|-------|--------|---------|---------|--------------|----------|--------|",
    ])
    for genre, roi in sorted(summary["by_genre"].items()):
        rpk = f"${roi['revenue_per_1k_streams']:.2f}" if roi.get("revenue_per_1k_streams") else "N/A"
        rpc = f"${roi['revenue_per_credit']:.4f}" if roi.get("revenue_per_credit") else "N/A"
        action = "—"
        for u in updates:
            if u["genre"] == genre and u["action"] != "hold":
                action = u["action"]
        lines.append(
            f"| {genre} | {roi['track_count']} | {roi['total_streams']:,} | "
            f"${roi['total_revenue_usd']:.2f} | {rpk} | {rpc} | {action} |"
        )
    lines.append("")

    # By lane
    lines.extend([
        "## Revenue by Lane",
        "",
        "| Lane | Tracks | Streams | Revenue | $/1k streams |",
        "|-------|--------|---------|---------|--------------|",
    ])
    for lane, roi in sorted(summary["by_lane"].items()):
        rpk = f"${roi['revenue_per_1k_streams']:.2f}" if roi.get("revenue_per_1k_streams") else "N/A"
        lines.append(
            f"| {lane} | {roi['track_count']} | {roi['total_streams']:,} | "
            f"${roi['total_revenue_usd']:.2f} | {rpk} |"
        )
    lines.append("")

    # Oracle proposals
    changes = [u for u in updates if u["action"] != "hold"]
    if changes:
        lines.extend([
            "## Oracle Weight Proposals",
            "",
            "Cadence changes proposed based on measured ROI. "
            "Require human approval before applying.",
            "",
            "| Genre | Current | Proposed | Reason |",
            "|-------|---------|----------|--------|",
        ])
        for u in changes:
            lines.append(
                f"| {u['genre']} | {u['current_cadence']} | "
                f"{u['proposed_cadence']} | {u['reason']} |"
            )
        lines.append("")
    else:
        lines.extend([
            "## Oracle Weight Proposals",
            "",
            "No cadence changes proposed. All genres are either "
            "performing within the hold band or have insufficient data.",
            "",
        ])

    # Human gate pending
    pending = [t for t in registry.all() if t.human_gate_pending]
    if pending:
        lines.extend([
            "## Stuck on Human Gate",
            "",
        ])
        for t in pending:
            lines.append(f"- **{t.title}** ({t.genre}×{t.lane}) — awaiting approval")
        lines.append("")

    # Unmeasured tracks
    unmeasured = [t for t in registry.all() if not t.is_measured]
    if unmeasured:
        lines.extend([
            "## Unmeasured Tracks",
            "",
            "These tracks have no performance data. They are NOT zero-earning. "
            "They are unknown.",
            "",
        ])
        for t in unmeasured:
            lines.append(f"- **{t.title}** ({t.genre}×{t.lane}) — no data")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Data Sources",
        "",
    ])
    # Collect all sources
    sources = set()
    for t in registry.all():
        for src in t.sources.values():
            sources.add(src)
    if sources:
        for s in sorted(sources):
            lines.append(f"- {s}")
    else:
        lines.append("- No data sources recorded")

    lines.append("")

    # Write
    output_dir.mkdir(parents=True, exist_ok=True)
    digest_path = output_dir / f"digest-{today}.md"
    digest_path.write_text("\n".join(lines), encoding="utf-8")
    return digest_path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python3 -m music.analytics.digest <registry.json> [output_dir]")
        return 2

    registry_path = Path(argv[1])
    if not registry_path.is_file():
        print(f"FAILED: registry not found: {registry_path}")
        return 1

    output_dir = Path(argv[2]) if len(argv) > 2 else Path(__file__).resolve().parent

    registry = TrackRegistry(registry_path)
    if not registry.tracks:
        print(f"FAILED: no tracks in registry: {registry_path}")
        return 1

    digest_path = generate_digest(registry, output_dir)
    print(f"Digest written to: {digest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
