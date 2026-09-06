#!/usr/bin/env python3
"""Gate: analyze stage — enforce the performance-report contract.

Blocks advance if:
- report.json missing
- Source not declared (youtube_analytics_api or youtube_studio_cdp)
- Required metrics present and plausible (CTR 0-100, retention 0-100,
  rpm >= 0, AVD <= video duration)
- Insufficient data (<100 views) is flagged, not hidden behind a keep/stop
- video_id matches upload-report.json (after path reconciliation)
- Decision matches data: keep/test/stop consistent with thresholds
- oracle_feedback is present
Exit 0 = PASS, exit 1 = FAIL with the failing check. No side effects.
"""
import json, sys
from pathlib import Path

REQUIRED_METRICS = ["views", "impressions", "ctr_percent",
                    "avg_view_duration_seconds", "retention_30s_percent"]
VALID_SOURCES = ("youtube_analytics_api", "youtube_studio_cdp")

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def resolve_upload_report(camp):
    """Reconcile the upload-report.json vs metadata.json contract mismatch.

    The stage spec says 'campaigns/<name>/metadata/upload-report.json', but the
    actual published artifact lives at 'campaigns/<name>/metadata.json'.
    Prefer metadata.json (canonical today); fall back to the spec path.
    """
    spec_path = camp / "metadata" / "upload-report.json"
    canonical = camp / "metadata.json"
    if canonical.exists():
        return canonical
    if spec_path.exists():
        return spec_path
    return None

def find_report(camp):
    """Locate performance report.json. Prefer the spec path, fall back to
    campaign-root analysis files."""
    spec_path = camp / "performance" / "report.json"
    if spec_path.exists():
        return spec_path
    return None

def pluck_num(d, key):
    v = d.get(key)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def main():
    if len(sys.argv) < 2:
        fail("usage: gate_analyze.py <campaign-dir>")
    camp = Path(sys.argv[1])

    # 1) Report exists
    report_path = find_report(camp)
    if not report_path:
        fail("performance/report.json missing — run the analyst stage first")
    try:
        r = json.loads(report_path.read_text())
    except json.JSONDecodeError as e:
        fail(f"performance/report.json parse error: {e}")
    metrics = r.get("metrics", {})

    # 2) Source declared and real
    source = r.get("source")
    if source not in VALID_SOURCES:
        fail(f"source '{source}' not in {VALID_SOURCES}")

    # 3) Plausibility bounds
    views = pluck_num(metrics, "views")
    if views is None or views < 0:
        fail(f"views implausible: {metrics.get('views')}")

    ctr = pluck_num(metrics, "ctr_percent")
    if ctr is None or not (0 <= ctr <= 100):
        fail(f"ctr_percent implausible: {metrics.get('ctr_percent')}")

    retention = pluck_num(metrics, "retention_30s_percent")
    if retention is None or not (0 <= retention <= 100):
        fail(f"retention_30s_percent implausible: {metrics.get('retention_30s_percent')}")

    rpm = pluck_num(metrics, "rpm")
    if rpm is None or rpm < 0:
        fail(f"rpm non-negative violated: {metrics.get('rpm')}")

    duration = pluck_num(r, "video_duration_seconds")
    avd = pluck_num(metrics, "avg_view_duration_seconds")
    if duration and avd and avd > duration:
        fail(f"avg_view_duration_seconds {avd}s > video duration {duration}s")

    # 4) All required metrics present (non-null)
    missing = [m for m in REQUIRED_METRICS if metrics.get(m) is None]
    if missing:
        fail(f"missing required metrics: {', '.join(missing)}")

    # 5) Insufficient-data flag when views < 100
    if views < 100:
        decision = r.get("decision", "")
        reasoning = r.get("reasoning", "")
        if decision != "test" and "insufficient" not in reasoning.lower():
            fail(f"views={views} (<100) but decision={decision!r} not 'test' — flag insufficient data")

    # 6) Video ID matches upload report (reconciled path)
    upload_report = resolve_upload_report(camp)
    if upload_report is None:
        fail("no upload-report.json and no metadata.json — cannot verify video_id")
    try:
        ur = json.loads(upload_report.read_text())
    except json.JSONDecodeError as e:
        fail(f"upload-report/metadata.json parse error: {e}")
    report_vid = r.get("video_id")
    report_vid_expected = ur.get("video_id")
    if report_vid_expected and report_vid != report_vid_expected:
        fail(f"video_id {report_vid!r} != upload-report {report_vid_expected!r}")
    if not report_vid:
        fail("report.json missing video_id")

    # 7) Decision consistency with data (keep/test/stop thresholds)
    decision = r.get("decision")
    if views >= 100:
        ctr_val = float(ctr)
        avd_val = float(avd)
        ret_val = float(retention)
        if decision == "stop":
            if not (ctr_val < 2 and avd_val < 30 and ret_val < 40):
                fail("decision='stop' but metrics don't meet stop thresholds "
                     "(CTR<2, AVD<30, retention<40%)")
        elif decision == "keep":
            if not (ctr_val >= 4 and avd_val >= 50 and ret_val >= 55):
                fail("decision='keep' but metrics don't meet keep thresholds "
                     "(CTR>=4, AVD>=50, retention>=55%)")

    # 8) Oracle feedback present
    if not r.get("oracle_feedback"):
        fail("oracle_feedback missing — analyst must feed weight adjustments back to routing")

    print(f"video_id={report_vid} source={source} views={views} CTR={ctr}% AVD={avd}s")
    print(f"decision={decision} retention={retention}% rpm={rpm}")
    print(f"oracle_feedback present={bool(r.get('oracle_feedback'))}")
    print(f"PASS: analyze gate (video {report_vid}, source {source})")
    sys.exit(0)

if __name__ == "__main__":
    main()