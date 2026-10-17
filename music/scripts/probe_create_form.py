#!/usr/bin/env python3
"""Read-only probe of the suno.com/create form (music lane).

Attaches to the existing CDP Chromium on :9222 (the logged-in
session). READ-ONLY: no clicks, no form entry, no credits.
Exits 0 with JSON findings either way.

Why this exists (verified 2026-10-08, t_498ab557): the prompt
templates previously instructed "Instrumental toggle ON", but
this probe measured the LIVE form and found NO toggle element of
any kind. Instrumental on today's Suno UI = leave the lyrics box
empty; the editor placeholder itself says "Start writing lyrics,
or leave this empty for instrumental". The templates were
corrected to match measured reality; this probe is the
regression check that keeps them honest.

Usage:
    python3 music/scripts/probe_create_form.py
"""
import json
import sys
from pathlib import Path

import importlib.util

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "music"))

_spec = importlib.util.spec_from_file_location(
    "suno_gen", REPO / "music" / "suno-gen.py")
suno_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(suno_gen)
CDP, SunoTab, CREATE_URL, CDP_PORT = (
    suno_gen.CDP, suno_gen.SunoTab, suno_gen.CREATE_URL, suno_gen.CDP_PORT)

PROBE_JS = """
(() => {
  const out = {href: location.href, instrumental: [], switches: [], textareas: [], buttons: []};
  // anything whose visible text or aria-label says Instrumental
  document.querySelectorAll('*').forEach((el) => {
    const aria = el.getAttribute('aria-label') || '';
    const txt = (el.children.length === 0 ? (el.textContent || '') : '');
    if (/instrumental/i.test(aria) || /instrumental/i.test(txt.trim())) {
      out.instrumental.push({tag: el.tagName, aria: aria, text: (txt || '').trim().slice(0, 60),
                             role: el.getAttribute('role') || '',
                             checked: el.getAttribute('aria-checked') || '',
                             state: el.getAttribute('data-state') || ''});
    }
  });
  out.instrumental = out.instrumental.slice(0, 8);
  // role=switch / checkbox elements (custom toggles usually use these)
  document.querySelectorAll('[role="switch"], [role="checkbox"], input[type="checkbox"]').forEach((el) => {
    const label = el.getAttribute('aria-label') || (el.textContent || '').trim().slice(0, 50);
    out.switches.push({tag: el.tagName, label, checked: el.getAttribute('aria-checked') || el.checked});
  });
  out.switches = out.switches.slice(0, 12);
  // textareas and their placeholders (form shape)
  document.querySelectorAll('textarea').forEach((t) => {
    out.textareas.push({placeholder: (t.placeholder || '').slice(0, 80),
                        aria: t.getAttribute('aria-label') || '',
                        len: (t.value || '').length});
  });
  // buttons mentioning instrumental / custom / create
  document.querySelectorAll('button').forEach((b) => {
    const t = ((b.getAttribute('aria-label') || '') + ' ' + (b.innerText || '')).trim();
    if (/instrumental|create song|custom/i.test(t)) {
      out.buttons.push(t.replace(/\\s+/g, ' ').slice(0, 60));
    }
  });
  out.buttons = [...new Set(out.buttons)].slice(0, 10);
  return JSON.stringify(out);
})()
"""

def main() -> int:
    cdp = CDP(CDP_PORT)
    tab = SunoTab(cdp)
    tab.navigate(CREATE_URL)
    href = tab.safe_eval("location.href", timeout=15)
    print(json.dumps({"nav": "ok", "href": href}))
    raw = tab.safe_eval(PROBE_JS, timeout=30)
    print(raw)
    return 0

if __name__ == "__main__":
    sys.exit(main())
