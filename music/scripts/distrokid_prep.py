#!/usr/bin/env python3
"""distrokid_prep — build a fill-in sheet for the DistroKid upload form.

Reads a release package (music/packages/streaming/<track_id>/) plus the
genre registry (music/genres.yaml) and emits, for each field on the DistroKid
upload form, the exact value to enter. Resolves the DistroKid genre CODE from
the genre name (no hardcoded tempo anywhere — tempo comes from the genre's
blueprint/caption if present, else "unknown"). Emits a Markdown sheet you read
while filling the form by hand.

No browser, no submission — this only prepares values.

Usage:
  PYTHONPATH=. python3 music/scripts/distrokid_prep.py --track-id <id>
  PYTHONPATH=. python3 music/scripts/distrokid_prep.py --track-id <id> --out sheet.md

Exit 0 on success, 2 on usage/missing-package error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
MUSIC = REPO / "music"
PACKAGES = MUSIC / "packages" / "streaming"

# DistroKid primary-genre <option value> codes, captured live 2026-10-09.
GENRE_CODES = {
    "Afrobeat": "58", "Afropop": "59", "Alternative": "1", "Big Band": "2",
    "Blues": "3", "Children's Music": "4", "Christian/Gospel": "5",
    "Classical": "33", "Comedy": "6", "Country": "7", "Dance": "8",
    "Electronic": "9", "Fitness & Workout": "34", "Folk": "14",
    "Hip-Hop/Rap": "5", "Holiday": "19", "Jazz": "20", "Latin": "16",
    "New Age": "22", "Pop": "24", "R&B/Soul": "10", "Reggae": "11",
    "Rock": "4", "Singer/Songwriter": "35", "Soundtrack": "36",
    "Spoken Word": "25", "World": "17",
}

# Electronic sub-genre codes (primary genre = Electronic, value "9"), live 2026-10-09.
ELEC_SUBGENRES = {
    "Big Room": "57", "Breaks": "35", "Chill Out": "36", "Deep House": "55",
    "Drum & Bass": "37", "Dubstep": "38", "Electro House": "39",
    "Electronica / Downtempo": "40", "Funk / Soul / Disco": "41",
    "Glitch Hop": "42", "Hard Dance": "43", "Hardcore / Hard Techno": "44",
    "Hip-Hop / R&B": "45", "House": "46",
}


def load_genre(name: str) -> dict:
    data = yaml.safe_load((MUSIC / "genres.yaml").read_text())
    genres = data.get("genres", data)
    return genres.get(name, {}) if isinstance(genres, dict) else {}


def resolve_distrokid_genre(genre_name: str, genre: dict) -> tuple[str, str, str]:
    """Return (primary_label, primary_code, subgenre_hint). Best-effort mapping
    of our genre name to a DistroKid primary genre; sub-genre left as a hint for
    the human to pick."""
    g = genre_name.lower()
    if any(k in g for k in ("lounge", "ambient", "chill")):
        return ("Electronic", GENRE_CODES["Electronic"], "Chill Out / Ambient")
    if any(k in g for k in ("trance", "house", "techno", "edm", "dnb", "dubstep")):
        return ("Electronic", GENRE_CODES["Electronic"], "pick matching sub-genre")
    if "piano" in g or "acoustic" in g:
        return ("Classical", GENRE_CODES["Classical"], "or New Age")
    if "orchestr" in g or "epic" in g:
        return ("Soundtrack", GENRE_CODES["Soundtrack"], "")
    if "anisong" in g or "anime" in g:
        return ("Pop", GENRE_CODES["Pop"], "")
    return ("Electronic", GENRE_CODES["Electronic"], "")


def build_sheet(track_id: str, manifest: dict) -> str:
    genre_name = manifest.get("genre", "")
    genre = load_genre(genre_name)
    prim_label, prim_code, sub_hint = resolve_distrokid_genre(genre_name, genre)
    tempo = genre.get("bpm_anchor") or "unknown (resolve from blueprint/caption)"

    # Songwriter = the human author of the lyrics. Legal name for DistroKid's
    # songwriter fields and SOCAN registration. (Fleet fact, 2026-10-09.)
    SONGWRITER = ("Jeremy", "Kroeker")
    # Canonical artist name for releases. (j_kro 2026-10-09: capitalized.)
    ARTIST_NAME = "Reverb256"
    title = manifest.get("title", "")
    artist = manifest.get("artist") or ARTIST_NAME
    isrc = manifest.get("isrc", "")
    explicit = "Yes" if manifest.get("explicit") else "No"
    instrumental = "No" if manifest.get("lyrics") else "Yes"

    # AI disclosure: our lane keeps lyrics human-authored.
    ai = manifest.get("ai_disclosure")
    ai_lines = (
        "- AI used? `ai_gate`: **Yes** (instrumental AI-rendered)\n"
        "- AI checkboxes to tick: **Music (composed by AI)** — NOT lyrics "
        "(lyrics are human-authored)"
    ) if ai else (
        "- AI used? `ai_gate`: **No**\n- AI checkboxes: none"
    )

    return f"""# DistroKid fill-in sheet — {track_id}

