#!/usr/bin/env python3
"""Consumer: read analyst performance reports and update the oracle watchlist.

Watches the performance/ directory for new report.json files and appends
weight-adjustment suggestions to performance/oracle-watchlist.md.

Only produces proposals — j_kro must approve before the brain updates.

Usage:
    python3 scripts/automation/oracle-consumer.py [campaign-dir ...]

Without args, scans all campaigns for new/updated reports.

Outputs a machine-readable JSON manifest on stdout for the cron driver.
"""
import json, sys, os
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(os.environ.get("REPO", os.path.expanduser("~/Projects/ai-content-pipeline")))
WATCHLIST = REPO / "performance" / "oracle-watchlist.md"
REPORTS_DIR = REPO / "performance"

# Weight-adjustment heuristics (tentative, pending j_kro approval)
THRESHOLDS = {
    "keep": {"ctr": 4.0, "avd": 50.0, "retention30": 55.0},
    "stop": {"ctr": 2.0, "avd": 30.0, "retention30": 40.0},
}

def load_watchlist():
    if WATCHLIST.exists():
        return WATCHLIST.read_text()
    return "# Oracle Watchlist — Niche Scoring\n\n"

def parse_report(path):
    try:
        r = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return {
        "campaign": r.get("campaign", path.parent.name),
        "video_id": r.get("video_id"),
        "source": r.get("source"),
        "decision": r.get("decision"),
        "metrics": r.get("metrics", {}),
        "oracle_feedback": r.get("oracle_feedback", {}),
        "pulled_at": r.get("pulled_at"),
        "path": str(path),
    }

def propose_weights(report):
    """Build a weight-adjustment proposal from a report."""
    m = report["metrics"]
    dec = report["decision"]
    proposals = {}
    ctr = m.get("ctr_percent")
    avd = m.get("avg_view_duration_seconds")
    ret = m.get("retention_30s_percent")
    views = m.get("views", 0)
    reasons = []

    if views < 100:
        return {"status": "insufficient_data", "reason": f"views={views} < 100"}

    if dec == "keep":
        proposals["watch_weight"] = "increase"
        reasons.append(f"KEEP: CTR {ctr}% >= {THRESHOLDS['keep']['ctr']}%, AVD {avd}s >= {THRESHOLDS['keep']['avd']}s, retention {ret}% >= {THRESHOLDS['keep']['retention30']}%")
    elif dec == "stop":
        proposals["watch_weight"] = "decrease"
        reasons.append(f"STOP: CTR {ctr}% < {THRESHOLDS['stop']['ctr']}%, AVD {avd}s < {THRESHOLDS['stop']['avd']}s, retention {ret}% < {THRESHOLDS['stop']['retention30']}%")
    elif dec == "test":
        proposals["watch_weight"] = "hold"
        reasons.append(f"TEST: mixed metrics — needs more data before weight change")

    # Title-keyword signal from oracle_feedback
    of = report.get("oracle_feedback", {})
    if of:
        proposals["oracle_feedback"] = of

    return {
        "status": "proposal",
        "weight_action": proposals.get("watch_weight", "hold"),
        "reasons": reasons,
        "oracle_feedback": of if of else None,
    }

def format_entry(report, proposal):
    campaign = report["campaign"]
    vid = report["video_id"] or "no-id"
    decision = report["decision"]
    m = report["metrics"]
    pulled = report.get("pulled_at", "unknown")
    weight = proposal.get("weight_action", "hold")
    reasons = proposal.get("reasons", [])

    lines = [
        f"## {campaign} ({vid})",
        f"",
        f"**Date:** {pulled}",
        f"**Decision:** {decision}  **Weight action:** {weight}",
        f"**CTR:** {m.get('ctr_percent')}%  **AVD:** {m.get('avg_view_duration_seconds')}s  **Retention@30s:** {m.get('retention_30s_percent')}%  **Views:** {m.get('views')}",
    ]
    if reasons:
        lines.append("**Rationale:**")
        for r in reasons:
            lines.append(f"- {r}")
    if proposal.get("oracle_feedback"):
        lines.append("**Oracle feedback:**")
        lines.append(f"- {json.dumps(proposal['oracle_feedback'])}")
    lines.append("**Status:** PROPOSAL — pending j_kro approval. No scoring weights changed until approved.")
    lines.append("")
    return "\n".join(lines)

def already_in_watchlist(watchlist_text, campaign, video_id):
    return campaign in watchlist_text and (video_id in watchlist_text if video_id else True)

def main():
    if len(sys.argv) > 1:
        targets = [Path(a) for a in sys.argv[1:]]
    else:
        targets = sorted((REPO / "performance").glob("*/report.json"))

    watchlist = load_watchlist()
    proposals = []
    new_entries = []

    for target in targets:
        if not target.exists():
            continue
        report = parse_report(target)
        if not report:
            continue
        proposal = propose_weights(report)
        if proposal.get("status") == "insufficient_data":
            continue
        # Skip if already in watchlist (avoid duplicates)
        if already_in_watchlist(watchlist, report["campaign"], report["video_id"]):
            continue
        entry = format_entry(report, proposal)
        new_entries.append(entry)
        proposals.append({
            "campaign": report["campaign"],
            "video_id": report["video_id"],
            "decision": report["decision"],
            "weight_action": proposal["weight_action"],
            "reasons": proposal["reasons"],
            "path": str(target),
        })

    if new_entries:
        appended = "\n".join(new_entries)
        updated = watchlist.rstrip() + "\n" + appended
        WATCHLIST.write_text(updated)

    manifest = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "proposals": proposals,
        "watchlist_updated": bool(new_entries),
        "watchlist_path": str(WATCHLIST),
    }
    print(json.dumps(manifest, indent=2))
    if new_entries:
        print(f"\nOracle watchlist updated: {len(new_entries)} proposal(s) appended. Pending j_kro approval.", file=sys.stderr)

if __name__ == "__main__":
    main()
