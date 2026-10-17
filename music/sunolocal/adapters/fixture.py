"""
Fixture engine — deterministic test double used by the acceptance checks.

Not a music model: it emits a short silent WAV so the service plumbing
(queue -> adapter -> artifact -> download) can be exercised without a GPU.
Selected only when an engine (or SUNOLOCAL_ENGINE) is explicitly set to
"fixture".
"""
from __future__ import annotations

import io
import wave
from typing import Any, Dict, Optional, Tuple


def render_fixture(duration: Optional[float] = None) -> Tuple[bytes, str, Dict[str, Any]]:
    seconds = 1.0
    if duration:
        seconds = max(0.5, min(float(duration), 2.0))
    sample_rate = 8000
    frames = int(sample_rate * seconds)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00" * frames)
    meta = {"engine": "fixture", "seconds": seconds, "note": "test double, not real audio"}
    return buf.getvalue(), "audio/wav", meta
