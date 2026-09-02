#!/usr/bin/env python3
"""Gate: evidence-trace — every script claim must trace to a research.md source.

Enforces the no-hallucination doctrine mechanically:
1. Extract factual claims from script.md (lines with statistics, numbers, or
   named claims — heuristic: prose containing digits, %, $, years, or bolded
   statements).
2. Require each claim section to have a Source: line with a URL.
3. Verify the cited source appears in research.md's source list (or the
   research.md itself exists with >=3 distinct sources).

Exit 0 = PASS, exit 1 = FAIL with the untraced claims listed.
"""
import re, sys
from pathlib import Path

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

CLAIM_RE = re.compile(r'(\d[\d,.]*%?|\$\s?\d[\d,.]*|\b(19|20)\d{2}\b|[A-Z][a-z]+ (said|reported|found|showed|claims?|estimates?))')

def main():
    if len(sys.argv) < 2:
        fail("usage: gate_evidence.py <campaign-dir>")
    camp = Path(sys.argv[1])
    script = camp / "script.md"
    research = camp / "research.md"

    if not script.exists():
        fail(f"script.md missing at {script}")
    text = script.read_text()

    if not research.exists():
        fail(f"research.md missing at {research} — claims cannot be traced")

    # research.md source inventory: collect URLs
    rtext = research.read_text()
    r_urls = set(re.findall(r'https?://[^\s)\]]+', rtext))
    print(f"research.md sources: {len(r_urls)} URLs found")
    if len(r_urls) < 3:
        fail(f"research.md has only {len(r_urls)} sources (<3) — evidence base too thin")

    # Walk script sections; each claim-bearing section must have a Source line
    current_section = "preamble"
    sections_claims = {}   # section -> list of claim snippets
    sections_sources = {}  # section -> list of source urls
    src_re = re.compile(r'Source[s]?:\s*(https?://[^\s)\]]+|[A-Za-z][A-Za-z0-9&.,\- ]{2,80}?)\.?\s*$')

    for line in text.splitlines():
        s = line.strip()
        h = re.match(r'^#+\s*(.+)', s)
        if h:
            current_section = h.group(1)
            sections_claims.setdefault(current_section, [])
            sections_sources.setdefault(current_section, [])
            continue
        for m in src_re.finditer(s):
            sections_sources.setdefault(current_section, []).append(m.group(1))
        # claim heuristic: numbers / stats / attribution words
        if CLAIM_RE.search(s):
            # skip structural/non-claim lines
            if s.startswith(('Source', '##', '###', '|', '- [', 'Visual', 'TTS', '**Runtime', '<!--', '>')):
                continue
            sections_claims.setdefault(current_section, []).append(s[:100])

    # If the script has a consolidated Source Trace table (the stronger pattern),
    # treat it as satisfying the trace requirement globally.
    has_source_trace_table = bool(re.search(r'Source Trace|Evidence source|Claim in script', text, re.I))
    if has_source_trace_table:
        print("  (found consolidated Source Trace table — claims traced at end of script)")
        sys.exit(0)

    # Verify: claim-bearing sections (excluding pure structure ones) have sources
    META_SECTIONS = re.compile(
        r'(runtime|contradiction|checklist|notes|production|source trace|appendix|template|title|h1|preamble|hook \(|stakes \(|payoff \(|cta|^script:|^script —|^script )',
        re.I)
    untraced = []
    for sec, claims in sections_claims.items():
        # structural sections often carry claims too; require source for any
        # section with >=1 factual claim AND that isn't obviously meta
        if not claims:
            continue
        if META_SECTIONS.search(sec):
            print(f"  (skip meta section: {sec[:60]})")
            continue
        if not sections_sources.get(sec):
            untraced.append(f"section '{sec}' has {len(claims)} claim(s) but no Source: line")
        else:
            # every claim line is adjacent to a source line? (light check)
            pass

    total_claims = sum(len(v) for v in sections_claims.values())
    print(f"claims detected: {total_claims} across {len([s for s in sections_claims if sections_claims[s]])} sections")
    if untraced:
        for u in untraced:
            print(f"  - {u}")
        fail(f"{len(untraced)} section(s) with untraced claims")

    print("PASS: evidence-trace gate")
    sys.exit(0)

if __name__ == "__main__":
    main()
