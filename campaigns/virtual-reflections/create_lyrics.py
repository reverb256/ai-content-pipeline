#!/usr/bin/env python3
"""Create lyrics files for Virtual Reflections album from extracted Suno data."""
import json
from pathlib import Path

REPO = Path("/home/j_kro/Projects/ai-content-pipeline")
LYRICS_DIR = REPO / "campaigns/virtual-reflections/lyrics"

# Load the raw lyrics data
with open(REPO / "campaigns/virtual-reflections/all-lyrics-raw.json") as f:
    raw = json.load(f)

# Load the full lyrics for truncated songs
with open(REPO / "campaigns/virtual-reflections/full-lyrics.json") as f:
    full = json.load(f)

# Song metadata
SONGS = [
    ("af1e57f0-6595-460b-a0e7-7bb0bdd41f37", "Welcome", "spoken word, ambient, mindfulness"),
    ("63ce63d8-9888-4626-a431-d225ff9019cb", "These Worlds Are Made of Light", "ambient, electronic, art-pop"),
    ("23937711-dbfe-4612-95a7-39a20a64379b", "Erasing the Distance", "synthpop, dream pop"),
    ("51c07d53-6eca-431a-886e-36f9c482abef", "This Small Forever", "art-pop, ballad"),
    ("4e23725e-e4ec-4b55-ad72-ed965fa822db", "World of Blue", "acoustic ballad, romantic"),
    ("6db57655-f2c7-4929-b6ad-3ab948155962", "Sincerely", "indie-pop, ballad, cinematic"),
]

for song_id, title, style in SONGS:
    slug = title.lower().replace(" ", "-")
    track_dir = LYRICS_DIR / slug
    track_dir.mkdir(parents=True, exist_ok=True)
    
    # Get lyrics text
    if title in full:
        lyrics_text = full[title]
    elif title in raw:
        lyrics_text = raw[title]["lyrics"]
        # Clean up: remove player UI text
        if "Edit displayed lyrics" in lyrics_text:
            lyrics_text = lyrics_text[:lyrics_text.find("Edit displayed lyrics")].strip()
    else:
        lyrics_text = ""
    
    # Write lyrics file
    lyrics_file = track_dir / "lyrics.txt"
    with open(lyrics_file, "w") as f:
        f.write(lyrics_text)
    
    # Write metadata file
    meta_file = track_dir / "metadata.json"
    meta = {
        "song_id": song_id,
        "title": title,
        "style": style,
        "lyrics_author": "j_kro",
        "lyrics_authored": "2026-10-07 to 2026-10-09",
        "source": "Suno song page (suno.com/song/<id>)",
        "extracted": "2026-10-09",
        "has_lyrics": len(lyrics_text) > 0,
        "lyrics_length": len(lyrics_text),
    }
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)
    
    print(f"Created {track_dir}/")
    print(f"  lyrics.txt: {len(lyrics_text)} chars")
    print(f"  metadata.json: {len(json.dumps(meta))} chars")

print(f"\nAll lyrics files created in {LYRICS_DIR}")
