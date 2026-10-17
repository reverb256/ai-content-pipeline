#!/usr/bin/env python3
"""check_doc_refs.py — two rules over every file that cites music-lane-architecture.md.

  Rule 1: every section reference (`§5`, `S12`, `section 11`) resolves to a real heading
          in the doc.
  Rule 2: no citing file also claims the doc is absent ("does not exist").

Regression check for card t_b0a4db92 (rule 1) and card t_fa731c5b (rule 2).

WHY RULE 2 EXISTS (card t_fa731c5b)
-----------------------------------
The playbook and the research doc were written 2026-10-08, stranded on
`wip/atlas-backup-20261014`, and restored into `main` in `5a01157` at 14:12 on 2026-10-16
(rewritten in `7411afa`). Ten briefs under `music/briefs/` kept the paragraph they had
written before that restore — "Dangling reference", stating the file "does not exist
anywhere on this machine" and citing a `find` that returned no hits. The paragraph was a
true measurement at its own instant and a false claim after 14:12, and nothing failed: a
cross-reference that cannot be checked is a defect that looks like documentation.

Rule 2 is deliberately coarse — file-level co-occurrence of the doc name and the phrase
"does not exist", case-insensitive. That is the acceptance check the card states, verbatim.
It is coarse enough to stay cheap on a shared tree and fine enough to catch every shape the
incident took: a whole paragraph, a struck-through `~~Still dangling~~` quote, and a
correction-table row that quotes the old claim in one column. A history-shaped line that
quotes the old wording without the words "does not exist" (for example "no copy exists on
this machine" inside a `CORRECTED` row) is not caught here — this is a net, not a proof.

Usage:
  /usr/bin/python3 check_doc_refs.py [--doc PATH] [--repo PATH] [--rev REV] [--selftest]

`--rev` reads the doc and the citing files at that revision (the citing-file list still
comes from the worktree), which is how the regression for t_fa731c5b is demonstrated:
  /usr/bin/python3 check_doc_refs.py --repo . --rev 5aed5cc   # the pre-fix revision -> FAIL
  /usr/bin/python3 check_doc_refs.py --repo .                 # after the fix      -> OK
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
# Rule 2 marker. Kept to the exact words the incident's briefs used.
ABSENCE_RE = re.compile(r"does not exist", re.IGNORECASE)


def read_at(repo: Path, rel: str, rev: str | None, missing_ok: bool = False) -> str:
    """Contents of `rel` at `rev`, or from the worktree when rev is None.

    `missing_ok` is for the citing-file sweep at an old revision: the file list is always
    taken from the worktree (so a file another worker just added is in the list but not in
    the old tree), and a file that did not exist at `rev` has no claim to check. The doc
    itself is read strictly.
    """
    if rev is None:
        try:
            return (repo / rel).read_text(errors="replace")
        except OSError:
            if missing_ok:
                return ""
            raise
    proc = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=repo,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        if missing_ok:
            return ""
        raise SystemExit(f"check_doc_refs: cannot read {rel} at {rev}: "
                         f"{proc.stderr.strip()}")
    return proc.stdout


def headings(doc_text: str) -> set[str]:
    found = set()
    for line in doc_text.splitlines():
        m = re.match(r"^#{1,4}\s+(\d+(?:\.\d+)?)\.?\s", line)
        if m:
            found.add(m.group(1))
    return found


def citations(repo: Path, doc_names: set[str], rev: str | None = None):
    """(relpath, line_no, line) for every line that names the doc, outside the doc."""
    exts = {".md", ".yaml", ".yml", ".py", ".sh", ".json", ".service", ".timer"}
    out = []
    for p in sorted(repo.rglob("*")):
        if not p.is_file() or p.suffix not in exts:
            continue
        if p.name in doc_names:
            continue
        if any(part in {".git", "__pycache__", "node_modules"} for part in p.parts):
            continue
        rel = str(p.relative_to(repo))
        text = read_at(repo, rel, rev, missing_ok=True)
        if not text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if DOC_NAME in line:
                out.append((rel, i, line.strip()))
    return out


def refs_on(line: str) -> list[str]:
    refs = []
    # only the refs that sit next to the doc name on that line
    for m in REF_RE.finditer(line):
        ref = m.group(1) or m.group(2)
        if ref:
            refs.append(ref)
    return refs


def absence_claims(repo: Path, citing_files: list[str], rev: str | None = None):
    """(relpath, line_no, line) for a citing file that also says the doc does not exist.

    `music/scripts/check_*.py` is skipped: a checking script carries the phrase as DATA (its
    own marker regex and its own docstring), not as a claim about the world. Every other file
    is a claim.
    """
    out = []
    for rel in citing_files:
        if rel.startswith("music/scripts/check_"):
            continue
        text = read_at(repo, rel, rev, missing_ok=True)
        if not text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if ABSENCE_RE.search(line):
                out.append((rel, i, line.strip()))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=f"brain/playbooks/{DOC_NAME}")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--rev", default=None,
                    help="read the doc and the citing files at this revision")
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
        # rule 2: the incident's own sentence must match, and a bare history row must not
        assert ABSENCE_RE.search('"does not exist anywhere on this machine"')
        assert ABSENCE_RE.search("**Still dangling:** ... does not exist.")
        assert not ABSENCE_RE.search('"no copy exists on this machine"')
        print("selftest OK")
        return 0

    repo = Path(args.repo).resolve()
    doc_rel = args.doc if not Path(args.doc).is_absolute() else str(
        Path(args.doc).relative_to(repo))
    doc_text = read_at(repo, doc_rel, args.rev)

    have = headings(doc_text)
    cites = citations(repo, {DOC_NAME}, args.rev)
    bad = []
    checked = 0
    for rel, line_no, line in cites:
        for ref in refs_on(line):
            checked += 1
            if ref not in have:
                bad.append((rel, line_no, ref, line))

    stale = absence_claims(repo, sorted({c[0] for c in cites}), args.rev)

    if stale:
        print("STALE ABSENCE CLAIM (card t_fa731c5b):", file=sys.stderr)
        for rel, line_no, line in stale:
            print(f"  {rel}:{line_no} :: {line[:100]}", file=sys.stderr)
        print("  Fix: state that the doc exists, or drop the sentence.", file=sys.stderr)
        return 1

    if bad:
        print("UNRESOLVED REFERENCES:", file=sys.stderr)
        for rel, line_no, ref, line in bad:
            print(f"  {rel}:{line_no} §{ref} :: {line[:100]}", file=sys.stderr)
        return 1

    print(f"doc      : {repo / doc_rel} ({len(doc_text)} B)")
    print(f"headings : {len(have)} -> {', '.join(sorted(have, key=lambda s: [int(x) for x in s.split('.')]))}")
    print(f"citing files (outside the doc): {len({c[0] for c in cites})}")
    print(f"section refs checked: {checked}")
    print(f"absence claims checked: {len({c[0] for c in cites})} citing file(s)")
    print("OK: every section reference resolves to a heading in the doc")
    return 0


if __name__ == "__main__":
    sys.exit(main())
