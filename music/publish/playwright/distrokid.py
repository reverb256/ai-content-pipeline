"""DistroKid Playwright adapter.

Automates release upload on the logged-in DistroKid session.

Selectors derived from two community implementations:
  1. Sam-r-ai/Automated_Distrokid_Uploader (webupload.py) — Selenium-based,
     exercises the full upload flow including modal confirmations.
  2. hlushchukm/Distrokid — unofficial Go wrapper from iOS app reversal;
     confirms API base URL (https://distrokid.com/api/v1) and auth pattern.

A third reference, distrokid-userjs/auto-input (userscript), provided
additional field-level selectors cross-checked against the form DOM.

This adapter NEVER creates accounts, NEVER hardcodes credentials, and
stops at DRAFT (does not submit a live release).
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from .session import SessionHelper, RateLimited, SessionError

logger = logging.getLogger(__name__)

# Selectors derived from reference implementations.
# Source: Sam-r-ai/Automated_Distrokid_Uploader/webupload.py (lines 55-140)
# Source: distrokid-userjs/auto-input/distrokid-auto-input.user.js (lines 80-200)
SELECTORS = {
    # Upload flow entry
    "upload_music_link": 'a:has-text("Upload music")',
    "snapchat_checkbox": "#chksnap",
    "snapchat_confirm": ".swal2-confirm",
    "roblox_checkbox": "#chkroblox",
    "roblox_confirm": "#confirm-chk-1",
    "roblox_confirm_2": "#confirm-chk-2",
    "roblox_confirm_3": "#confirm-chk-3",
    "roblox_confirm_4": "#confirm-chk-4",
    "roblox_final_confirm": ".swal2-confirm",
    "song_count_select": "#howManySongsOnThisAlbum",
    "genre_primary": "#genrePrimary",
    "sub_genre_primary": "#subGenrePrimary",
    "genre_secondary": "#genreSecondary",
    "sub_genre_secondary": "#subGenreSecondary",
    "release_date": "#release-date-dp",
    "artwork_input": "#artwork",
    "album_title": "#albumTitleInput",
    "track_title": 'input[placeholder="Track {idx} title"]',
    "track_upload": "#js-track-upload-{idx}",
    "track_lyrics_exempt": '#js-track-table-{idx} .dkRequiredForSpotify:nth-child(21) label:nth-child(2) div:nth-child(2)',
    "songwriter_type": "#js-track-1-songwriter-1 .coolSelect",
    "songwriter_first": 'input[name="songwriter_real_name_first1"]',
    "songwriter_last": 'input[name="songwriter_real_name_last1"]',
    "copy_songwriters": "#js-copy-songwriters-link-1 div:nth-child(2)",
    "mandatory_youtube": "#mandatoryCheckboxYouTube .container-flex",
    "mandatory_promo": "#mandatoryCheckboxPromoServices .container-flex",
    "mandatory_recorded": "#mandatoryAreyousurerecorded .radio-flex",
    "mandatory_other_artist": "#mandatoryAreyousureotherartist .container-flex",
    "mandatory_tandc": "#mandatoryAreyousuretandc .container-flex",
    "mandatory_snap": "#mandatoryCheckboxSnap b",
    "non_standard_caps": "#nonStandardCapsCheckbox .container-flex",
    "done_button": "#doneButton",
}

# Genre value mapping (from auto-input userscript DEFAULT_PRESET comments)
GENRE_VALUES = {
    "Electronic": "9",
    "Pop": "24",
    "Jazz": "20",
    "Alternative": "1",
    "Hip Hop/Rap": "5",
    "Rock": "4",
    "Country": "7",
    "R&B/Soul": "10",
    "Classical": "15",
    "Folk": "14",
    "Reggae": "11",
    "Blues": "12",
    "Latin": "16",
    "World": "17",
    "Children's": "18",
    "Holiday": "19",
    "Christian/Gospel": "21",
    "New Age": "22",
    "Comedy": "23",
    "Spoken Word": "25",
}

# Sub-genre option values — re-derived from the live form 2026-10-09.
# These are the real <option value> codes for the Electronic primary genre
# (genrePrimary value "9"); DistroKid renumbered them from the older 9_N scheme.
SUB_GENRE_VALUES = {
    "Big Room": "57",
    "Breaks": "35",
    "Chill Out": "36",
    "Deep House": "55",
    "Drum & Bass": "37",
    "Dubstep": "38",
    "Electro House": "39",
    "Electronica / Downtempo": "40",
    "Funk / Soul / Disco": "41",
    "Glitch Hop": "42",
    "Hard Dance": "43",
    "Hardcore / Hard Techno": "44",
    "Hip-Hop / R&B": "45",
    "House": "46",
}

TRACK_COUNT_OPTIONS = {
    1: "1 song",
    2: "2 songs",
    3: "3 songs",
    4: "4 songs",
    5: "5 songs",
    6: "6 songs",
    7: "7 songs",
    8: "8 songs",
    9: "9 songs",
    10: "10 songs",
    11: "11 songs",
    12: "12 songs",
    13: "13 songs",
    14: "14 songs",
    15: "15 songs",
}


class DistroKidAdapter:
    """Upload adapter for DistroKid. Stops at DRAFT, never submits."""

    def __init__(self, session: SessionHelper):
        self.session = session

    def check_existing(self, page: Page, album_title: str) -> Optional[str]:
        """Idempotency check: search existing releases for this title.
        Returns the URL of the existing release if found."""
        page.goto("https://distrokid.com/releases")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Check for rate limiting
        if self.session.is_rate_limited(page):
            raise RateLimited("Rate limited on releases page")

        # Search for the album title in the releases table
        existing = page.query_selector_all(f'tr:has-text("{album_title}")')
        if existing:
            link = existing[0].query_selector("a")
            if link:
                href = link.get_attribute("href")
                logger.info("Found existing release: %s", href)
                return f"https://distrokid.com{href}" if href and href.startswith("/") else href
        return None

    def fill_upload_form(
        self,
        page: Page,
        album_title: str,
        track_titles: list[str],
        artwork_path: Optional[str] = None,
        genre_primary: str = "Electronic",
        sub_genre_primary: str = "",
        genre_secondary: str = "",
        sub_genre_secondary: str = "",
        release_date: str = "",
        songwriter_first: str = "",
        songwriter_last: str = "",
    ) -> dict:
        """Fill the DistroKid upload form. Returns a dict with field values
        for verification. Stops at DRAFT (does not click doneButton)."""

        result = {
            "album_title": album_title,
            "track_titles": track_titles,
            "fields_filled": [],
            "fields_failed": [],
            "artwork_uploaded": False,
            "screenshot_path": None,
        }

        # Navigate to upload page
        page.goto("https://distrokid.com/new")
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        if self.session.is_rate_limited(page):
            raise RateLimited("Rate limited on upload page")

        # Handle Snapchat checkbox modal
        try:
            snap = page.query_selector(SELECTORS["snapchat_checkbox"])
            if snap and snap.is_visible():
                snap.click()
                time.sleep(0.5)
                page.click(SELECTORS["snapchat_confirm"])
                time.sleep(0.5)
                result["fields_filled"].append("snapchat")
        except Exception as e:
            logger.debug("Snapchat modal not present: %s", e)

        # Handle Roblox checkbox modal
        try:
            roblox = page.query_selector(SELECTORS["roblox_checkbox"])
            if roblox and roblox.is_visible():
                roblox.click()
                time.sleep(0.5)
                for sel in [
                    SELECTORS["roblox_confirm"],
                    SELECTORS["roblox_confirm_2"],
                    SELECTORS["roblox_confirm_3"],
                    SELECTORS["roblox_confirm_4"],
                ]:
                    try:
                        page.click(sel, timeout=3000)
                        time.sleep(0.3)
                    except Exception:
                        pass
                page.click(SELECTORS["roblox_final_confirm"])
                time.sleep(0.5)
                result["fields_filled"].append("roblox")
        except Exception as e:
            logger.debug("Roblox modal not present: %s", e)

        # Song count — select by VALUE (label text changed to "N song (a single)";
        # the <option value> is stable). Verified live 2026-10-09.
        num_tracks = len(track_titles)
        if 1 <= num_tracks <= 34:
            try:
                page.select_option(
                    SELECTORS["song_count_select"],
                    value=str(num_tracks),
                )
                time.sleep(1.0)  # let the form advance its layout step
                result["fields_filled"].append("song_count")
            except Exception as e:
                result["fields_failed"].append(f"song_count: {e}")

        # Genre primary
        if genre_primary in GENRE_VALUES:
            try:
                page.select_option(
                    SELECTORS["genre_primary"],
                    value=GENRE_VALUES[genre_primary],
                )
                time.sleep(0.5)
                result["fields_filled"].append("genre_primary")
            except Exception as e:
                result["fields_failed"].append(f"genre_primary: {e}")

        # Sub-genre primary (options populate after primary genre is set)
        if sub_genre_primary and sub_genre_primary in SUB_GENRE_VALUES:
            try:
                page.wait_for_selector(SELECTORS["sub_genre_primary"], timeout=5000)
                page.select_option(
                    SELECTORS["sub_genre_primary"],
                    value=SUB_GENRE_VALUES[sub_genre_primary],
                )
                time.sleep(0.5)
                result["fields_filled"].append("sub_genre_primary")
            except Exception as e:
                result["fields_failed"].append(f"sub_genre_primary: {e}")

        # Genre secondary
        if genre_secondary and genre_secondary in GENRE_VALUES:
            try:
                page.select_option(
                    SELECTORS["genre_secondary"],
                    value=GENRE_VALUES[genre_secondary],
                )
                time.sleep(0.5)
                result["fields_filled"].append("genre_secondary")
            except Exception as e:
                result["fields_failed"].append(f"genre_secondary: {e}")

        # Sub-genre secondary
        if sub_genre_secondary and sub_genre_secondary in SUB_GENRE_VALUES:
            try:
                page.wait_for_selector(SELECTORS["sub_genre_secondary"], timeout=5000)
                page.select_option(
                    SELECTORS["sub_genre_secondary"],
                    value=SUB_GENRE_VALUES[sub_genre_secondary],
                )
                time.sleep(0.5)
                result["fields_filled"].append("sub_genre_secondary")
            except Exception as e:
                result["fields_failed"].append(f"sub_genre_secondary: {e}")

        # Release date
        if release_date:
            try:
                page.fill(SELECTORS["release_date"], release_date)
                result["fields_filled"].append("release_date")
            except Exception as e:
                result["fields_failed"].append(f"release_date: {e}")

        # Artwork upload
        if artwork_path and Path(artwork_path).exists():
            try:
                page.set_input_files(SELECTORS["artwork_input"], artwork_path)
                time.sleep(2)
                result["artwork_uploaded"] = True
                result["fields_filled"].append("artwork")
            except Exception as e:
                result["fields_failed"].append(f"artwork: {e}")

        # Album title
        try:
            page.fill(SELECTORS["album_title"], album_title)
            result["fields_filled"].append("album_title")
        except Exception as e:
            result["fields_failed"].append(f"album_title: {e}")

        # Track titles and file uploads
        for idx, title in enumerate(track_titles, start=1):
            track_sel = SELECTORS["track_title"].format(idx=idx)
            upload_sel = SELECTORS["track_upload"].format(idx=idx)
            try:
                page.wait_for_selector(track_sel, timeout=10000)
                page.fill(track_sel, title)
                result["fields_filled"].append(f"track_{idx}_title")
            except Exception as e:
                result["fields_failed"].append(f"track_{idx}_title: {e}")

            # Upload track file if provided
            track_file = f"{title}.mp3"
            track_path = Path(track_file)
            if track_path.exists():
                try:
                    page.set_input_files(upload_sel, str(track_path))
                    time.sleep(1)
                    result["fields_filled"].append(f"track_{idx}_file")
                except Exception as e:
                    result["fields_failed"].append(f"track_{idx}_file: {e}")

            # Click "This song is instrumental and contains no lyrics".
            # The radio input name carries a per-track UUID (instrumental_<uuid>),
            # so target the stable visible label text, not the input name.
            try:
                page.get_by_text(
                    "This song is instrumental and contains no lyrics",
                    exact=True,
                ).first.click(timeout=5000)
                result["fields_filled"].append(f"track_{idx}_no_lyrics")
            except Exception as e:
                result["fields_failed"].append(f"track_{idx}_no_lyrics: {e}")

        # Songwriter info
        if songwriter_first and songwriter_last:
            try:
                page.select_option(SELECTORS["songwriter_type"], label="Music")
                time.sleep(0.5)
                page.fill(SELECTORS["songwriter_first"], songwriter_first)
                page.fill(SELECTORS["songwriter_last"], songwriter_last)
                result["fields_filled"].append("songwriter")

                # Copy to all tracks
                page.click(SELECTORS["copy_songwriters"])
                time.sleep(0.5)
                page.click(SELECTORS["snapchat_confirm"])
                time.sleep(0.5)
                page.click(SELECTORS["snapchat_confirm"])
                time.sleep(0.5)
                result["fields_filled"].append("songwriter_copy_all")
            except Exception as e:
                result["fields_failed"].append(f"songwriter: {e}")

        # Mandatory checkboxes
        for key in [
            "mandatory_youtube",
            "mandatory_promo",
            "mandatory_recorded",
            "mandatory_other_artist",
            "mandatory_tandc",
            "mandatory_snap",
        ]:
            try:
                el = page.query_selector(SELECTORS[key])
                if el and el.is_visible():
                    el.click()
                    time.sleep(0.2)
                    result["fields_filled"].append(key)
            except Exception as e:
                result["fields_failed"].append(f"{key}: {e}")

        # Non-standard caps (optional)
        try:
            el = page.query_selector(SELECTORS["non_standard_caps"])
            if el and el.is_visible():
                el.click()
                result["fields_filled"].append("non_standard_caps")
        except Exception:
            pass

        # Capture screenshot of filled form (DRAFT state)
        screenshot_dir = Path("/home/j_kro/.hermes/profiles/music-producer/cache/scratch/distrokid-draft")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"distrokid_draft_{ts}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot_path"] = str(screenshot_path)

        # DO NOT CLICK doneButton — stop at DRAFT
        logger.info("Form filled to DRAFT state. NOT submitting.")
        return result

    def upload_release(
        self,
        album_title: str,
        track_titles: list[str],
        artwork_path: Optional[str] = None,
        genre_primary: str = "Electronic",
        sub_genre_primary: str = "",
        genre_secondary: str = "",
        sub_genre_secondary: str = "",
        release_date: str = "",
        songwriter_first: str = "",
        songwriter_last: str = "",
        skip_if_exists: bool = True,
    ) -> dict:
        """Full upload flow. Idempotent: checks for existing release first.

        Returns a dict with:
          - status: "draft" | "exists" | "error"
          - url: release URL if found/created
          - fields_filled: list of successfully filled fields
          - fields_failed: list of fields that failed
          - screenshot_path: path to DRAFT screenshot
        """
        page = self.session.new_page()
        try:
            # Idempotency check
            if skip_if_exists:
                existing_url = self.check_existing(page, album_title)
                if existing_url:
                    return {
                        "status": "exists",
                        "url": existing_url,
                        "fields_filled": [],
                        "fields_failed": [],
                        "screenshot_path": None,
                    }

            # Fill the form
            result = self.fill_upload_form(
                page,
                album_title=album_title,
                track_titles=track_titles,
                artwork_path=artwork_path,
                genre_primary=genre_primary,
                sub_genre_primary=sub_genre_primary,
                genre_secondary=genre_secondary,
                sub_genre_secondary=sub_genre_secondary,
                release_date=release_date,
                songwriter_first=songwriter_first,
                songwriter_last=songwriter_last,
            )

            result["status"] = "draft"
            result["url"] = page.url
            return result

        except RateLimited:
            raise
        except Exception as e:
            logger.error("Upload failed: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "url": page.url,
                "fields_filled": [],
                "fields_failed": [],
                "screenshot_path": None,
            }
        finally:
            page.close()
