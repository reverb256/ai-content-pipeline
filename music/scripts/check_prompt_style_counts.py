#!/usr/bin/env python3
"""check_prompt_style_counts — a template's declared style-field length must be TRUE.

Why this exists
---------------
Measured 2026-10-16 (card `t_05b640f6`, the duplicate-card pass on
`music/briefs/chiptune-8bit.md`, §8.4): that brief asserted the template's own header
claim was stale — "style block measures **844 chars** (the template header claims
'567/1000' — stale)". Not one slice of `music/prompts/chiptune-8bit.md` is 844
characters; the block is 568 bytes / 567 chars (1 line), exactly what the header says.
The same class of error hit the sibling anime-opening brief (`t_abaa7e2d`, commit
`afa242e`), which mislabelled 754 bytes as 752 chars. Both times the artifact was
fine and the *claim about it* was wrong, and nothing in the repo could catch it.

The upstream budget is real: templates say "paste into Suno Styles, N/1000 chars". A
block that outgrows the 1000-character box is silently truncated by the surface, so
the count is not cosmetic bookkeeping — it is the only guard on that budget.

Rules enforced
--------------
1. FAIL when a `## Style field ...` heading declares `N/M chars` and the first
   ```text block in that section measures a different number (newlines stripped,
   which is the convention every template header uses).
2. FAIL when that block is longer than the declared limit — a silent Styles-box
   overflow, the defect the count exists to prevent.
3. FAIL when a `## Style field ...` heading is followed by no ```text block at all.
4. WARN (does not fail) when a style heading declares no `N/M chars` figure.

Deliberately NOT checked: briefs' prose claims about these templates. Those are not
machine-readable; rule 1 makes the ground truth one command away instead, so the
next worker measures rather than recalls.

Usage:
  python3 music/scripts/check_prompt_style_counts.py [--dir music/prompts] [--selftest]

Exit codes: 0 = every claim true, 1 = at least one false, 2 = usage error.
Stdlib only, so both /usr/bin/python3 and the bundled interpreter can run it.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

HEAD_RE = re.compile(r"^##\s+Style field\b(?P<rest>.*)$", re.M)
CLAIM_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*chars")
BLOCK_RE = re.compile(r"```text\n(.*?)```", re.S)
NEXT_HEAD_RE = re.compile(r"^##\s", re.M)


def scan(prompts_dir: Path) -> tuple[int, list[str], list[str]]:
    """Return (claims_checked, problems, warnings)."""
    problems: list[str] = []
    warnings: list[str] = []
    checked = 0

    files = sorted(prompts_dir.glob("*.md"))
    if not files:
        return 0, [f"no prompt templates under {prompts_dir}"], []

    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = path.name
        for m in HEAD_RE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            claim = CLAIM_RE.search(m.group("rest"))
            section_start = m.end()
            nxt = NEXT_HEAD_RE.search(text, section_start)
            section = text[section_start : nxt.start() if nxt else len(text)]
            block = BLOCK_RE.search(section)
            where = f"{rel}:{line_no}"

            if claim is None:
                warnings.append(f"{where}: style heading declares no `N/M chars` figure")
                continue
            declared, limit = int(claim.group(1)), int(claim.group(2))
            if block is None:
                problems.append(f"{where}: no ```text block follows the style heading")
                continue

            measured = len(block.group(1).replace("\n", ""))
            checked += 1
            if measured != declared:
                problems.append(
                    f"{where}: declares {declared}/{limit} chars, block measures {measured} "
                    f"({measured - declared:+d}) — the header claim is FALSE"
                )
            if measured > limit:
                problems.append(
                    f"{where}: block is {measured} chars against a {limit}-char limit — "
                    f"overflow is silently truncated by the Styles box"
                )
    return checked, problems, warnings


def selftest() -> int:
    """Prove the check can fail: two injected defects must both be caught."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        body = "word " * 20
        (d / "good.md").write_text(
            f"# good\n\n## Style field (paste into Suno \"Styles\", {len(body)}/1000 chars)\n\n"
            f"```text\n{body}\n```\n",
            encoding="utf-8",
        )
        (d / "wrong-count.md").write_text(
            "# wrong\n\n## Style field (paste into Suno \"Styles\", 99/1000 chars)\n\n"
            f"```text\n{body}\n```\n",
            encoding="utf-8",
        )
        big = "word " * 300
        (d / "overflow.md").write_text(
            f"# big\n\n## Style field (paste into Suno \"Styles\", {len(big)}/1000 chars)\n\n"
            f"```text\n{big}\n```\n",
            encoding="utf-8",
        )
        checked, problems, _ = scan(d)

    wrong = [p for p in problems if "FALSE" in p]
    over = [p for p in problems if "overflow" in p]
    ok = checked == 3 and len(wrong) == 1 and len(over) == 1
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_prompt_style_counts: "
          f"checked={checked} false-claim={len(wrong)} overflow={len(over)}")
    for p in problems:
        print(f"  (caught) {p}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="A template's declared style-field length must be true.")
    ap.add_argument("--dir", default=None, help="directory of prompt templates")
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    prompts = Path(args.dir) if args.dir else Path(args.repo) / "music/prompts"
    if not prompts.is_dir():
        print(f"FAIL check_prompt_style_counts: no such directory {prompts}")
        return 2

    checked, problems, warnings = scan(prompts)
    if problems:
        print(f"FAIL check_prompt_style_counts: {len(problems)} false or unsafe style-field "
              f"claim(s) across {checked} checked claim(s)")
        for p in problems:
            print(f"  {p}")
        print("  Fix: correct the header figure, or trim the block to the limit.")
        return 1

    print(f"PASS check_prompt_style_counts: {checked} declared style-field length(s) across "
          f"{len(sorted(prompts.glob('*.md')))} template(s) match their blocks")
    for w in warnings:
        print(f"  WARN {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
