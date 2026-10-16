import os
import json
import uuid
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("streaming_lane")

# CONSTANTS
REPO_ROOT = Path("/home/j_kro/Projects/ai-content-pipeline")
MUSIC_ROOT = REPO_ROOT / "music"
PACKAGES_DIR = MUSIC_ROOT / "packages" / "streaming"

class StreamingPackage:
    """
    Packages a music release for streaming distributors (DistroKid/TuneCore).
    Follows the requirement: one track, complete metadata, ISRC, and master.
    """
    
    def __init__(self, track_id: str, metadata: Dict[str, Any]):
        self.track_id = track_id
        self.metadata = metadata
        self.package_path = PACKAGES_DIR / track_id
        self.package_path.mkdir(parents=True, exist_ok=True)
        
    def generate_isrc(self) -> str:
        """
        Generates a mock ISRC for packaging verification.
        In a real scenario, this is assigned by the distributor or PRO.
        Format: CC-XXX-YY-NNNNN
        """
        return f"US-TKN-26-{uuid.uuid4().hex[:5].upper()}"

    def package(self, master_path: Path, artwork_path: Path):
        """
        Creates the distribution bundle on disk.
        """
        isrc = self.metadata.get("isrc") or self.generate_isrc()
        self.metadata["isrc"] = isrc
        
        # 1. Save Metadata Manifest
        manifest_path = self.package_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
            
        # 2. Link Master Audio
        master_dest = self.package_path / "master.wav"
        if master_path.exists():
            # Use symlink to avoid duplicating large WAVs during packaging
            if master_dest.exists(): master_dest.unlink()
            master_dest.symlink_to(master_path)
        else:
            raise FileNotFoundError(f"Master audio not found at {master_path}")
            
        # 3. Link Artwork
        art_dest = self.package_path / "artwork.jpg"
        if artwork_path.exists():
            if art_dest.exists(): art_dest.unlink()
            art_dest.symlink_to(artwork_path)
        else:
            raise FileNotFoundError(f"Artwork not found at {artwork_path}")
            
        logger.info(f"Package created at {self.package_path}")
        return {
            "package_path": str(self.package_path),
            "isrc": isrc,
            "manifest": str(manifest_path)
        }

def package_release(track_id: str, master_path: str, artwork_path: str, 
                    title: str, artist: str, genre: str, 
                    lyrics: str = "", explicit: bool = False, 
                    ai_disclosure: bool = True):
    """
    Entry point for the distributor bot to package a track.
    """
    metadata = {
        "title": title,
        "artist": artist,
        "genre": genre,
        "lyrics": lyrics,
        "explicit": explicit,
        "ai_disclosure": ai_disclosure,
        "distributor_preference": "distrokid", # Primary per architecture
        "secondary_distributor": "tunecore"
    }
    
    packer = StreamingPackage(track_id, metadata)
    return packer.package(Path(master_path), Path(artwork_path))

if __name__ == "__main__":
    # Verification mode: Create a dummy track package
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_master = Path(tmpdir) / "test_master.wav"
        tmp_art = Path(tmpdir) / "test_art.jpg"
        tmp_master.write_text("DUMMY WAV DATA")
        tmp_art.write_text("DUMMY JPG DATA")
        
        try:
            res = package_release(
                track_id="t_verify_streaming",
                master_path=str(tmp_master),
                artwork_path=str(tmp_art),
                title="Verification Track",
                artist="Hermes Bot",
                genre="Chill Lounge"
            )
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Verification failed: {e}")
