import os
import json
import shutil
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
    
    def __init__(self, track_id: str, metadata: Dict[str, Any],
                 out_dir: Optional[Path] = None):
        self.track_id = track_id
        self.metadata = metadata
        # `out_dir` exists so the VERIFICATION run below packs into a tempdir
        # instead of into this repo. Card t_8f515be3 measured why: the throwaway
        # `t_verify_streaming/` package was committed to main as a manifest plus
        # two symlinks into a pruned scratch dir, and a reader counts that as
        # "the master is in the repo".
        self.package_path = (Path(out_dir) if out_dir else PACKAGES_DIR) / track_id
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
            
        # 2. Copy Master Audio - a COPY, never a symlink (card t_8f515be3).
        # git stores a link's TARGET, not the bytes: the committed package of the
        # verification run held an 82-byte master.wav whose target was a scratch
        # path that no longer existed. Duplicating bytes costs nothing here - a
        # package master that is byte-identical to the campaign master is the
        # SAME blob in the object store (measured on
        # music/packages/streaming/erasing-the-distance/master.wav).
        master_dest = self.package_path / "master.wav"
        if master_path.exists():
            if master_dest.exists() or master_dest.is_symlink(): master_dest.unlink()
            shutil.copyfile(master_path, master_dest)
        else:
            raise FileNotFoundError(f"Master audio not found at {master_path}")
            
        # 3. Copy Artwork - the same rule as the master above (card t_8f515be3):
        # a package ships bytes, and a link to a scratch dir ships a path string.
        art_dest = self.package_path / "artwork.jpg"
        if artwork_path.exists():
            if art_dest.exists() or art_dest.is_symlink(): art_dest.unlink()
            shutil.copyfile(artwork_path, art_dest)
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
                    ai_disclosure: bool = True, out_dir: Optional[Path] = None):
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
    
    packer = StreamingPackage(track_id, metadata, out_dir=out_dir)
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
                genre="Chill Lounge",
                # Pack into the tempdir: a verification run must leave no package
                # dir behind (card t_8f515be3).
                out_dir=Path(tmpdir) / "packages"
            )
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Verification failed: {e}")
