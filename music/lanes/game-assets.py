# music/lanes/game-assets.py
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("game_assets_lane")

# --- CONFIGURATION ---
# Game asset packs require: 
# 1. Master loopable track
# 2. Stems (standardized set)
# 3. One-shots (derived from stems/master)
# 4. Seamless loop point metadata
# 5. High-quality WAV (44.1kHz/16-bit or 48kHz/24-bit)
REQUIRED_STEMS = [
    "drums", "bass", "lead", "pads", "percussion", 
    "fx", "sub", "melody", "atmos", "chord_prog"
]

class GameAssetPackage:
    """
    Packages music as a game asset pack for itch.io / Unity Asset Store.
    Focuses on loopability, stem availability, and clear naming.
    """
    def __init__(self, track_id: str, genre: str, output_root: str):
        self.track_id = track_id
        self.genre = genre
        self.package_path = Path(output_root) / "packages" / "game-assets" / f"{genre}_{track_id}"
        self.package_path.mkdir(parents=True, exist_ok=True)
        
        # Sub-directories for organization
        (self.package_path / "loops").mkdir(exist_ok=True)
        (self.package_path / "stems").mkdir(exist_ok=True)
        (self.package_path / "one_shots").mkdir(exist_ok=True)
        (self.package_path / "docs").mkdir(exist_ok=True)

    def package(self, source_dir: str, metadata: Dict[str, Any], loop_points: Tuple[float, float]):
        """
        Organizes assets into the final deliverable structure.
        loop_points: (start_sample, end_sample)
        """
        source_path = Path(source_dir)
        
        # 1. Package the Master Loop
        master_src = source_path / "full_mix.wav"
        master_dst = self.package_path / "loops" / f"{self.track_id}_loop.wav"
        if master_src.exists():
            # In production: shutil.copy2(master_src, master_dst)
            master_dst.write_text("DUMMY WAV DATA") 
        else:
            raise FileNotFoundError(f"Master loop missing: {master_src}")

        # 2. Package Stems
        stems_dir = source_path / "stems"
        for stem in REQUIRED_STEMS:
            stem_src = stems_dir / f"{stem}.wav"
            stem_dst = self.package_path / "stems" / f"{self.track_id}_{stem}.wav"
            if stem_src.exists():
                # shutil.copy2(stem_src, stem_dst)
                stem_dst.write_text("DUMMY STEM DATA")
            else:
                logger.warning(f"Optional stem {stem} missing for {self.track_id}")

        # 3. Generate One-Shots (Mock logic: usually derived via slicing)
        for stem in ["drums", "percussion", "fx"]:
            one_shot_dst = self.package_path / "one_shots" / f"{self.track_id}_{stem}_oneshot.wav"
            one_shot_dst.write_text("DUMMY ONE-SHOT DATA")

        # 4. Write Technical Metadata (The 'Click-Free' Guarantee)
        manifest = {
            "track_id": self.track_id,
            "genre": self.genre,
            "sample_rate": metadata.get("sample_rate", 44100),
            "bit_depth": metadata.get("bit_depth", 16),
            "bpm": metadata.get("bpm"),
            "key": metadata.get("key"),
            "loop_points": {
                "start_sample": loop_points[0],
                "end_sample": loop_points[1],
                "duration_seconds": (loop_points[1] - loop_points[0]) / metadata.get("sample_rate", 44100)
            },
            "licence": "perpetual_game_asset_v1"
        }
        with open(self.package_path / "metadata.json", "w") as f:
            json.dump(manifest, f, indent=2)

        return str(self.package_path)

def build_game_asset_pack(track_id: str, genre: str, source_dir: str, output_root: str, metadata: Dict[str, Any], loop_points: Tuple[float, float]):
    """
    Entry point for packaging game assets.
    """
    packer = GameAssetPackage(track_id, genre, output_root)
    return packer.package(source_dir, metadata, loop_points)

if __name__ == "__main__":
    # Verification mode
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup source files
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        (source_dir / "full_mix.wav").write_text("MASTER")
        stems_dir = source_dir / "stems"
        stems_dir.mkdir()
        for s in REQUIRED_STEMS: (stems_dir / f"{s}.wav").write_text("STEM")
        
        meta = {"bpm": 120, "key": "Am", "sample_rate": 44100, "bit_depth": 16}
        loops = (0, 44100 * 4) # 4 second loop
        
        res = build_game_asset_pack("test_game_001", "chiptune-8bit", str(source_dir), "/tmp/hermes_test", meta, loops)
        print(f"Package created at: {res}")
