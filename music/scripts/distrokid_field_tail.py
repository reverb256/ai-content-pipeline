#!/usr/bin/env python3
"""Capture the tail of the DistroKid track-form controls that the main
inventory truncates: explicit/radio-edit, instrumental, AI-lyrics
disclosure, language, songwriter-type, and the mandatory-confirmation
checkboxes. Read-only."""
import json
import time

from music.publish.playwright.session import SessionHelper

TAIL_JS = r"""(() => {
  const out = {radios: [], selects: [], checkboxes: [], mandatory: []};
  document.querySelectorAll('input[type=radio]').forEach(e => {
    let l = e.closest('label') || (e.id && document.querySelector(`label[for="${e.id}"]`));
    const t = l ? (l.innerText||'').trim().replace(/\s+/g,' ').slice(0,70) : (e.name||'?');
    out.radios.push({name: e.name, id: e.id||null, label: t, checked: e.checked});
  });
  document.querySelectorAll('select').forEach(e => {
    const nm = e.name || e.id;
    if (/sitetran|language/.test(nm)) return;
    out.selects.push({name: nm, id: e.id||null,
      val: e.value,
      opts: Array.from(e.options).map(o => o.value+'|'+o.text.trim()).slice(0,12)});
  });
  document.querySelectorAll('input[type=checkbox]').forEach(e => {
    if (e.name === 'store' || e.name === 'extras') return;
    let l = e.closest('label') || (e.id && document.querySelector(`label[for="${e.id}"]`));
    const t = l ? (l.innerText||'').trim().replace(/\s+/g,' ').slice(0,70) : (e.name||'?');
    out.checkboxes.push({name: e.name, id: e.id||null, label: t, checked: e.checked});
  });
  // mandatory confirmation checkboxes (YouTube Content ID, T&C, recorded, etc.)
  document.querySelectorAll('input[type=checkbox]').forEach(e => {
    const id = e.id||''; const nm = e.name||'';
    if (/mandatory|chkyoutube|youtubeContent|Areyousure|tandc|recorded|otherartist/i.test(id+nm))
      out.mandatory.push({id, name: nm, checked: e.checked});
  });
  return out;
})()"""

with SessionHelper() as session:
    page = session.new_page()
    page.goto("https://distrokid.com/new", wait_until="domcontentloaded")
    time.sleep(7)
    # need a track present for the track-level radios to render
    try:
        page.select_option("#howManySongsOnThisAlbum", value="1")
        time.sleep(2)
    except Exception:
        pass
    tail = page.evaluate(TAIL_JS)
    print("=== NON-STORE RADIOS ===")
    for r in tail["radios"]:
        print(f"  [{r['checked'] and 'x' or ' '}] {r['label'][:65]}  (name={r['name'][:40]}, id={r['id']})")
    print("\n=== CONTENT SELECTS (language/songwriter-type) ===")
    for s in tail["selects"]:
        print(f"  {s['id'] or s['name']}: {s['opts'][:10]}")
    print("\n=== NON-STORE CHECKBOXES ===")
    for c in tail["checkboxes"]:
        print(f"  [{c['checked'] and 'x' or ' '}] {c['label'][:65]}  (id={c['id']})")
    print("\n=== MANDATORY CONFIRMATIONS ===")
    for m in tail["mandatory"]:
        print(f"  [{m['checked'] and 'x' or ' '}] id={m['id']} name={m['name']}")
    page.close()
