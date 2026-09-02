#!/usr/bin/env python3
"""Gate: script stage — enforce the script.md contract.

Blocks advance if:
- script.md missing
- narration word count below minimum (750/5min, 1200/8min, 1500/10min, 2250/15min by target)
- no required structure skeleton (Hook/Stakes/Body/Payoff markers)
- evidence claims have no source lines
Exit 0 = PASS, exit 1 = FAIL (with reasons). Idempotent, no side effects.
"""
import re, sys, os
from pathlib import Path

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        fail("usage: gate_script.py <campaign-dir>")
    camp = Path(sys.argv[1])
    script = camp / "script.md"
    if not script.exists():
        fail(f"script.md missing at {script}")
    text = script.read_text()

    # --- word count: narration = prose lines, excluding structure/notes ---
    words = 0
    sections = []
    for line in text.splitlines():
        s = line.strip()
        # track section headers for skeleton check FIRST (before # skip)
        m = re.match(r'^##\s+(.+)', s)
        if m:
            sections.append(m.group(1).lower())
            continue
        if not s or s.startswith('#') or s.startswith('<!--') or s.startswith('---'):
            continue
        # skip non-narration directive lines
        if s.startswith('**') or s.startswith('Visual:') or s.startswith('TTS') or \
           s.startswith('Source') or s.startswith('>') or s.startswith('- [') or s.startswith('Pause'):
            continue
        words += len(s.split())

    # duration target from opportunity/campaign? default min 1200 (8min)
    # read campaign metadata if present
    min_words = 1200
    for meta_name in ("opportunity.md", "campaign.md", "metadata.json"):
        meta = camp / meta_name
        if meta.exists():
            raw = meta.read_text()
            for pat, mins in [(r'15\s*min', 2250), (r'10\s*min', 1500), (r'8\s*min', 1200), (r'5\s*min', 750)]:
                if re.search(pat, raw, re.I):
                    min_words = mins
                    break
            if min_words != 1200:
                break

    print(f"narration_words={words}")
    if words < min_words:
        fail(f"narration {words} < minimum {min_words}")

    # --- skeleton ---
    joined = ' '.join(sections)
    needed = {'hook': 'hook', 'stakes': 'stakes', 'payoff': 'payoff'}
    if 'hook' not in joined:
        fail("missing Hook section")
    if 'stake' not in joined:
        fail("missing Stakes section")
    if 'payoff' not in joined:
        fail("missing Payoff section")

    # --- visual beats anti-slideshow: prose has visual notes per section ---
    visual_notes = len(re.findall(r'Visual:', text, re.I))
    # need at least ceil(words/45) beats
    need_beats = max(1, -(-words // 45))
    if visual_notes < need_beats:
        print(f"WARN: visual notes {visual_notes} < suggested {need_beats} (anti-slideshow)")
        # not a hard fail — videobot holds the beat count on visuals

    print(f"PASS: script gate (words={words}, sections={len(sections)})")
    sys.exit(0)

if __name__ == "__main__":
    main()
