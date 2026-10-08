#!/usr/bin/env python3
"""gate_quota — PASS/FAIL gate over the Suno download/export quota.

Why this gate exists (music-lane-architecture.md §6):
  Suno Premier caps STANDARD downloads at 60/month. STUDIO exports
  are unlimited. Every export path must run through Studio, and
  gate_quota reads music/quota-ledger.json BEFORE any generate or
  export operation. A 55/60 reading is a warning; 58 is a hard
  stop that routes the export through Studio or halts.

The gate EXECUTES the ledger: it parses the JSON, verifies the
ledger's internal consistency (used <= limit, warn_at < hard_stop_at
<= limit), and enforces:
  - used >= hard_stop_at  -> FAIL (hard stop; export must route
    through Studio or halt)
  - used >= warn_at       -> PASS WITH WARNING (exit 0, warning
    printed; Studio export strongly advised)
  - otherwise             -> PASS

Usage:
  python3 music/gates/gate_quota.py [--ledger music/quota-ledger.json]
                                      [--require-studio]

Exit codes: 0 = PASS (0, or 0-with-warning), 1 = FAIL (hard stop),
2 = usage/ledger error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "music" / "quota-ledger.json"


def load_ledger(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR gate_quota: no ledger at {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"ERROR gate_quota: ledger {path} is corrupt JSON: {exc}",
              file=sys.stderr)
        sys.exit(2)


def check_ledger(ledger: dict) -> list[str]:
    """Consistency checks on the ledger itself. Empty = consistent."""
    problems: list[str] = []
    used = ledger.get("standard_downloads_used")
    limit = ledger.get("standard_downloads_limit")
    warn_at = ledger.get("warn_at")
    hard_stop_at = ledger.get("hard_stop_at")
    for name, val in (("standard_downloads_used", used),
                      ("standard_downloads_limit", limit),
                      ("warn_at", warn_at),
                      ("hard_stop_at", hard_stop_at)):
        if not isinstance(val, int):
            problems.append(f"ledger field '{name}' is not an integer")
    if problems:
        return problems
    if used > limit:  # type: ignore[operator]
        problems.append("used exceeds limit — ledger is inconsistent")
    if not (warn_at < hard_stop_at <= limit):  # type: ignore[operator]
        problems.append("ledger thresholds violate warn_at < "
                        "hard_stop_at <= limit")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_quota — Suno standard-download quota gate")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER),
                        help="path to quota-ledger.json")
    parser.add_argument("--require-studio", action="store_true",
                        help="FAIL unless the ledger shows Studio as the "
                             "export path (defaults.export == 'studio' in "
                             "genres.yaml, or a studio flag in the ledger)")
    args = parser.parse_args(argv)

    ledger = load_ledger(Path(args.ledger))

    problems = check_ledger(ledger)
    if problems:
        print("FAIL gate_quota — ledger is inconsistent", file=sys.stderr)
        for m in problems:
            print(f"  - {m}", file=sys.stderr)
        return 1

    used: int = ledger["standard_downloads_used"]
    limit: int = ledger["standard_downloads_limit"]
    warn_at: int = ledger["warn_at"]
    hard_stop_at: int = ledger["hard_stop_at"]
    studio_exports: int = ledger.get("studio_exports", 0)
    period: str = ledger.get("period", "?")

    # --- hard stop ---------------------------------------------------
    if used >= hard_stop_at:
        print("FAIL gate_quota — HARD STOP", file=sys.stderr)
        print(f"  period          : {period}", file=sys.stderr)
        print(f"  standard dl used: {used}/{limit} "
              f"(hard_stop_at={hard_stop_at})", file=sys.stderr)
        print("  remaining standard downloads are reserved for the "
              "month. Route this export through Suno STUDIO "
              "(unlimited) or halt generation.", file=sys.stderr)
        return 1

    # --- Studio path check ---------------------------------------------
    studio_path = (ledger.get("export_path") == "studio"
                   or ledger.get("defaults", {}).get("export") == "studio")
    if args.require_studio and not studio_path:
        print("FAIL gate_quota — export path is not Studio", file=sys.stderr)
        print(f"  standard dl used: {used}/{limit}", file=sys.stderr)
        print("  The pipeline's binding rule: exports go through "
              "Suno STUDIO (unlimited), never the standard download "
              "button. Fix the export path and re-run the gate.",
              file=sys.stderr)
        return 1

    # --- warning band --------------------------------------------------
    if used >= warn_at:
        print("PASS gate_quota (WARNING — quota nearly exhausted)")
        print(f"  period          : {period}")
        print(f"  standard dl used: {used}/{limit} "
              f"(warn_at={warn_at}, hard_stop_at={hard_stop_at})")
        print(f"  studio exports  : {studio_exports}")
        print("  WARNING: standard downloads are nearly exhausted. "
              "Use Suno STUDIO for this export.")
        return 0

    print("PASS gate_quota")
    print(f"  period          : {period}")
    print(f"  standard dl used: {used}/{limit} "
          f"(warn_at={warn_at}, hard_stop_at={hard_stop_at})")
    print(f"  studio exports  : {studio_exports}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
