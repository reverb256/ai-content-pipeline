"""music/analytics — CLI entry point.

Subcommands:
  init              Create a new empty track registry
  import-tsv        Import DistroKid TSV earnings report
  import-youtube    Import YouTube Analytics data
  compute           Compute ROI summary
  oracle            Propose oracle weight updates
  digest            Generate weekly digest
  demo              Run full demo with sample data + FAILED path
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO / "music" / "analytics" / "tracks.json"


def cmd_init(args) -> int:
    registry = DEFAULT_REGISTRY if not args.registry else Path(args.registry)
    if registry.is_file():
        print(f"FAILED: registry already exists: {registry}")
        return 1
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"version": 1, "tracks": {}}, indent=2) + "\n")
    print(f"Created empty registry: {registry}")
    return 0


def cmd_import_tsv(args) -> int:
    from .distrokid_parser import parse_distrokid_tsv
    from .track_record import TrackRecord, TrackRegistry

    tsv_path = Path(args.tsv)
    registry = TrackRegistry(Path(args.registry))

    try:
        tracks = parse_distrokid_tsv(tsv_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"FAILED: {e}")
        return 1

    for title, rec in tracks.items():
        tid = title.lower().replace(" ", "-")[:40]
        existing = registry.get(tid)
        if existing:
            existing.streams = rec["streams"]
            existing.revenue_usd = rec["earnings_usd"]
            existing.sources["distrokid_tsv"] = str(tsv_path)
        else:
            registry.add(TrackRecord(
                track_id=tid,
                title=title,
                genre="unknown",
                lane="streaming",
                streams=rec["streams"],
                revenue_usd=rec["earnings_usd"],
                sources={"distrokid_tsv": str(tsv_path)},
            ))

    registry.save()
    print(f"Imported {len(tracks)} tracks from {tsv_path}")
    return 0


def cmd_import_youtube(args) -> int:
    from .youtube_fetcher import fetch_youtube_metrics
    from .track_record import TrackRecord, TrackRegistry

    registry = TrackRegistry(Path(args.registry))
    try:
        result = fetch_youtube_metrics(
            args.channel_id, args.start_date, args.end_date,
            Path(args.credentials), Path(args.token),
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"FAILED: {e}")
        return 1

    # Update matching tracks or create a channel-level record
    tid = f"youtube-{args.channel_id[:8]}"
    existing = registry.get(tid)
    if existing:
        existing.youtube_views = result["views"]
        existing.youtube_revenue_usd = result["estimated_revenue"]
        existing.retention_30s = result["retention_30s"]
        existing.sources["youtube_api"] = f"queried {args.end_date}"
    else:
        registry.add(TrackRecord(
            track_id=tid,
            title=f"YouTube channel {args.channel_id}",
            genre="unknown",
            lane="youtube-longform",
            youtube_views=result["views"],
            youtube_revenue_usd=result["estimated_revenue"],
            retention_30s=result["retention_30s"],
            sources={"youtube_api": f"queried {args.end_date}"},
        ))

    registry.save()
    print(f"YouTube: {result['views']} views, ${result['estimated_revenue']:.2f}")
    return 0


def cmd_compute(args) -> int:
    from .roi_calculator import compute_roi_summary
    from .track_record import TrackRegistry

    registry = TrackRegistry(Path(args.registry))
    if not registry.tracks:
        print(f"FAILED: no tracks in registry: {args.registry}")
        return 1

    summary = compute_roi_summary(registry)
    print(json.dumps(summary, indent=2))
    return 0


def cmd_oracle(args) -> int:
    from .oracle_updater import compute_oracle_updates, apply_oracle_updates
    from .track_record import TrackRegistry

    registry = TrackRegistry(Path(args.registry))
    if not registry.tracks:
        print(f"FAILED: no tracks in registry: {args.registry}")
        return 1

    updates = compute_oracle_updates(registry)
    result = apply_oracle_updates(updates, dry_run=not args.apply)

    print(f"Oracle weight update ({'APPLIED' if args.apply else 'DRY RUN'}):")
    for change in result["changes"]:
        print(f"  {change['genre']}: {change['old']} → {change['new']} ({change['action']})")
    return 0


def cmd_digest(args) -> int:
    from .digest import generate_digest
    from .track_record import TrackRegistry

    registry = TrackRegistry(Path(args.registry))
    if not registry.tracks:
        print(f"FAILED: no tracks in registry: {args.registry}")
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent
    digest_path = generate_digest(registry, output_dir)
    print(f"Digest: {digest_path}")
    return 0


def cmd_demo(args) -> int:
    """Run full demo: import sample data, compute ROI, generate digest, show FAILED path."""
    from .track_record import TrackRecord, TrackRegistry
    from .roi_calculator import compute_roi_summary
    from .digest import generate_digest

    print("=== MUSIC ANALYTICS DEMO ===")
    print()

    # 1. Create registry with real + sample tracks
    registry = TrackRegistry(Path(args.registry))

    # Real track: reflection-vrchat-erp (Virtual Reflections campaign)
    real_track = TrackRecord(
        track_id="reflection-vrchat-erp",
        title="Reflection — VRChat ERP Intimacy",
        genre="chill-lounge",
        lane="streaming",
        campaign="virtual-reflections",
        credits_used=500,
        generation_hours=2.0,
        studio_exports=1,
        streams=847,
        revenue_usd=0.0,
        youtube_views=12,
        youtube_revenue_usd=0.0,
        retention_30s=0.42,
        ctr=None,
        sources={"local_audio": "campaigns/virtual-reflections/audio/reflection-vrchat-erp.flac"},
        is_exported=True,
        is_published=False,
        human_gate_pending=True,
    )
    registry.add(real_track)

    # Sample earning track (hypothetical but realistic)
    earning_track = TrackRecord(
        track_id="lofi-rain-001",
        title="Rainy Window (lofi mix)",
        genre="chill-lounge",
        lane="youtube-longform",
        campaign="",
        credits_used=500,
        generation_hours=1.5,
        studio_exports=1,
        streams=15420,
        revenue_usd=42.30,
        youtube_views=8900,
        youtube_revenue_usd=18.75,
        retention_30s=0.58,
        ctr=0.034,
        sources={"distrokid_tsv": "sample", "youtube_api": "sample"},
        is_exported=True,
        is_published=True,
    )
    registry.add(earning_track)

    # Sample under-threshold track (the anti-pattern)
    spray_track = TrackRecord(
        track_id="trance-spray-001",
        title="Untitled Trance #47",
        genre="trance",
        lane="streaming",
        campaign="",
        credits_used=500,
        generation_hours=1.0,
        studio_exports=1,
        streams=234,
        revenue_usd=0.0,
        sources={"distrokid_tsv": "sample"},
        is_exported=True,
        is_published=True,
    )
    registry.add(spray_track)

    # Unmeasured track
    unmeasured = TrackRecord(
        track_id="elemental-fire-001",
        title="Elemental Fire (game loop)",
        genre="elemental-fire",
        lane="game-assets",
        credits_used=500,
        generation_hours=1.0,
        studio_exports=1,
        sources={},
        is_exported=False,
        is_published=False,
        human_gate_pending=True,
    )
    registry.add(unmeasured)

    registry.save()
    print(f"Registry: {len(registry.tracks)} tracks")
    print()

    # 2. Compute ROI
    print("--- ROI Summary ---")
    summary = compute_roi_summary(registry)
    print(json.dumps(summary, indent=2))
    print()

    # 3. Generate digest
    print("--- Weekly Digest ---")
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent
    digest_path = generate_digest(registry, output_dir)
    print(f"Digest written to: {digest_path}")
    print()

    # 4. Demonstrate FAILED path
    print("--- FAILED Path Demonstration ---")
    print("Attempting to parse a non-existent DistroKid TSV:")
    from .distrokid_parser import parse_distrokid_tsv
    try:
        parse_distrokid_tsv(Path("/nonexistent/distrokid.tsv"))
    except FileNotFoundError as e:
        print(f"  FAILED: {e}")
        print()

    print("Attempting to fetch YouTube metrics without credentials:")
    from .youtube_fetcher import fetch_youtube_metrics
    try:
        fetch_youtube_metrics("UCxxxx", "2026-01-01", "2026-10-01",
                            Path("/nonexistent/creds.json"), Path("/tmp/token.json"))
    except (FileNotFoundError, RuntimeError) as e:
        print(f"  FAILED: {e}")
        print()

    print("Attempting to compute ROI on empty registry:")
    empty_registry = TrackRegistry(Path(args.registry).parent / "empty.json")
    from .roi_calculator import compute_roi_summary
    if not empty_registry.tracks:
        print("  FAILED: no tracks in registry (empty)")
    print()

    print("=== DEMO COMPLETE ===")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="music/analytics — lane ROI analytics")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY),
                        help="Path to track registry JSON")

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create empty registry").set_defaults(func=cmd_init)

    p_tsv = sub.add_parser("import-tsv", help="Import DistroKid TSV report")
    p_tsv.add_argument("tsv", help="Path to DistroKid TSV file")
    p_tsv.set_defaults(func=cmd_import_tsv)

    p_yt = sub.add_parser("import-youtube", help="Import YouTube Analytics data")
    p_yt.add_argument("channel_id")
    p_yt.add_argument("start_date")
    p_yt.add_argument("end_date")
    p_yt.add_argument("credentials")
    p_yt.add_argument("token", nargs="?")
    p_yt.set_defaults(func=cmd_import_youtube)

    p_compute = sub.add_parser("compute", help="Compute ROI summary")
    p_compute.set_defaults(func=cmd_compute)

    p_oracle = sub.add_parser("oracle", help="Propose oracle weight updates")
    p_oracle.add_argument("--apply", action="store_true")
    p_oracle.set_defaults(func=cmd_oracle)

    p_digest = sub.add_parser("digest", help="Generate weekly digest")
    p_digest.add_argument("--output-dir", default=None)
    p_digest.set_defaults(func=cmd_digest)

    p_demo = sub.add_parser("demo", help="Run full demo with sample data")
    p_demo.add_argument("--output-dir", default=None)
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
