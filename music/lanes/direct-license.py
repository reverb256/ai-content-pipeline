import json
from pathlib import Path
from typing import Dict, Any

# --- PRICING TIERS (2026 Research) ---
LICENSE_TIERS = {
    "personal": {
        "price": 25.00,
        "rights": "Non-commercial use, social media, personal projects. No broadcast.",
        "duration": "Perpetual",
        "exclusive": False
    },
    "commercial": {
        "price": 150.00,
        "rights": "Commercial advertising, indie film, corporate videos. No broadcast TV.",
        "duration": "Perpetual",
        "exclusive": False
    },
    "exclusive": {
        "price": 500.00,
        "rights": "Full ownership of the license for a specific project. No other licenses sold.",
        "duration": "Perpetual",
        "exclusive": True
    }
}

def generate_license_table(track_id: str, output_dir: str):
    """
    Generates a pricing and deliverables table for a track's direct licensing.
    """
    out_path = Path(output_dir) / f"{track_id}_license_tiers.json"
    
    data = {
        "track_id": track_id,
        "tiers": LICENSE_TIERS,
        "deliverable_spec": {
            "personal": ["full_mix.wav"],
            "commercial": ["full_mix.wav", "instrumental.wav"],
            "exclusive": ["full_mix.wav", "instrumental.wav", "all_stems.zip"]
        }
    }
    
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return str(out_path)

if __name__ == "__main__":
    print(f"Direct-license tier generation initialized for track: TEST_001")
