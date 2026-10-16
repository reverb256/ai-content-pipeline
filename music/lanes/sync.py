import os
import json
from pathlib import Path
from typing import Dict, List, Any

# --- CONFIGURATION ---
# Sync-ready packages require: full mix, instrumental, 12 stems, and legal docs.
REQUIRED_ARTIFACTS = [
    "full_mix.wav",
    "instrumental.wav",
    "stems/drums.wav",
    "stems/bass.wav",
    "stems/synth_lead.wav",
    "stems/synth_pad.wav",
    "stems/percussion.wav",
    "stems/vocals_main.wav",
    "stems/vocals_back.wav",
    "stems/fx.wav",
    "stems/sub.wav",
    "stems/chord_prog.wav",
    "stems/melody.wav",
    "stems/atmos.wav",
    "clearance_doc.pdf",
    "ai_disclosure.txt"
]

def build_sync_package(track_id: str, source_dir: str, output_root: str, metadata: Dict[str, Any]):
    """
    Packages a track for sync licensing.
    Organizes files into a standardized structure and writes a manifest.
    """
    package_dir = Path(output_root) / "sync" / track_id
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "stems").mkdir(exist_ok=True)

    # 1. Verify and Copy Artifacts
    for artifact in REQUIRED_ARTIFACTS:
        src = Path(source_dir) / artifact
        dst = package_dir / artifact
        if src.exists():
            # In real usage: shutil.copy2(src, dst)
            pass 
        else:
            print(f"MISSING: {artifact}")

    # 2. Write Metadata Manifest
    manifest = {
        "track_id": track_id,
        "metadata": metadata,
        "package_version": "1.0",
        "artifacts": REQUIRED_ARTIFACTS
    }
    with open(package_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return str(package_dir)

if __name__ == "__main__":
    test_meta = {
        "mood": "Tense, Cinematic",
        "tempo": "120",
        "key": "C Minor",
        "instrumentation": "Orchestral Hybrid",
        "themes": "Pursuit, Industrial",
        "bpm": 120
    }
    print(f"Build sync package logic initialized for track: TEST_001")
