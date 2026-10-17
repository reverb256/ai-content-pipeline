"""Fab/Unreal publisher portal Playwright adapter.

Automates asset submission on the logged-in Fab publisher account.
Fab (fab.com) is the Unreal Engine marketplace. Publisher onboarding
is human-gated; this adapter operates post-onboarding.

Selectors derived from the Fab publisher portal DOM structure.
Stops at DRAFT — does not submit for review.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from .session import SessionHelper, RateLimited

logger = logging.getLogger(__name__)

SELECTORS = {
    "new_asset_btn": 'button:has-text("Create new asset")',
    "asset_name": 'input[name="name"]',
    "asset_description": 'textarea[name="description"]',
    "category_select": 'select[name="category"]',
    "subcategory_select": 'select[name="subcategory"]',
    "tags_input": 'input[name="tags"]',
    "price_input": 'input[name="price"]',
    "engine_version": 'select[name="engineVersion"]',
    "upload_file": 'input[type="file"]',
    "thumbnail_upload": 'input[accept*="image"]',
    "submit_btn": 'button:has-text("Submit for review")',
    "save_draft_btn": 'button:has-text("Save draft")',
}


class FabAdapter:
    """Submit assets to the Fab/Unreal publisher portal."""

    def __init__(self, session: SessionHelper):
        self.session = session

    def submit_asset(
        self,
        page: Page,
        name: str,
        description: str,
        category: str,
        subcategory: str = "",
        tags: list[str] | None = None,
        price: float = 0.0,
        engine_version: str = "5.3",
        file_path: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
    ) -> dict:
        """Fill the Fab asset submission form. Stops at DRAFT.

        Returns a dict with field values and screenshot path.
        """
        result = {
            "name": name,
            "fields_filled": [],
            "fields_failed": [],
            "screenshot_path": None,
            "url": None,
        }

        page.goto("https://www.fab.com/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if self.session.is_rate_limited(page):
            raise RateLimited("Rate limited on Fab dashboard")

        # Click "Create new asset"
        try:
            page.click(SELECTORS["new_asset_btn"], timeout=10000)
            time.sleep(2)
            result["fields_filled"].append("new_asset_btn")
        except Exception as e:
            result["fields_failed"].append(f"new_asset_btn: {e}")

        # Fill name
        try:
            page.fill(SELECTORS["asset_name"], name)
            result["fields_filled"].append("name")
        except Exception as e:
            result["fields_failed"].append(f"name: {e}")

        # Fill description
        try:
            page.fill(SELECTORS["asset_description"], description)
            result["fields_filled"].append("description")
        except Exception as e:
            result["fields_failed"].append(f"description: {e}")

        # Select category
        try:
            page.select_option(SELECTORS["category_select"], label=category)
            time.sleep(0.5)
            result["fields_filled"].append("category")
        except Exception as e:
            result["fields_failed"].append(f"category: {e}")

        # Select subcategory
        if subcategory:
            try:
                page.select_option(SELECTORS["subcategory_select"], label=subcategory)
                time.sleep(0.5)
                result["fields_filled"].append("subcategory")
            except Exception as e:
                result["fields_failed"].append(f"subcategory: {e}")

        # Tags
        if tags:
            try:
                page.fill(SELECTORS["tags_input"], ", ".join(tags))
                result["fields_filled"].append("tags")
            except Exception as e:
                result["fields_failed"].append(f"tags: {e}")

        # Price
        if price > 0:
            try:
                page.fill(SELECTORS["price_input"], str(price))
                result["fields_filled"].append("price")
            except Exception as e:
                result["fields_failed"].append(f"price: {e}")

        # Engine version
        try:
            page.select_option(SELECTORS["engine_version"], label=engine_version)
            result["fields_filled"].append("engine_version")
        except Exception as e:
            result["fields_failed"].append(f"engine_version: {e}")

        # Upload file
        if file_path and Path(file_path).exists():
            try:
                page.set_input_files(SELECTORS["upload_file"], file_path)
                time.sleep(2)
                result["fields_filled"].append("file")
            except Exception as e:
                result["fields_failed"].append(f"file: {e}")

        # Upload thumbnail
        if thumbnail_path and Path(thumbnail_path).exists():
            try:
                page.set_input_files(SELECTORS["thumbnail_upload"], thumbnail_path)
                time.sleep(1)
                result["fields_filled"].append("thumbnail")
            except Exception as e:
                result["fields_failed"].append(f"thumbnail: {e}")

        # Save as draft (do NOT submit for review)
        try:
            page.click(SELECTORS["save_draft_btn"], timeout=5000)
            time.sleep(1)
            result["fields_filled"].append("save_draft")
        except Exception as e:
            result["fields_failed"].append(f"save_draft: {e}")

        # Screenshot
        screenshot_dir = Path("/home/j_kro/.hermes/profiles/music-producer/cache/scratch/fab-draft")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"fab_draft_{ts}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot_path"] = str(screenshot_path)
        result["url"] = page.url

        logger.info("Fab form filled to DRAFT state. NOT submitting for review.")
        return result
