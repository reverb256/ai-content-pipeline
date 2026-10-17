#!/usr/bin/env python3
"""DRAFT probe — fill the DistroKid upload form to DRAFT, never submit.

Verifies the adapter's selector chain against the live form. Prints a
one-line summary of filled/failed fields. Read-only outcome: a screenshot
at DRAFT, no live release.
"""
import json
from music.publish.playwright.session import SessionHelper
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from music.publish.playwright.distrokid import DistroKidAdapter

with SessionHelper() as session:
    adapter = DistroKidAdapter(session)
    result = adapter.upload_release(
        album_title="DRAFT PROBE",
        track_titles=["DRAFT PROBE"],
        artwork_path="music/packages/streaming/fixtures/artwork.jpg",
        genre_primary="Electronic",
        sub_genre_primary="Deep House",
        songwriter_first="PROBE",
        songwriter_last="ONLY",
        skip_if_exists=True,
    )

print("STATUS:", result.get("status"))
print("URL:", result.get("url"))
filled = result.get("fields_filled", [])
failed = result.get("fields_failed", [])
print(f"FILLED ({len(filled)}):", filled)
print(f"FAILED ({len(failed)}):", [f.split(":")[0] for f in failed])
print("SCREENSHOT:", result.get("screenshot_path"))
print("ARTWORK:", result.get("artwork_uploaded"))
