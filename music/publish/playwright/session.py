"""Shared Playwright session helper for music/publish/playwright/.

Reuses the persistent browser profile so logins survive across sessions.
Connects to the pipeline's CDP Chromium (:9222) when available, falling
back to launching a new browser with the persistent profile.

Never hardcodes credentials. Never creates accounts.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext

logger = logging.getLogger(__name__)

DEFAULT_CDP_PORT = int(os.environ.get("MUSIC_PW_CDP_PORT", "9222"))
DEFAULT_PROFILE_DIR = os.environ.get(
    "MUSIC_PW_PROFILE_DIR",
    os.path.expanduser("~/.hermes/automation-profile"),
)

MAX_RETRIES = 3
BACKOFF_BASE = 2.0
BACKOFF_MAX = 60.0

RATE_LIMIT_MARKERS = ("rate limit", "too many requests", "429", "slow down")


class SessionError(Exception):
    """Session-level failure (browser crash, navigation failure)."""


class RateLimited(Exception):
    """Hit a 429 rate limit."""


class SessionHelper:
    """Manages a persistent Playwright browser session.

    Usage:
        with SessionHelper() as session:
            page = session.new_page()
            ...
    """

    def __init__(
        self,
        cdp_port: int = DEFAULT_CDP_PORT,
        profile_dir: str = DEFAULT_PROFILE_DIR,
    ):
        self.cdp_port = cdp_port
        self.profile_dir = profile_dir
        self._pw = None
        self._browser = None
        self._context = None

    def start(self) -> SessionHelper:
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.connect_over_cdp(
                f"http://127.0.0.1:{self.cdp_port}"
            )
            self._context = self._browser.contexts[0]
            logger.info("Connected to CDP Chromium on :%d", self.cdp_port)
            return self
        except Exception as e:
            logger.warning("CDP connect failed (%s); launching persistent context", e)

        if not Path(self.profile_dir).exists():
            raise SessionError(f"Browser profile not found: {self.profile_dir}")

        self._context = self._pw.chromium.launch_persistent_context(
            self.profile_dir,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Launched persistent context with profile %s", self.profile_dir)
        return self

    def new_page(self) -> Page:
        if self._context is None:
            raise SessionError("Session not started. Call start() first.")
        return self._context.new_page()

    def close(self):
        if self._pw:
            self._pw.stop()
            self._pw = None

    def __enter__(self) -> SessionHelper:
        return self.start()

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def is_rate_limited(page: Page) -> bool:
        try:
            body = page.inner_text("body")
            low = body.lower()
            return any(m in low for m in RATE_LIMIT_MARKERS)
        except Exception:
            return False

    @staticmethod
    def retry_with_backoff(fn, max_retries: int = MAX_RETRIES):
        last_exc = None
        for attempt in range(max_retries):
            try:
                return fn()
            except RateLimited as e:
                last_exc = e
                if attempt == max_retries - 1:
                    raise
                delay = min(BACKOFF_BASE ** attempt, BACKOFF_MAX)
                logger.warning("Rate limited; retrying in %.1fs", delay)
                time.sleep(delay)
        raise SessionError(f"max retries exceeded: {last_exc}")
