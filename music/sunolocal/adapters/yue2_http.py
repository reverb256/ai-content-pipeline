"""
YuE2 adapter for sunolocal: calls the yue2-zephyr HTTP service.

Env override (resolved per call):
  YUE2_BASE_URL   base URL of the service (default: the in-cluster DNS name)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple

HTTP_TIMEOUT = 120


def _base() -> str:
    default = "http://yue2-zephyr.mining.svc.cluster.local"
    return os.environ.get("YUE2_BASE_URL", default).rstrip("/")


def render_yue2(kwargs: Dict[str, Any]) -> Tuple[bytes, str, Dict[str, Any]]:
    """Generate one song via YuE2-3B; returns (flac_bytes, mime, metadata)."""
    url = _base() + "/generate"
    payload: Dict[str, Any] = {}
    for key in ("id", "style", "lyrics", "cot", "seed", "cfg_scale", "abc"):
        value = kwargs.get(key)
        if value is not None:
            payload[key] = value
    if "id" not in payload:
        payload["id"] = "suno"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            if resp.status != 200:
                raise RuntimeError(f"YuE2 service returned status {resp.status}")
            audio_bytes = resp.read()
            meta = {
                "engine": "yue2",
                "request": payload,
                "response_headers": dict(resp.headers),
            }
            return audio_bytes, "audio/flac", meta
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"YuE2 service HTTP error {exc.code}: {body[:200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"YuE2 service URL error: {exc}") from exc
