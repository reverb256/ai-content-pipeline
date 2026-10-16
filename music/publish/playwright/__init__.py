"""Playwright adapters for music publishing surfaces without official APIs.

Adapters:
  - DistroKid (distrokid.py) — release upload automation
  - Fab/Unreal (fab.py) — publisher portal submission
  - Unity Asset Store (unity.py) — publisher submission
  - Splice/Loopmasters (splice.py) — form-based submission

All adapters use SessionHelper for persistent browser state.
"""
from .session import SessionHelper, SessionError, RateLimited

__all__ = ["SessionHelper", "SessionError", "RateLimited"]