Generated from the package manifest + genre registry. Enter these values into
the DistroKid upload form (distrokid.com/new). Field names match the live form.

## Release setup
- Number of songs: **1** (single) — `#howManySongsOnThisAlbum` value `1`
- Previously released?: **No**
- Artist/band name (`#artistName`): **{artist}**
- Artwork (`#artwork`): upload `artwork.jpg` from the package

## Stores
Tick at minimum: **Spotify** (`#chkspotify`), **Apple Music** (`#chkapplemusic`),
**YouTube Music** (`#chkgoogle`), **TikTok** (`#chktiktok`),
**Instagram & Facebook** (`#chkfacebook`). Add others as desired.

## Timing & pricing
- Release date: pick a date >= 2-3 weeks out (stores need lead time)
- Language (`#language`): **en** (English)
- Track price: **$0.99** (`price_<uuid>` = `Track Mid`) — optional
- Global sync: leave default (listener time zone)

## Genre
- Primary genre (`#genrePrimary`): **{prim_label}** (value `{prim_code}`)
- Sub-genre (`#subGenrePrimary`): {sub_hint or "leave blank"}
- Reference tempo for your own notes: **{tempo}** (NOT entered on the form)

## Per-track (Track 1)
- Track title (`title_<uuid>`): **{title}**
- Audio file (`#js-track-upload-1`): upload `master.wav`
- Original or cover: **I wrote this song (original)**
- Songwriter: first = **Jeremy**, last = **Kroeker** (`songwriter_real_name_first1` / `_last1`); type = **Music and lyrics**
- Explicit (`explicit_<uuid>`): **{explicit}**
- Instrumental (`instrumental_<uuid>`): **{instrumental}**
- ISRC: **{isrc}** (enter if pre-assigned; else let DistroKid assign and record it back)

## AI disclosure (must match the rights record)
{ai_lines}

## Mandatory confirmations (tick all before submit)
- `areyousureyoutube` — YouTube Music selected
- `areyousurepromoservices` — no stream-guarantee promo services
- `areyousurenonstandardscaps` — caps warning (if title has unusual caps)

## STOP
Do NOT click `#doneButton` unless you intend a LIVE release. For a draft, stop here.
After a live release, run `music/analytics/distrokid_mail_watch.py --track-id {track_id}`
to capture the ISRC + live date from the confirmation email.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DistroKid fill-in prep sheet")
    ap.add_argument("--track-id", required=True)
    ap.add_argument("--out", help="write sheet here instead of stdout")
    args = ap.parse_args(argv)

    pkg = PACKAGES / args.track_id
    manifest_path = pkg / "manifest.json"
    if not manifest_path.is_file():
        print(f"no manifest at {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sheet = build_sheet(args.track_id, manifest)

    if args.out:
        Path(args.out).write_text(sheet, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
