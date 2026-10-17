"""DistroKid TSV report parser.

DistroKid has NO public API (verified 2026-10-09, deepwiki.com/api-evangelist/distrokid).
The only data source is the TSV export from distrokid.com/bank/details/.

TSV format (verified against betterkid parser, DJSethDuncan/betterkid):
  Tab-separated, header row, columns include:
    Track, Artist, Store, Country, Date, Streams, Earnings, etc.

This parser reads the TSV and produces per-track performance records.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Optional


def parse_distrokid_tsv(path: Path) -> dict[str, dict]:
    """Parse a DistroKid TSV earnings report.

    Returns:
        dict mapping track_title -> {
            "streams": int,
            "earnings_usd": float,
            "stores": list[str],
            "countries": list[str],
            "rows": int
        }

    Raises:
        FileNotFoundError: TSV does not exist
        ValueError: TSV is malformed or has no recognizable columns
    """
    if not path.is_file():
        raise FileNotFoundError(f"DistroKid TSV not found: {path}")

    with open(path, encoding="utf-8") as f:
        # DistroKid exports are TSV
        sample = f.read(4096)
        f.seek(0)

        # Detect delimiter (tab is standard, but be robust)
        if "\t" in sample:
            delimiter = "\t"
        else:
            delimiter = ","

        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"DistroKid TSV has no header row: {path}")

        # Normalize header names (strip, lower)
        fieldnames = [fn.strip().lower() for fn in reader.fieldnames]

        # Map common column names
        track_col = _find_col(fieldnames, ["track", "track name", "song", "title"])
        streams_col = _find_col(fieldnames, ["streams", "plays", "stream count"])
        earnings_col = _find_col(fieldnames, ["earnings", "revenue", "amount", "payout"])
        store_col = _find_col(fieldnames, ["store", "platform", "service"])
        country_col = _find_col(fieldnames, ["country", "region"])

        if not track_col:
            raise ValueError(
                f"DistroKid TSV has no recognizable track column. "
                f"Found: {reader.fieldnames}"
            )

        tracks: dict[str, dict] = {}
        for row in reader:
            # Re-map row keys to normalized names
            normalized = {
                fn.strip().lower(): val
                for fn, val in zip(reader.fieldnames, row.values())
            }

            title = normalized.get(track_col, "").strip()
            if not title:
                continue

            if title not in tracks:
                tracks[title] = {
                    "streams": 0,
                    "earnings_usd": 0.0,
                    "stores": set(),
                    "countries": set(),
                    "rows": 0,
                }

            rec = tracks[title]
            rec["rows"] += 1

            if streams_col:
                try:
                    rec["streams"] += int(normalized.get(streams_col, "0").replace(",", ""))
                except (ValueError, TypeError):
                    pass

            if earnings_col:
                try:
                    val = normalized.get(earnings_col, "0").replace(",", "").replace("$", "")
                    rec["earnings_usd"] += float(val)
                except (ValueError, TypeError):
                    pass

            if store_col:
                store = normalized.get(store_col, "").strip()
                if store:
                    rec["stores"].add(store)

            if country_col:
                country = normalized.get(country_col, "").strip()
                if country:
                    rec["countries"].add(country)

        # Convert sets to sorted lists for JSON serialization
        for rec in tracks.values():
            rec["stores"] = sorted(rec["stores"])
            rec["countries"] = sorted(rec["countries"])

        return tracks


def _find_col(fieldnames: list[str], candidates: list[str]) -> Optional[str]:
    """Find the first candidate column name that exists in fieldnames."""
    for cand in candidates:
        if cand in fieldnames:
            return cand
    return None


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python3 -m music.analytics.distrokid_parser <tsv_path>")
        return 2

    path = Path(argv[1])
    try:
        tracks = parse_distrokid_tsv(path)
    except FileNotFoundError as e:
        print(f"FAILED: {e}")
        return 1
    except ValueError as e:
        print(f"FAILED: {e}")
        return 1

    if not tracks:
        print("FAILED: no tracks found in TSV")
        return 1

    print(f"Parsed {len(tracks)} tracks from {path}")
    for title, rec in sorted(tracks.items()):
        print(f"  {title}: {rec['streams']} streams, ${rec['earnings_usd']:.2f}, "
              f"{rec['rows']} rows, stores={rec['stores'][:3]}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
