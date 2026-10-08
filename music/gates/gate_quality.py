#!/usr/bin/env python3
"""gate_quality — routes the track to an independent reviewer on a
DIFFERENT model than the producer (architecture §5, row
`gate_quality`).

The gate EXECUTES the artifact: it does not grade the music
itself (that is the reviewer's job) — it verifies the review
RECORD exists, was produced by a reviewer model different from
the producing model, carries a verdict, and covers THIS master
(sha256 binding).

Review record layout (review.json in the package dir):
{
  "master": {"sha256": "...", "path": "master.wav"},
  "reviewer_model": "deepseek-chat",
  "producer_model": "suno-v4.5",
  "verdict": "pass",               # pass | fail
  "findings": ["..."],
  "reviewed_at": "2026-10-08T...",
  "reviewer": "reviewer-deepseek"
}

The same-model rule is structural: a producer reviewing its own
output on the same model is the failure mode this gate exists
to prevent (self-review is editor's lane, never the maker's).

Usage:
  python3 music/gates/gate_quality.py --package-dir <dir> \
      [--producer-model <name>]

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REVIEW_NAME = "review.json"
MASTER_NAME = "master.wav"


def fail(msgs: list[str]) -> int:
    print("FAIL gate_quality", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_quality — independent-review record gate")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--producer-model", default=None,
                        help="model the producer used; the gate "
                             "fails if the reviewer used the same "
                             "model (defaults to the record's "
                             "producer_model field)")
    args = parser.parse_args(argv)

    pkg = Path(args.package_dir)
    if not pkg.is_dir():
        return fail([f"no such package directory: {pkg}"])

    problems: list[str] = []

    record = pkg / REVIEW_NAME
    if not record.is_file():
        return fail([f"no {REVIEW_NAME} — the track has not been "
                     "reviewed. Route to the reviewer panel "
                     "(reviewer-deepseek / longcat / minimax / "
                     "nemotron) and record the verdict."])

    try:
        review = json.loads(record.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail([f"{REVIEW_NAME} is corrupt JSON: {exc}"])
    if not isinstance(review, dict):
        return fail([f"{REVIEW_NAME} is not a JSON object"])

    # --- 1. verdict ---------------------------------------------------
    verdict = str(review.get("verdict", "")).lower()
    if verdict not in ("pass", "fail"):
        problems.append(f"review verdict is {verdict!r}; "
                        "expected 'pass' or 'fail'")
    elif verdict == "fail":
        problems.append("reviewer verdict is FAIL — see "
                        f"{REVIEW_NAME} findings: "
                        + "; ".join(str(f) for f in
                                    review.get("findings", [])))

    # --- 2. different model than the producer --------------------------
    reviewer_model = str(review.get("reviewer_model", "")).strip()
    producer_model = (args.producer_model
                      or str(review.get("producer_model", "")).strip())
    if not reviewer_model:
        problems.append("reviewer_model is empty — the record must "
                        "name the model that produced the review")
    if not producer_model:
        problems.append("producer_model is unknown — pass "
                        "--producer-model or record it in the review")
    if reviewer_model and producer_model and \
            reviewer_model.lower() == producer_model.lower():
        problems.append(f"reviewer_model == producer_model "
                        f"('{reviewer_model}') — the review is not "
                        "independent. gate_quality requires a "
                        "DIFFERENT model than the producer "
                        "(architecture §5).")

    # --- 3. the review covers THIS master --------------------------------
    master = pkg / MASTER_NAME
    master_entry = review.get("master") or {}
    if not master.is_file():
        problems.append(f"no {MASTER_NAME} in the package")
    elif not isinstance(master_entry, dict) or \
            not master_entry.get("sha256"):
        problems.append(f"{REVIEW_NAME} has no master sha256 — the "
                        "review is not bound to the master it "
                        "reviewed")
    else:
        digest = hashlib.sha256(master.read_bytes()).hexdigest()
        if master_entry["sha256"] != digest:
            problems.append("master sha256 in the review record does "
                            "not match master.wav — the review covers "
                            "a different file")

    # --- 4. human reviewer identity + timestamp --------------------------
    if not review.get("reviewer"):
        problems.append("review record has no named reviewer "
                        "(reviewer profile)")
    if not review.get("reviewed_at"):
        problems.append("review record is undated")

    if problems:
        return fail(problems)

    print("PASS gate_quality")
    print(f"  package        : {pkg}")
    print(f"  reviewer       : {review.get('reviewer')} "
          f"on {reviewer_model}")
    print(f"  producer model : {producer_model} (independent: yes)")
    print(f"  verdict        : {verdict}")
    print(f"  master bound   : sha256 verified")
    print(f"  reviewed_at    : {review.get('reviewed_at')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
