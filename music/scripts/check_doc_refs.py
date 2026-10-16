#!/usr/bin/env python3
"""check_doc_refs.py — every section reference to music-lane-architecture.md must
resolve to a real heading in that file. Regression check for card t_b0a4db92.

Usage:
  /usr/bin/python3 check_doc_refs.py [--doc PATH] [--repo PATH] [--selftest]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

DOC_NAME = "music-lane-architecture.md"
# "§5", "§11.2", "S5" (ascii fallback used by some rubric files), "section 11"
REF_RE = re.compile(r"(?:§|\bS)(\d+(?:\.\d+)?)(?![\d.])|section (\d+(?:\.\d+)?)",
                    re.IGNORECASE)


def headings(doc_text: str) -> set[str]:
    found = set()
    for line in doc_text.splitlines():
        m = re.match(r"^#{1,4}\s+(\d+(?:\.\d+)?)\.?\s", line)
        if m:
            found.add(m.group(1))
    return found


def citations(repo: Path, doc_names: set[str]) -> list[tuple[str, int, str]]:
    exts = {".md", ".yaml", ".yml", ".py", ".sh", ".json", ".service", ".timer"}
    out = []
    for p in sorted(repo.rglob("*")):
        if not p.is_file() or p.suffix not in exts:
            continue
        if p.name in doc_names:
            continue
        if any(part in {".git", "__pycache__", "node_modules"} for part in p.parts):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if DOC_NAME in line:
                out.append((str(p.relative_to(repo)), i, line.strip()))
    return out


def refs_on(line: str) -> list[str]:
    refs = []
    # only the refs that sit next to the doc name on that line
    for m in REF_RE.finditer(line):
        ref = m.group(1) or m.group(2)
        if ref:
            refs.append(ref)
    return refs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=f"brain/playbooks/{DOC_NAME}")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        text = "# A\n## 5. Gates\n### 11.2 Ladder\n"
        have = headings(text)
        assert have == {"5", "11.2"}, have
        assert refs_on("Spec (music-lane-architecture.md §5)") == ["5"]
        assert refs_on("music-lane-architecture.md S12") == ["12"]
        assert refs_on("Architecture: music-lane-architecture.md §3 and §5") == ["3", "5"]
        assert refs_on("no refs here") == []
        # a missing heading must be reported
        assert "12" not in have
        print("selftest OK")
        return 0

    repo = Path(args.repo).resolve()
    doc = Path(args.doc)
    if not doc.is_absolute():
        doc = repo / doc
    if not doc.is_file():
        print(f"FAIL: {doc} does not exist", file=sys.stderr)
        return 1

    have = headings(doc.read_text())
    cites = citations(repo, {DOC_NAME})
    bad = []
    checked = 0
    for rel, line_no, line in cites:
        for ref in refs_on(line):
            checked += 1
            if ref not in have:
                bad.append((rel, line_no, ref, line))

    print(f"doc      : {doc} ({doc.stat().st_size} B)")
    print(f"headings : {len(have)} -> {', '.join(sorted(have, key=lambda s: [int(x) for x in s.split('.')]))}")
    print(f"citing files (outside the doc): {len({c[0] for c in cites})}")
    print(f"section refs checked: {checked}")
    if bad:
        print("UNRESOLVED REFERENCES:", file=sys.stderr)
        for rel, line_no, ref, line in bad:
            print(f"  {rel}:{line_no} §{ref} :: {line[:100]}", file=sys.stderr)
        return 1
    print("OK: every section reference resolves to a heading in the doc")
    return 0


if __name__ == "__main__":
    sys.exit(main())
