# Stage Spec — Analyze (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> This file is the contract the analyst bot reads before reporting performance
> and making keep/test/stop decisions. Data integrity is non-negotiable —
> fabricated metrics are worse than no metrics.

## STAGE
analyze

## BOT
analyst

## INPUT
- `campaigns/<name>/metadata/upload-report.json` — has the video ID.
- YouTube Analytics API or YouTube Studio CDP scrape — the SOURCE of truth
  for all performance numbers.
- `campaigns/<name>/metadata/seo.json` — metadata context (title, tags).
- `brain/playbooks/performance.md` — benchmark thresholds and decision rules.
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md`.

## OUTPUT
- `campaigns/<name>/performance/report.json`:
  ```json
  {
    "video_id": "<id>",
    "pulled_at": "<ISO timestamp>",
    "source": "youtube_analytics_api",
    "metrics": {
      "views": 0, "impressions": 0, "ctr_percent": 0.0,
      "avg_view_duration_seconds": 0, "avg_view_duration_percent": 0.0,
      "retention_30s_percent": 0.0, "retention_60s_percent": 0.0,
      "rpm": 0.0, "revenue": 0.0, "subscribers_gained": 0
    },
    "decision": "keep|test|stop",
    "reasoning": "<data-backed justification>",
    "oracle_feedback": {"weight_adjustments": {...}},
    "mechanical_gate": {"passed": true, "checks": {...}}
  }
  ```
- Kanban comment: key metrics, decision, gate result.

## SPEC (measurable)

### Metrics — pull REAL numbers, never fabricate
Pull the following from the YouTube Analytics API (or CDP scrape if API
unavailable). Every number must trace to a specific API response field:
- **Views** — total views.
- **Impressions** — times the thumbnail was shown.
- **CTR** — click-through rate (views / impressions × 100). Report as percent.
- **AVD** — average view duration (seconds AND percent of video length).
- **Retention** — % viewers retained at 30s and 60s (from retention curve).
- **RPM** — revenue per mille (if monetized).
- **Subscribers gained** — attributed subscriber change.

### Decision framework (data-backed)
Based on `performance.md` thresholds:
- **KEEP** — CTR ≥ 4%, AVD ≥ 50%, retention@30s ≥ 55%. The video performs
  at or above benchmark → continue this angle/format.
- **TEST** — metrics are mixed (some above, some below) → needs more data
  or a variant test before deciding.
- **STOP** — CTR < 2%, AVD < 30%, retention@30s < 40%. The video
  underperforms → abandon this angle/format.

The decision MUST reference specific numbers. "Feels off" is not a reason.

### Oracle weight feedback
Feed insights back to the oracle/routing layer:
- Which title keywords correlated with high CTR.
- Which hook patterns correlated with retention@30s.
- Which video length/format correlated with AVD.
- Suggested weight adjustments for future video routing.

### No-fabrication rule
- NEVER invent metrics because the API returned an error or the video is too
  new for data. If data is unavailable, report `null` for that metric and
  note the reason.
- NEVER copy metrics from another video, a template, or a plausible estimate.
- If the video has <100 views, flag as "insufficient data" rather than
  making a keep/test/stop call.

## MECHANICAL GATE (BLOCKS — run before commenting done)
```python
import json, sys
p = "campaigns/<name>/performance/report.json"
r = json.load(open(p))
metrics = r["metrics"]
checks = {}

# 1) Source is declared and real
checks["source_declared"] = r.get("source") in ("youtube_analytics_api", "youtube_studio_cdp")

# 2) No obviously fabricated numbers (plausibility bounds)
checks["views_plausible"] = metrics["views"] >= 0
checks["ctr_plausible"] = 0 <= metrics["ctr_percent"] <= 100
checks["avd_not_exceed_duration"] = metrics["avg_view_duration_seconds"] <= (r.get("video_duration_seconds", 9999))
checks["retention_plausible"] = 0 <= metrics["retention_30s_percent"] <= 100
checks["rpm_non_negative"] = metrics["rpm"] >= 0

# 3) Decision matches the data (simple consistency check)
if metrics.get("views", 0) < 100:
    checks["insufficient_data_flag"] = r["decision"] == "test" or "insufficient" in r.get("reasoning", "").lower()
else:
    checks["insufficient_data_flag"] = True  # N/A when enough data

# 4) All required metrics present (non-null)
required = ["views", "impressions", "ctr_percent", "avg_view_duration_seconds", "retention_30s_percent"]
checks["all_metrics_present"] = all(metrics.get(k) is not None for k in required)

# 5) Video ID matches upload report
upload_report = json.load(open("campaigns/<name>/metadata/upload-report.json"))
checks["video_id_matches"] = r.get("video_id") == upload_report.get("video_id")

all_pass = all(checks.values())
print(f"views={metrics['views']} CTR={metrics['ctr_percent']}% AVD={metrics['avg_view_duration_seconds']}s")
print(f"decision={r['decision']} checks={checks}")
print("PASS" if all_pass else "FAIL")
```
Any check failing → the bot MUST re-query the API, correct the metric, and
re-run. Do NOT advance with fabricated or inconsistent data.

## SCORED REVIEW (1-10, min pass 7)
1. **Data integrity** — every number traces to an API response, not invented.
2. **Metric completeness** — all required metrics present (or null with reason).
3. **Decision soundness** — keep/test/stop is justified by specific thresholds.
4. **Oracle feedback quality** — actionable insights fed back to routing.
5. **Context awareness** — accounts for video age, traffic source, and sample size.
6. **No false confidence** — insufficient data is flagged, not hidden.
7. **Actionability** — the report tells the human what to do next.

PASS: all ≥ 7. FAIL: feedback must name the metric/field + exact fix.

## DONE WHEN
report.json exists, all metrics trace to an API source (no fabrication),
decision is data-backed with specific thresholds referenced, oracle feedback
is present, video ID matches the upload report, mechanical gate PASSED, and
the comment reports key metrics + decision + gate result.
