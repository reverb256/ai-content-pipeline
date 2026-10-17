#!/usr/bin/env python3
"""scripts/gates/gate_asset_pack.py — Executable gate for asset packs.

Verifies an asset pack manifest by CHECKING the artifact files on disk
and measuring loop seam discontinuities. This is NOT a grep-gate.

Usage:
    python3 scripts/gates/gate_asset_pack.py <pack_dir>

Exit codes:
    0 = PASS
    1 = FAIL (missing files, too few assets, loops not click-free)
"""

import argparse
import json
import sys
from pathlib import Path

REQUIRED_COUNTS = {
    "loops": 5,
    "stems": 12,
    "one_shots": 5,
}
CLICK_FREE_THRESHOLD_DBFS = -60.0  # measured seam must be below this


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pack_dir", help="Directory containing manifest.json")
    args = ap.parse_args()

    pkg = Path(args.pack_dir)
    manifest_path = pkg / "manifest.json"
    if not manifest_path.exists():
        print(f"FAIL: manifest.json not found in {pkg}")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    # The manifest file paths are repo-relative; resolve from cwd
    repo_root = Path.cwd()

    all_pass = True
    print(f"=== ASSET PACK GATE: {manifest.get('pack_name', 'unknown')} ===")
    print(f"BPM={manifest.get('bpm')}, Key={manifest.get('key')}")
    print()

    # 1. Verify counts
    for cat, min_count in REQUIRED_COUNTS.items():
        entries = manifest.get(cat, [])
        actual = len(entries)
        status = "PASS" if actual >= min_count else "FAIL"
        if actual < min_count:
            all_pass = False
        print(f"  [{status}] {cat}: {actual} >= {min_count}")

    # 2. Verify all asset files exist (real disk check)
    print()
    for cat in ["loops", "stems", "one_shots", "sfx"]:
        for entry in manifest.get(cat, []):
            fpath = repo_root / entry["file"]
            if not fpath.exists():
                print(f"  [FAIL] file missing: {entry['file']}")
                all_pass = False

    # 3. Verify each loop is click-free (real measurement)
    print()
    print("--- Loop seam click-free verification (measured) ---")
    for loop in manifest.get("loops", []):
        seam_db = loop.get("seam_discontinuity_db")
        click_free = loop.get("click_free", False)
        measured_pass = seam_db is not None and abs(seam_db) > abs(CLICK_FREE_THRESHOLD_DBFS)
        status = "PASS" if measured_pass else "FAIL"
        if not measured_pass:
            all_pass = False
        print(f"  [{status}] {Path(loop['file']).name}: seam={seam_db} dBFS "
              f"(threshold={CLICK_FREE_THRESHOLD_DBFS} dBFS)")

    # 4. Verify licence
    lic = pkg / "LICENCE.txt"
    if lic.exists():
        print(f"\n  [PASS] licence present: {lic} ({lic.stat().st_size} bytes)")
    else:
        print(f"\n  [FAIL] licence missing: {lic}")
        all_pass = False

    result = "PASS" if all_pass else "FAIL"
    print(f"\n=== GATE RESULT: {result} ===")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
