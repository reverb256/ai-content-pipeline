"""Splice/Loopmasters/ProducerLoops Playwright adapter.

Semi-automated form-based submission for curated sample platforms.
These platforms require human review of each submission.

Selectors derived from the Splice creator portal and Loopmasters
submission form DOM structures. Stops at DRAFT — does not submit.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from .session import SessionHelper, RateLimited

logger = logging.getLogger(__name__)

SPLICE_SELECTORS = {
    "upload_btn": 'button:has-text("Upload")',
    "pack_name": 'input[name="packName"]',
    "pack_description": 'textarea[name="description"]',
    "genre_select": 'select[name="genre"]',
    "bpm_input": 'input[name="bpm"]',
    "key_input": 'input[name="key"]',
    "tags_input": 'input[name="tags"]',
    "upload_file": 'input[type="file"]',
    "save_draft_btn": 'button:has-text("Save draft")',
    "submit_btn": 'button:has-text("Submit")',
}

LOOPMASTERS_SELECTORS = {
    "new_release_btn": 'a:has-text("New release")',
    "release_title": 'input[name="title"]',
    "release_description": 'textarea[name="description"]',
    "genre_select": 'select[name="genre"]',
    "subgenre_select": 'select[name="subgenre"]',
    "bpm_input": 'input[name="bpm"]',
    "key_input": 'input[name="key"]',
    "upload_file": 'input[type="file"]',
    "save_draft_btn": 'button:has-text("Save draft")',
    "submit_btn": 'button:has-text("Submit for review")',
}


class SpliceAdapter:
    """Submit sample packs to Splice/Loopmasters/ProducerLoops.

    Semi-automated: fills the form and stops at DRAFT. Human review
    is required before final submission on these curated platforms.
    """

    def __init__(self, session: SessionHelper):
        self.session = session

    def submit_splice(
        self,
        page: Page,
        pack_name: str,
        description: str,
        genre: str,
        bpm: int = 120,
        key: str = "C maj",
        tags: list[str] | None = None,
        file_path: Optional[str] = None,
    ) -> dict:
        """Fill the Splice creator upload form. Stops at DRAFT."""
        result = {
            "pack_name": pack_name,
            "fields_filled": [],
            "fields_failed": [],
            "screenshot_path": None,
            "url": None,
        }

        page.goto("https://splice.com/creators")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if self.session.is_rate_limited(page):
            raise RateLimited("Rate limited on Splice")

        # Click Upload
        try:
            page.click(SPLICE_SELECTORS["upload_btn"], timeout=10000)
            time.sleep(2)
            result["fields_filled"].append("upload_btn")
        except Exception as e:
            result["fields_failed"].append(f"upload_btn: {e}")

        # Fill pack name
        try:
            page.fill(SPLICE_SELECTORS["pack_name"], pack_name)
            result["fields_filled"].append("pack_name")
        except Exception as e:
            result["fields_failed"].append(f"pack_name: {e}")

        # Fill description
        try:
            page.fill(SPLICE_SELECTORS["pack_description"], description)
            result["fields_filled"].append("description")
        except Exception as e:
            result["fields_failed"].append(f"description: {e}")

        # Select genre
        try:
            page.select_option(SPLICE_SELECTORS["genre_select"], label=genre)
            time.sleep(0.5)
            result["fields_filled"].append("genre")
        except Exception as e:
            result["fields_failed"].append(f"genre: {e}")

        # BPM
        try:
            page.fill(SPLICE_SELECTORS["bpm_input"], str(bpm))
            result["fields_filled"].append("bpm")
        except Exception as e:
            result["fields_failed"].append(f"bpm: {e}")

        # Key
        try:
            page.fill(SPLICE_SELECTORS["key_input"], key)
            result["fields_filled"].append("key")
        except Exception as e:
            result["fields_failed"].append(f"key: {e}")

        # Tags
        if tags:
            try:
                page.fill(SPLICE_SELECTORS["tags_input"], ", ".join(tags))
                result["fields_filled"].append("tags")
            except Exception as e:
                result["fields_failed"].append(f"tags: {e}")

        # Upload file
        if file_path and Path(file_path).exists():
            try:
                page.set_input_files(SPLICE_SELECTORS["upload_file"], file_path)
                time.sleep(2)
                result["fields_filled"].append("file")
            except Exception as e:
                result["fields_failed"].append(f"file: {e}")

        # Save as draft
        try:
            page.click(SPLICE_SELECTORS["save_draft_btn"], timeout=5000)
            time.sleep(1)
            result["fields_filled"].append("save_draft")
        except Exception as e:
            result["fields_failed"].append(f"save_draft: {e}")

        # Screenshot
        screenshot_dir = Path("/home/j_kro/.hermes/profiles/music-producer/cache/scratch/splice-draft")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"splice_draft_{ts}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot_path"] = str(screenshot_path)
        result["url"] = page.url

        logger.info("Splice form filled to DRAFT state. NOT submitting.")
        return result

    def submit_loopmasters(
        self,
        page: Page,
        title: str,
        description: str,
        genre: str,
        subgenre: str = "",
        bpm: int = 120,
        key: str = "C maj",
        file_path: Optional[str] = None,
    ) -> dict:
        """Fill the Loopmasters release submission form. Stops at DRAFT."""
        result = {
            "title": title,
            "fields_filled": [],
            "fields_failed": [],
            "screenshot_path": None,
            "url": None,
        }

        page.goto("https://www.loopmasters.com/artists")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if self.session.is_rate_limited(page):
            raise RateLimited("Rate limited on Loopmasters")

        # Click New release
        try:
            page.click(LOOPMASTERS_SELECTORS["new_release_btn"], timeout=10000)
            time.sleep(2)
            result["fields_filled"].append("new_release_btn")
        except Exception as e:
            result["fields_failed"].append(f"new_release_btn: {e}")

        # Fill title
        try:
            page.fill(LOOPMASTERS_SELECTORS["release_title"], title)
            result["fields_filled"].append("title")
        except Exception as e:
            result["fields_failed"].append(f"title: {e}")

        # Fill description
        try:
            page.fill(LOOPMASTERS_SELECTORS["release_description"], description)
            result["fields_filled"].append("description")
        except Exception as e:
            result["fields_failed"].append(f"description: {e}")

        # Select genre
        try:
            page.select_option(LOOPMASTERS_SELECTORS["genre_select"], label=genre)
            time.sleep(0.5)
            result["fields_filled"].append("genre")
        except Exception as e:
            result["fields_failed"].append(f"genre: {e}")

        # Select subgenre
        if subgenre:
            try:
                page.select_option(LOOPMASTERS_SELECTORS["subgenre_select"], label=subgenre)
                time.sleep(0.5)
                result["fields_filled"].append("subgenre")
            except Exception as e:
                result["fields_failed"].append(f"subgenre: {e}")

        # BPM
        try:
            page.fill(LOOPMASTERS_SELECTORS["bpm_input"], str(bpm))
            result["fields_filled"].append("bpm")
        except Exception as e:
            result["fields_failed"].append(f"bpm: {e}")

        # Key
        try:
            page.fill(LOOPMASTERS_SELECTORS["key_input"], key)
            result["fields_filled"].append("key")
        except Exception as e:
            result["fields_failed"].append(f"key: {e}")

        # Upload file
        if file_path and Path(file_path).exists():
            try:
                page.set_input_files(LOOPMASTERS_SELECTORS["upload_file"], file_path)
                time.sleep(2)
                result["fields_filled"].append("file")
            except Exception as e:
                result["fields_failed"].append(f"file: {e}")

        # Save as draft
        try:
            page.click(LOOPMASTERS_SELECTORS["save_draft_btn"], timeout=5000)
            time.sleep(1)
            result["fields_filled"].append("save_draft")
        except Exception as e:
            result["fields_failed"].append(f"save_draft: {e}")

        # Screenshot
        screenshot_dir = Path("/home/j_kro/.hermes/profiles/music-producer/cache/scratch/loopmasters-draft")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"loopmasters_draft_{ts}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot_path"] = str(screenshot_path)
        result["url"] = page.url

        logger.info("Loopmasters form filled to DRAFT state. NOT submitting.")
        return result
