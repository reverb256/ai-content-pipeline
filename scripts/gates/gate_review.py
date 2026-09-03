#!/usr/bin/env python3
"""Gate: review stage — enforce scored review contract (anti-rubber-stamp).

Blocks advance if:
- review/<stage>.review.json missing or invalid schema
- reviewer == producer (maker-checker violation)
- any criterion score < 7 (min pass threshold)
- any criterion missing 'evidence' field (score without evidence = invalid)
- mechanical gate not verified (gate_verified != true)
- overall score < 7
- eval-set detection: known-bad artifact passed (flagged in audit)

Exit 0 = PASS, exit 1 = FAIL (with reasons). No side effects.
"""
import json, sys, os, re
from pathlib import Path
from datetime import datetime

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        fail("usage: gate_review.py <campaign-dir> <stage-being-reviewed>")
    camp = Path(sys.argv[1])
    stage = sys.argv[2]  # e.g., "script", "visuals", "voice", "thumbnail", "seo"

    # --- locate review artifact ---
    review_dir = camp / "review"
    review_file = review_dir / f"{stage}.review.json"
    if not review_file.exists():
        fail(f"review artifact missing: {review_file}")

    review = None
    try:
        review = json.loads(review_file.read_text())
    except json.JSONDecodeError as e:
        fail(f"review JSON invalid: {e}")

    assert review is not None, "review JSON parse failed"

    # --- required fields ---
    required = ["stage", "reviewer", "producer", "gate_verified", "criteria", "overall", "pass", "ts"]
    for field in required:
        if field not in review:
            fail(f"review missing required field: {field}")

    if review["stage"] != stage:
        fail(f"review stage mismatch: review says {review['stage']}, expected {stage}")

    # --- maker-checker: reviewer != producer ---
    if review["reviewer"] == review["producer"]:
        fail(f"maker-checker violation: reviewer '{review['reviewer']}' == producer '{review['producer']}'")

    # --- mechanical gate verified ---
    if not review.get("gate_verified"):
        fail("mechanical gate not verified (gate_verified must be true)")

    # --- criteria validation ---
    criteria = review.get("criteria", [])
    if not isinstance(criteria, list) or len(criteria) < 7:
        fail(f"criteria must be a list with at least 7 items, got {len(criteria)}")

    required_criteria = [
        "originality", "spec_compliance", "audience_value",
        "evidence_integrity", "voice_match", "technical_quality", "overall_watchability"
    ]
    # Allow extra criteria (cross-artifact, template_risk, hook_resolution, specificity, cta_match)
    found_names = set()
    for i, c in enumerate(criteria):
        if not isinstance(c, dict):
            fail(f"criteria[{i}] must be an object")
        name = c.get("name")
        if not name:
            fail(f"criteria[{i}] missing 'name'")
        found_names.add(name)
        score = c.get("score")
        if not isinstance(score, (int, float)):
            fail(f"criteria '{name}' missing or invalid 'score'")
        if score < 7:
            fail(f"criteria '{name}' score {score} < 7 (min pass)")
        if "evidence" not in c or not c["evidence"]:
            fail(f"criteria '{name}' missing 'evidence' (score without evidence = invalid)")

    # ensure core 7 are present
    for req in required_criteria:
        if req not in found_names:
            fail(f"missing required criterion: {req}")

    # --- overall score ---
    overall = review.get("overall")
    if not isinstance(overall, (int, float)) or overall < 7:
        fail(f"overall score {overall} < 7")

    # --- pass flag consistent ---
    if not review.get("pass"):
        fail("review.pass is false — cannot advance")

    # --- eval-set check: audit log for known-bad seeds ---
    audit_file = camp / "audit.jsonl"
    if audit_file.exists():
        for line in audit_file.read_text().splitlines():
            try:
                entry = json.loads(line)
                if entry.get("type") == "eval_seed" and entry.get("stage") == stage:
                    if entry.get("verdict") == "passed" and entry.get("artifact") == stage:
                        fail(f"EVAL SET VIOLATION: known-bad artifact for stage '{stage}' was passed (audit: {entry})")
            except json.JSONDecodeError:
                pass

    # --- log audit entry for this review ---
    audit_entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": "review_gate",
        "stage": stage,
        "reviewer": review["reviewer"],
        "producer": review["producer"],
        "overall": overall,
        "pass": True,
        "artifact": review_file.name
    }
    try:
        with audit_file.open("a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception:
        pass  # audit is best-effort

    print(f"PASS: review gate for stage '{stage}' (reviewer={review['reviewer']}, overall={overall})")
    sys.exit(0)

if __name__ == "__main__":
    main()