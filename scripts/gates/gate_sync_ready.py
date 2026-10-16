import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("gate_sync_ready")

def gate_sync_ready(track_id: str, package_path: str) -> Dict[str, Any]:
    """
    Executable gate: ensures all sync-critical artifacts are present and valid.
    Requirement: Stems, Metadata, Clearance Doc, Instrumental.
    """
    pkg_dir = Path(package_path)
    
    # 1. Check for required files
    critical_files = [
        "full_mix.wav",
        "instrumental.wav",
        "clearance_doc.pdf",
        "ai_disclosure.txt"
    ]
    
    for f in critical_files:
        if not (pkg_dir / f).exists():
            return {"status": "FAIL", "reason": f"Missing critical file: {f}"}
    
    # 2. Check for stems (at least 4 required)
    stems_dir = pkg_dir / "stems"
    if not stems_dir.exists() or len(list(stems_dir.glob("*.wav"))) < 4:
        return {"status": "FAIL", "reason": "Insufficient stems (minimum 4 required for sync)"}
    
    # 3. Validate Metadata
    manifest_path = pkg_dir / "manifest.json"
    if not manifest_path.exists():
        return {"status": "FAIL", "reason": "Missing manifest.json"}
    
    with open(manifest_path, "r") as f:
        meta = json.load(f)
    
    required_meta = ["bpm", "key", "mood"]
    for field in required_meta:
        if field not in meta:
            return {"status": "FAIL", "reason": f"Missing metadata field: {field}"}

    return {"status": "PASS", "findings": "All sync deliverables verified"}

if __name__ == "__main__":
    # Verification test
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "test_pkg"
        pkg.mkdir()
        (pkg / "stems").mkdir()
        for f in ["full_mix.wav", "instrumental.wav", "clearance_doc.pdf", "ai_disclosure.txt"]:
            (pkg / f).write_text("DUMMY")
        for i in range(5): (pkg / "stems" / f"stem_{i}.wav").write_text("DUMMY")
        with open(pkg / "manifest.json", "w") as f:
            json.dump({"bpm": 120, "key": "Am", "mood": "Dark"}, f)
            
        res = gate_sync_ready("test_sync", str(pkg))
        print(json.dumps(res, indent=2))
