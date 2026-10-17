#!/usr/bin/env python3
"""DRAFT probe — fill the DistroKid upload form to DRAFT, never submit.

Verifies the adapter's selector chain against the live form. Prints a
one-line summary of filled/failed fields. Read-only outcome: a screenshot
at DRAFT, no live release.

The artwork source is a CLI argument, defaulting to the TRACKED fixture under
music/packages/streaming/fixtures/artwork.jpg. Card t_23641f1f measured that the
previous default ("music/packages/streaming/t_verify_streaming/artwork.jpg") was a
deleted fixture: t_verify_streaming was verification output, removed from the tree,
so the path resolved nowhere and the probe's only failure mode was "BrowserUse
fills a form with no artwork" -- a silent miss, not a loud error. A probe that
cannot find its own fixture is a defect: it exits 2 before it touches the form.
"""
import argparse
import os
import sys
from pathlib import Path

# The probe lives at music/scripts/, so the repo root (its parent's parent) is the
# package root. Without this, `python3 music/scripts/distrokid_draft_probe.py` from
# the repo root raises ModuleNotFoundError: No module named 'music' and the probe can
# never reach its own loud-fail path -- it dies on the import instead of on the
# missing artwork (card t_23641f1f: the loud exit is the whole point).
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from music.publish.playwright.session import SessionHelper
from music.publish.playwright.distrokid import DistroKidAdapter

DEFAULT_ARTWORK = "music/packages/streaming/fixtures/artwork.jpg"

ap = argparse.ArgumentParser(
    description="DistroKid DRAFT-form probe. Fills the upload form and stops at DRAFT.")
ap.add_argument("--artwork", default=DEFAULT_ARTWORK,
                help="artwork source (default: the tracked fixture under "
                     "music/packages/streaming/fixtures/)")
ap.add_argument("--album-title", default="DRAFT PROBE")
ap.add_argument("--track-titles", nargs="*", default=["DRAFT PROBE"])
ap.add_argument("--genre-primary", default="Electronic")
ap.add_argument("--sub-genre-primary", default="Deep House")
ap.add_argument("--songwriter-first", default="PROBE")
ap.add_argument("--songwriter-last", default="ONLY")
ap.add_argument("--skip-if-exists", action="store_true", default=True)
args = ap.parse_args()

artwork_path = args.artwork
import os
if not os.path.exists(artwork_path):
    print(f"PROBE REFUSED: artwork not found at {artwork_path!r} -- the probe cannot "
          f"verify the adapter without a real image (card t_23641f1f: the previous "
          f"default pointed at a deleted fixture and the form was filled with no "
          f"artwork, which is a silent miss, not a loud error).", file=sys.stderr)
    sys.exit(2)

with SessionHelper() as session:
    adapter = DistroKidAdapter(session)
    result = adapter.upload_release(
        album_title=args.album_title,
        track_titles=args.track_titles,
        artwork_path=artwork_path,
        genre_primary=args.genre_primary,
        sub_genre_primary=args.sub_genre_primary,
        songwriter_first=args.songwriter_first,
        songwriter_last=args.songwriter_last,
        skip_if_exists=args.skip_if_exists,
    )

print("STATUS:", result.get("status"))
print("URL:", result.get("url"))
filled = result.get("fields_filled", [])
failed = result.get("fields_failed", [])
print(f"FILLED ({len(filled)}):", filled)
print(f"FAILED ({len(failed)}):", [f.split(":")[0] for f in failed])
print("SCREENSHOT:", result.get("screenshot_path"))
print("ARTWORK:", result.get("artwork_uploaded"))