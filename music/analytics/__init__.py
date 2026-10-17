"""music/analytics/ — lane ROI analytics and tracking.

Measures which genre x lane combinations actually earn. Feeds results back
into the genre registry cadence (oracle-style weight update). Produces a
weekly music digest.

Every metric that cannot be measured prints FAILED: <reason> and exits
non-zero. Never a false 0.

Research basis (2026-10-09):
  - DistroKid: NO public API. TSV export from distrokid.com/bank/details/
    is the only data source. (deepwiki.com/api-evangelist/distrokid)
  - YouTube Analytics API v2: OAuth 2.0, metrics=views,estimatedRevenue,
    audienceWatchRatio,cpm. (developers.google.com/youtube/analytics)
  - Existing tools: betterkid (TSV parser), music-streaming-royalty-analyzer-app
"""
