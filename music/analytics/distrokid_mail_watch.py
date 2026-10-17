#!/usr/bin/env python3
"""distrokid_mail_watch — parse DistroKid emails for release signals and
write them back into the track manifest.

Reads reverb256@gmail.com over IMAP via himalaya, finds DistroKid messages,
extracts release facts (ISRC, live/release date, track/album title, status),
and merges them into music/packages/streaming/<track_id>/manifest.json under
a `distrokid_mail` block. Never overwrites a field the manifest already holds
unless --force is passed. Read-only against the mailbox: it never trashes,
marks, or sends.

DistroKid sender families (verified 2026-10-09):
  mailbot@distrokid.com   transactional (login codes, release confirmations)
  dk@hello.distrokid.com  marketing (ignored by this tool)

Usage:
  python3 music/analytics/distrokid_mail_watch.py --track-id <id> [--dry-run]
  python3 music/analytics/distrokid_mail_watch.py --all [--dry-run]

Exit codes: 0 = ran (signals found or not), 1 = himalaya/config error,
2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGES = REPO / "music" / "packages" / "streaming"

MAILBOXES = ("INBOX", "[Gmail]/All Mail", "[Gmail]/Spam")

# Sender domains that carry real release signal (not marketing).
SIGNAL_SENDERS = ("distrokid.com",)

# Subject fragments that mark a transactional release email. Calibrated
# against the observed sender family; release-confirmation subjects will be
# added here the first time one arrives (this list is DATA, not logic).
SUBJECT_HINTS = (
    "release", "isrc", "live", "upload", "track", "album",
    "approved", "processing", "distributed", "now available",
)

# Phrases that are pure marketing / security noise — never a release signal.
IGNORE_HINTS = (
    "verification code", "log in", "sign in", "boost your release",
    "free tools", "unsubscribe", "password",
)

ISRC_RE = re.compile(r"\b([A-Z]{2}[A-Z0-9]{3}\d{2}\d{5})\b")
DATE_RES = [
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"),
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
        r"(\d{1,2}),?\s+(\d{4})\b", re.I),
]


def run_himalaya(args: list[str]) -> str:
    proc = subprocess.run(
        ["himalaya", "-a", "gmail", *args],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"himalaya failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


def list_distrokid_ids() -> list[dict]:
    """Return [{id, from, subject, date}] for every DistroKid message we can
    find, deduped by id across the mailboxes we scan."""
    seen: dict[str, dict] = {}
    for mb in MAILBOXES:
        try:
            out = run_himalaya(
                ["envelope", "list", "-m", mb, "-s", "60", "--json"])
        except RuntimeError:
            continue
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            continue
        rows = data.get("envelopes", []) if isinstance(data, dict) else data
        for e in rows:
            if not isinstance(e, dict):
                continue
            from_list = e.get("from") or []
            if isinstance(from_list, dict):
                from_list = [from_list]
            addr = ""
            if from_list and isinstance(from_list[0], dict):
                addr = from_list[0].get("email", "") or ""
            if "distrokid.com" not in addr.lower():
                continue
            eid = str(e.get("id"))
            if eid not in seen:
                seen[eid] = {
                    "id": eid,
                    "from": addr,
                    "subject": str(e.get("subject", "")),
                    "date": str(e.get("date", "")),
                    "mailbox": mb,
                }
    return list(seen.values())


def is_signal(msg: dict) -> bool:
    subj = msg["subject"].lower()
    if any(bad in subj for bad in IGNORE_HINTS):
        return False
    return any(hint in subj for hint in SUBJECT_HINTS)


def read_body(msg: dict) -> str:
    try:
        return run_himalaya(
            ["message", "read", msg["id"], "-m", msg["mailbox"]])
    except RuntimeError:
        return ""


def extract_signals(body: str) -> dict:
    sig: dict = {}
    m = ISRC_RE.search(body)
    if m:
        sig["isrc"] = m.group(1)
    for rx in DATE_RES:
        dm = rx.search(body)
        if dm:
            sig["date_hint"] = dm.group(0)
            break
    return sig


def merge_manifest(pkg_dir: Path, signals: dict, force: bool) -> bool:
    """Merge signals into manifest.json. Returns True if it changed."""
    manifest = pkg_dir / "manifest.json"
    if not manifest.is_file():
        print(f"  skip {pkg_dir.name}: no manifest.json")
        return False
    data = json.loads(manifest.read_text(encoding="utf-8"))
    block = data.setdefault("distrokid_mail", {})
    changed = False
    for k, v in signals.items():
        if k in ("date_hint",):
            key = "live_date_hint"
        else:
            key = k
        if force or not block.get(key):
            block[key] = v
            changed = True
    if changed:
        block["source"] = "distrokid_mail_watch"
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DistroKid mail → manifest")
    ap.add_argument("--track-id", help="package dir under packages/streaming/")
    ap.add_argument("--all", action="store_true",
                    help="scan every package dir")
    ap.add_argument("--force", action="store_true",
                    help="overwrite fields already present")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not args.track_id and not args.all:
        print("need --track-id or --all", file=sys.stderr)
        return 2

    msgs = list_distrokid_ids()
    signal_msgs = [m for m in msgs if is_signal(m)]
    print(f"scanned mailbox: {len(msgs)} DistroKid msgs, "
          f"{len(signal_msgs)} release-signal msgs")

    targets: list[Path] = []
    if args.all:
        targets = [p for p in PACKAGES.iterdir() if p.is_dir()]
    else:
        targets = [PACKAGES / args.track_id]

    if not signal_msgs:
        print("no release-signal mail yet — nothing to merge "
              "(expected until a release is published)")
        return 0

    changed_any = False
    for pkg in targets:
        for m in signal_msgs:
            body = read_body(m)
            sig = extract_signals(body)
            if not sig:
                continue
            print(f"  {pkg.name} <- {m['subject'][:50]}: {sig}")
            if not args.dry_run:
                changed_any |= merge_manifest(pkg, sig, args.force)
    return 0 if changed_any or args.dry_run else 0


if __name__ == "__main__":
    sys.exit(main())
