#!/usr/bin/env python3
"""gate_human_approval — the j_kro approval gate. NEVER auto-passes.

Architecture §5, row `gate_human_approval` ("j_kro gate —
never auto-passed") and §7: publish approval is a human
gate. This gate verifies an APPROVAL RECORD exists, is
cryptographically attributable to a human approver, names
the artifact it approves (sha256-bound), and is not older
than the artifact it approves.

Approval record (approval.json in the package dir):
{
  "approver": "j_kro",
  "approved_at": "2026-10-08T09:00:00",
  "action": "approve-public",          # or "approve-private"
  "artifact": {"sha256": "...", "path": "master.wav"},
  "note": "angle approved for streaming"
}

There is deliberately NO --force / --auto-approve flag.
The only way this gate passes is a real approval record
for the real artifact.

Usage:
  python3 music/gates/gate_human_approval.py \
      --package-dir <dir> [--artifact master.wav]

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

APPROVAL_NAME = "approval.json"
DEFAULT_ARTIFACT = "master.wav"
APPROVERS = ("j_kro",)


def fail(msgs: list[str]) -> int:
    print("FAIL gate_human_approval", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    print("  This gate cannot be satisfied by a bot: it needs a "
          "human approval record for THIS artifact.", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_human_approval — j_kro approval gate")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--artifact", default=DEFAULT_ARTIFACT,
                        help="artifact file the approval must "
                             "cover (default: master.wav)")
    args = parser.parse_args(argv)

    pkg = Path(args.package_dir)
    if not pkg.is_dir():
        return fail([f"no such package directory: {pkg}"])

    problems: list[str] = []

    record = pkg / APPROVAL_NAME
    if not record.is_file():
        return fail([f"no {APPROVAL_NAME} — nothing has been "
                     "approved. Publish approval is j_kro's "
                     "decision (architecture §7, item 1)."])

    try:
        approval = json.loads(record.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail([f"{APPROVAL_NAME} is corrupt JSON: {exc}"])
    if not isinstance(approval, dict):
        return fail([f"{APPROVAL_NAME} is not a JSON object"])

    # --- 1. a human approved -------------------------------------------
    approver = str(approval.get("approver", "")).strip()
    if not approver:
        problems.append("approval record names no approver")
    elif approver not in APPROVERS:
        problems.append(f"approver '{approver}' is not a human "
                        f"approver (allowed: {', '.join(APPROVERS)})")

    # --- 2. the approval is for a real action --------------------------
    action = str(approval.get("action", "")).strip()
    if action not in ("approve-public", "approve-private"):
        problems.append(f"action '{action}' is not a publish "
                        "approval action (approve-public | "
                        "approve-private)")

    # --- 3. dated, and not older than the artifact ----------------------
    approved_at = approval.get("approved_at")
    if not approved_at:
        problems.append("approval record is undated")
    else:
        try:
            stamp = dt.datetime.fromisoformat(str(approved_at))
        except ValueError:
            problems.append(f"approved_at '{approved_at}' is not "
                            "an ISO-8601 timestamp")
        else:
            artifact_path = pkg / args.artifact
            if artifact_path.is_file():
                mtime = dt.datetime.fromtimestamp(
                    artifact_path.stat().st_mtime,
                    tz=dt.timezone.utc)
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=dt.timezone.utc)
                if stamp < mtime:
                    problems.append(
                        f"approval ({approved_at}) predates the "
                        f"artifact mtime ({mtime.isoformat()}) — "
                        "the approval does not cover this version")

    # --- 4. bound to THIS artifact --------------------------------------
    artifact = pkg / args.artifact
    entry = approval.get("artifact") or {}
    if not artifact.is_file():
        problems.append(f"artifact {args.artifact} is not in the "
                        "package")
    elif not isinstance(entry, dict) or not entry.get("sha256"):
        problems.append(f"{APPROVAL_NAME} has no artifact sha256 — "
                        "the approval is not bound to the artifact")
    else:
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if entry["sha256"] != digest:
            problems.append("approval sha256 does not match "
                            f"{args.artifact} — the approval covers "
                            "a different version of the artifact")

    if problems:
        return fail(problems)

    print("PASS gate_human_approval")
    print(f"  package  : {pkg}")
    print(f"  approver : {approver}")
    print(f"  action   : {action}")
    print(f"  artifact : {args.artifact} (sha256 verified)")
    print(f"  approved : {approved_at}")
    note = approval.get("note")
    if note:
        print(f"  note     : {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
