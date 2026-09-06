"""Fuzzy atmos/room-tone resolver + default keyword map for storyteller.py.

Exact-file lookup is too brittle: a story says [ATMOS: rain on tin roof]
but the library file is assets/atmos/rain.wav. This module gives the
storyteller a small fuzzy matcher that maps cue names onto the library,
plus keyword-driven defaults for scenes with NO explicit atmos cue.

Imported by storyteller.py; keeps asset-resolution logic out of the main
render loop.
"""
from __future__ import annotations

import re
from pathlib import Path

# ---- atmos keyword dictionary ------------------------------------------- #
# Canonical library stems that exist in assets/atmos/. Each is keyed by the
# words a writer would plausibly type in [ATMOS: ...].
ATMOS_KEYWORDS: dict[str, str] = {
    # rooms / interior
    "room": "roomtone-indoor-quiet",
    "indoor": "roomtone-indoor-quiet",
    "quiet room": "roomtone-indoor-quiet",
    "interior": "roomtone-indoor-quiet",
    "office": "roomtone-office-open",
    "cafe": "roomtone-cafe",
    "coffee": "roomtone-cafe",
    "restaurant": "roomtone-cafe",
    "library": "roomtone-library",
    "basement": "roomtone-basement",
    "cellar": "roomtone-basement",
    "hospital": "hospice-ward",
    "hospice": "hospice-ward",
    "ward": "hospice-ward",
    "lab": "containment-lab-sterile-hum-faint-air-filtration",
    "laboratory": "containment-lab-sterile-hum-faint-air-filtration",
    "station": "station-ventilation-electrical-hum",
    "space station": "station-ventilation-electrical-hum",
    "spacecraft": "spacecraft-cabin",
    "cabin": "spacecraft-cabin",
    "ship": "spacecraft-cabin",
    "ventilation": "station-ventilation-electrical-hum",
    # weather
    "rain": "rain",
    "rain on tin roof": "rain-on-window",
    "window": "rain-on-window",
    "wind": "wind",
    "breeze": "wind",
    "howling": "wind-storm",
    "gust": "wind-storm",
    "storm": "wind-storm",
    "thunder": "thunder-rain",
    "ocean": "ocean-waves",
    "sea": "ocean-waves",
    "beach": "ocean-waves",
    "waves": "ocean-waves",
    "forest": "forest",
    "woods": "forest",
    "jungle": "alien-jungle",
    "crickets": "night-crickets",
    "night": "night-crickets",
    "countryside": "night-crickets",
    "street": "city-street",
    "city": "city-street",
    "traffic": "city-street",
    "urban": "city-street",
    "harbor": "harbor",
    "harbour": "harbor",
    "dock": "harbor",
    "snow": "snowfall",
    "winter": "snowfall",
    "desert": "desert-wind",
    "dune": "desert-wind",
    "cave": "underground-cavern",
    "cavern": "underground-cavern",
    "underground": "underground-cavern",
    "tension": "tension-room",
    "suspense": "tension-room",
    "ominous": "tension-room",
    "deep space": "deep-space-hum-low-and-constant",
    "space": "deep-space-hum-faint",
    "hum": "station-ventilation-electrical-hum",
    "drone": "deep-space-hum-low-and-constant",
    "silence": "silence",
    "quiet": "roomtone-indoor-quiet",
    "calm": "roomtone-indoor-quiet",
}

# Default bed when a scene has NO atmos cue and NO keyword match.
DEFAULT_ATMOS = "roomtone-indoor-quiet"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def resolve_atmos(value: str, atmos_dir: Path) -> str:
    """Resolve an [ATMOS: value] cue to a real library path.

    Strategy:
      1. Exact: assets/atmos/<slug(value)>.wav
      2. Keyword: longest matching phrase in ATMOS_KEYWORDS whose stem exists
      3. Token: any single significant word from the cue that maps to a bed
    Returns the file path, or '' when nothing matches.
    """
    v = value.strip().lower()

    # 1. exact slug
    p = atmos_dir / f"{slug(v)}.wav"
    if p.exists():
        return str(p)

    # 2. keyword map — longest phrase wins
    for phrase in sorted(ATMOS_KEYWORDS, key=len, reverse=True):
        if phrase in v:
            cand = atmos_dir / f"{ATMOS_KEYWORDS[phrase]}.wav"
            if cand.exists():
                return str(cand)

    # 3. token-level: any word that maps to a known stem
    words = re.findall(r"[a-z]+", v)
    for w in words:
        if w in ATMOS_KEYWORDS:
            cand = atmos_dir / f"{ATMOS_KEYWORDS[w]}.wav"
            if cand.exists():
                return str(cand)
    return ""


def default_atmos_path(atmos_dir: Path) -> str:
    """Return the default room-tone bed path, or '' when missing."""
    p = atmos_dir / f"{DEFAULT_ATMOS}.wav"
    return str(p) if p.exists() else ""
