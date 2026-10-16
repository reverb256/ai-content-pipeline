"""YouTube Analytics API v2 fetcher.

Pulls views, revenue, CTR, and audience retention for music videos.
Requires OAuth 2.0 credentials (client_secret.json) and a token file.

YouTube Analytics API v2 metrics used:
  - views
  - estimatedRevenue
  - estimatedAdRevenue
  - cpm
  - audienceWatchRatio (retention, dimensions=elapsedVideoTimeRatio)
  - relativeRetentionPerformance

Scopes needed:
  - https://www.googleapis.com/auth/yt-analytics.readonly
  - https://www.googleapis.com/auth/yt-analytics-monetary.readonly (for revenue)

Source: developers.google.com/youtube/analytics/metrics (verified 2026-10-09)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional


def fetch_youtube_metrics(
    channel_id: str,
    start_date: str,
    end_date: str,
    credentials_path: Path,
    token_path: Path,
) -> dict:
    """Fetch YouTube analytics for a channel.

    Args:
        channel_id: YouTube channel ID (UC...)
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        credentials_path: path to client_secret.json (OAuth 2.0)
        token_path: path to token.json (stored credentials)

    Returns:
        dict with keys: views, estimated_revenue, cpm, retention_30s, videos

    Raises:
        FileNotFoundError: credentials or token missing
        RuntimeError: API call failed
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "google-api-python-client not installed. "
            "Run: pip install google-api-python-client google-auth-httplib2"
        )

    if not credentials_path.is_file():
        raise FileNotFoundError(
            f"YouTube OAuth credentials not found: {credentials_path}. "
            f"Download from Google Console (YouTube Analytics API scope)."
        )

    SCOPES = [
        "https://www.googleapis.com/auth/yt-analytics.readonly",
        "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
    ]

    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    service = build("youtubeAnalytics", "v2", credentials=creds)

    # Channel-level report
    report = service.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedRevenue,estimatedAdRevenue,cpm",
    ).execute()

    views = 0
    revenue = 0.0
    cpm = 0.0
    if report.get("rows"):
        row = report["rows"][0]
        headers = [h["name"] for h in report["columnHeaders"]]
        values = dict(zip(headers, row))
        views = int(values.get("views", 0))
        revenue = float(values.get("estimatedRevenue", 0.0))
        cpm = float(values.get("cpm", 0.0))

    # Top videos report for per-video metrics
    top_videos = service.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        dimensions="video",
        metrics="views,estimatedRevenue",
        sort="-views",
        maxResults=10,
    ).execute()

    videos = []
    if top_videos.get("rows"):
        headers = [h["name"] for h in top_videos["columnHeaders"]]
        for row in top_videos["rows"]:
            vals = dict(zip(headers, row))
            videos.append({
                "video_id": vals.get("video", ""),
                "views": int(vals.get("views", 0)),
                "revenue": float(vals.get("estimatedRevenue", 0.0)),
            })

    # Retention report
    retention = service.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        dimensions="elapsedVideoTimeRatio",
        metrics="audienceWatchRatio,relativeRetentionPerformance",
        filters="video==all",
    ).execute()

    retention_30s = 0.0
    if retention.get("rows"):
        # elapsedVideoTimeRatio is 0.0-1.0; 30s retention ≈ ratio at 0.05 (30s/600s avg)
        # Use the first data point as a proxy for early retention
        headers = [h["name"] for h in retention["columnHeaders"]]
        for row in retention["rows"]:
            vals = dict(zip(headers, row))
            ratio = float(vals.get("elapsedVideoTimeRatio", 0))
            awr = float(vals.get("audienceWatchRatio", 0))
            if 0.03 <= ratio <= 0.08:  # ~30s window for a typical video
                retention_30s = awr
                break

    # CTR is not directly available from Analytics API; it comes from
    # the Data API (videos.list with statistics). We mark it as not measured.
    ctr = None

    return {
        "channel_id": channel_id,
        "start_date": start_date,
        "end_date": end_date,
        "views": views,
        "estimated_revenue": revenue,
        "cpm": cpm,
        "retention_30s": retention_30s,
        "ctr": ctr,
        "videos": videos,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 5:
        print("usage: python3 -m music.analytics.youtube_fetcher "
              "<channel_id> <start_date> <end_date> <credentials_path> [token_path]")
        return 2

    channel_id = argv[1]
    start_date = argv[2]
    end_date = argv[3]
    creds = Path(argv[4])
    token = Path(argv[5]) if len(argv) > 5 else Path.home() / ".config/youtube_token.json"

    try:
        result = fetch_youtube_metrics(channel_id, start_date, end_date, creds, token)
    except FileNotFoundError as e:
        print(f"FAILED: {e}")
        return 1
    except RuntimeError as e:
        print(f"FAILED: {e}")
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
