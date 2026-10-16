#!/usr/bin/env python3
"""Read-only inventory of the DistroKid upload form + account state.

Dumps every visible form control (inputs, selects, textareas, checkboxes)
with its name/id/type/placeholder and nearest label text, plus the section
headings that group them. Also captures the account page (artist name, plan).
Writes a compact JSON summary to stdout. No clicks that submit, no fills.
"""
import json
import time

from music.publish.playwright.session import SessionHelper

FORM_JS = r"""(() => {
  const val = e => {
    if (!e) return null;
    if (e.tagName === 'SELECT') return {tag: e.tagName, name: e.name, id: e.id,
      opts: Array.from(e.options).slice(0,8).map(o => o.value + '|' + o.text.trim())};
    return {tag: e.tagName, name: e.name || null, id: e.id || null,
      type: e.type || null, ph: (e.placeholder||'').slice(0,50) || null,
      max: e.maxLength > 0 ? e.maxLength : null};
  };
  const labelFor = e => {
    let l = e.id && document.querySelector(`label[for="${e.id}"]`);
    if (!l) l = e.closest('label');
    if (!l) { const p = e.closest('tr,div'); if (p) l = p.querySelector('label'); }
    return l ? (l.innerText||'').trim().replace(/\s+/g,' ').slice(0,60) : null;
  };
  const out = {url: location.href, sections: [], inputs: [], selects: [], textareas: [], checkboxes: []};
  document.querySelectorAll('h1,h2,h3,h4,legend,.section-title,.step').forEach(h => {
    const t = (h.innerText||'').trim().replace(/\s+/g,' ');
    if (t && t.length < 70) out.sections.push(t);
  });
  document.querySelectorAll('input').forEach(e => {
    const r = val(e); r.label = labelFor(e); r.visible = !!e.offsetParent;
    if (e.type === 'checkbox' || e.type === 'radio') out.checkboxes.push(r);
    else out.inputs.push(r);
  });
  document.querySelectorAll('select').forEach(e => { const r = val(e); r.label = labelFor(e); r.visible = !!e.offsetParent; out.selects.push(r); });
  document.querySelectorAll('textarea').forEach(e => { const r = val(e); r.label = labelFor(e); r.visible = !!e.offsetParent; out.textareas.push(r); });
  return out;
})()"""

with SessionHelper() as session:
    # --- account page: artist name, plan, payout state
    page = session.new_page()
    page.goto("https://distrokid.com/account", wait_until="domcontentloaded")
    time.sleep(5)
    acct = page.evaluate(r"""(() => {
      const t = document.body.innerText || '';
      const grab = (re) => { const m = t.match(re); return m ? m[0].slice(0,60) : null; };
      return {
        artist: grab(/artist[^\n]{0,50}/i),
        plan: grab(/(musician|premier|plus|ultimate|free)[^\n]{0,30}/i),
        hasBank: /bank|paypal|payout/i.test(t),
        snippet: t.replace(/\s+/g,' ').slice(0, 400)
      };
    })()""")
    print("=== ACCOUNT ===")
    print(json.dumps(acct, indent=1)[:900])
    page.close()

    # --- upload form: full field inventory
    page = session.new_page()
    page.goto("https://distrokid.com/new", wait_until="domcontentloaded")
    time.sleep(7)
    form = page.evaluate(FORM_JS)
    print("\n=== UPLOAD FORM:", form["url"], "===")
    print("SECTIONS:", json.dumps(form["sections"][:20]))
    vis = lambda lst: [x for x in lst if x.get("visible")]
    print(f"\nVISIBLE INPUTS ({len(vis(form['inputs']))}):")
    for x in vis(form["inputs"]):
        print(" ", json.dumps(x))
    print(f"\nVISIBLE SELECTS ({len(vis(form['selects']))}):")
    for x in vis(form["selects"]):
        print(" ", json.dumps(x))
    print(f"\nVISIBLE TEXTAREAS ({len(vis(form['textareas']))}):")
    for x in vis(form["textareas"]):
        print(" ", json.dumps(x))
    print(f"\nVISIBLE CHECKBOXES/RADIOS ({len(vis(form['checkboxes']))}):")
    for x in vis(form["checkboxes"])[:40]:
        print(" ", json.dumps(x))
    page.close()
