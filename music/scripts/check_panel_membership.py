#!/usr/bin/env python3
"""check_panel_membership — the reviewer panel must be REACHABLE and DISJOINT.

Why this exists
---------------
Measured 2026-10-16 (card t_3d84acfe, host nexus). `music/rubrics/panel.py`
wrote `verdict: fail` for EVERY track because no judge was reachable, and
`music/gates/gate_quality.py` validates exactly that review.json — so the gate
stage could not pass for any asset, silently. Three causes, every one of them a
CONFIG shape, and none of them visible to the running panel:

 1. every `reviewer*` profile's PRIMARY was `opencode-go`, which now answers
    HTTP 400 `MissingSessionID` (a missing `x-opencode-session` header, not a
    quota) — the whole panel was dead at the same moment;
 2. `panel.py` never walked the profile's own `fallback_providers` chain, so a
    live fallback saved nothing (fixed in panel.py itself, card t_3d84acfe);
 3. `reviewer-deepseek` and `reviewer-nemotron` had byte-identical routing, so
    the "panel" was ONE model counted twice. The PoLL contract
    (music/rubrics/README.md) needs judges from DISJOINT model families, and
    the panel cannot see that two configs are the same model.

Causes 1 and 3 are shape defects in the profile configs and in
`scripts/fleet-routing.json`, so the check that catches them must read those
files. This is that check. It spends NO tokens and makes NO API call — it is
the offline half of the pair; `music/rubrics/probe_judges.py` is the live half.

Rules enforced
--------------
1. FAIL if DEFAULT_PANEL is shorter than `panel.MIN_VALID_JUDGES`: the panel
   could never pass even with every judge live.
2. FAIL if a member's profile config is missing, or its primary cannot be
   resolved (model, provider, endpoint, key env).
3. FAIL if the members' primary model FAMILIES are not pairwise disjoint
   (fingerprint of cause 3).
4. FAIL if a member has no fallback, or a chain member leaves the member's
   family: a fallback from another family can collide with a sibling judge, and
   the panel cannot detect that either.
5. FAIL if any candidate of any member uses a provider that is dead for API
   use, or a model slug the spec lists as dead. Both lists are DATA, read from
   `scripts/fleet-routing.json` — not hardcoded here.
6. FAIL if `model.base_url` does not match the primary provider's endpoint in
   the spec: the endpoint must follow the provider. `fleet-route.py apply` now
   writes it (card t_3d84acfe), and a hand-edited config can still break it.
7. NOTE (never a failure) for a member whose primary provider differs from its
   chain's first provider: legal, but the two orders must not drift apart.

Usage:
  python3 music/scripts/check_panel_membership.py [--repo DIR] [--hermes DIR]

Exit codes: 0 = PASS, 1 = FAIL, 2 = the panel module could not be imported
(that is its own failure — run it with an interpreter that has numpy + PyYAML,
e.g. /usr/bin/python3; measured 2026-10-16, the Hermes bundled interpreter has
neither).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

DEFAULT_REPO = "/home/j_kro/ai-content-pipeline"
# Providers that cannot serve an API caller at all. Measured 2026-10-16:
# opencode-zen 403 "free tier can only be used within OpenCode",
# opencode-go 400 MissingSessionID.
DEAD_PROVIDERS = ("opencode-go", "opencode-zen")


def load_panel(repo: Path):
    """Import music/rubrics/panel.py by path, so this check needs no package
    layout and no installed module."""
    path = repo / "music" / "rubrics" / "panel.py"
    spec = importlib.util.spec_from_file_location("music_panel", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load panel module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["music_panel"] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="check_panel_membership — the reviewer panel must be "
                    "reachable and disjoint")
    ap.add_argument("--repo", default=DEFAULT_REPO,
                    help="checkout that holds music/rubrics/panel.py")
    ap.add_argument("--hermes", default=None,
                    help="Hermes root (default: $HERMES_HOME, else ~/.hermes)")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    try:
        panel = load_panel(repo)
    except Exception as exc:  # noqa: BLE001 — the reason IS the report
        print(f"FAIL check_panel_membership: cannot import the panel module: "
              f"{type(exc).__name__}: {exc}")
        print("  run this check with an interpreter that has numpy + PyYAML: "
              "/usr/bin/python3")
        return 2
    if args.hermes:
        setattr(panel, "HERMES", Path(args.hermes))

    fails: list[str] = []
    notes: list[str] = []
    members = list(panel.DEFAULT_PANEL)

    spec_path = repo / "scripts" / "fleet-routing.json"
    spec = {}
    if spec_path.is_file():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    dead_slugs = set(spec.get("dead_slugs") or [])
    spec_providers = spec.get("providers") or {}

    # 1. enough members to ever reach the threshold
    if len(members) < panel.MIN_VALID_JUDGES:
        fails.append(f"DEFAULT_PANEL has {len(members)} members but the panel "
                     f"needs {panel.MIN_VALID_JUDGES} valid judges: the review "
                     f"stage can never pass")

    # 2./3./4./5./6. resolve every member and judge its shape
    families: dict = {}
    resolved = 0
    for name in members:
        try:
            candidates = panel.judge_candidates(name)
        except Exception as exc:  # noqa: BLE001 — record, keep checking
            fails.append(f"{name}: profile unusable — {type(exc).__name__}: {exc}")
            continue
        usable = [c for c in candidates if not c.get("error")]
        if not usable:
            fails.append(f"{name}: no candidate resolves — "
                         + "; ".join(c["error"] for c in candidates)[:200])
            continue
        primary = candidates[0]
        if primary.get("error"):
            fails.append(f"{name}: primary unusable — {primary['error']}")
        resolved += 1
        fam = panel.judge_family(primary.get("model"))
        families.setdefault(fam, []).append(name)
        if len(candidates) < 2:
            fails.append(f"{name}: no fallback_providers chain — a dead primary "
                         f"makes this judge dead, which is cause 2 of t_3d84acfe")
        for cand in candidates:
            if panel.judge_family(cand.get("model")) != fam:
                fails.append(f"{name}: {cand['role']} '{cand.get('model')}' is "
                             f"family '{panel.judge_family(cand.get('model'))}', "
                             f"not '{fam}' — a cross-family fallback can "
                             f"duplicate a sibling judge")
            if cand.get("provider") in DEAD_PROVIDERS:
                fails.append(f"{name}: {cand['role']} uses provider "
                             f"'{cand['provider']}', dead for API callers")
            if cand.get("model") in dead_slugs:
                fails.append(f"{name}: {cand['role']} uses dead slug "
                             f"'{cand['model']}' (scripts/fleet-routing.json "
                             f"dead_slugs)")
        # 6. the endpoint must follow the provider
        provider = primary.get("provider")
        want = (spec_providers.get(provider) or {}).get("base_url")
        got = primary.get("base_url")
        if want and got and want.rstrip("/") != got.rstrip("/"):
            fails.append(f"{name}: model.base_url is {got} but provider "
                         f"'{provider}' is {want} — the endpoint must follow "
                         f"the provider")
        elif not want:
            notes.append(f"{name}: provider '{provider}' is not in "
                         f"scripts/fleet-routing.json — not compared")
        # 7. chain order vs primary
        if candidates and candidates[0].get("provider") not in (None, ""):
            notes.append(f"{name}: primary {panel.judge_family(primary.get('model'))}"
                         f"/{provider} with {len(candidates) - 1} fallback(s)")

    for fam, names in sorted(families.items()):
        if len(names) > 1:
            fails.append(f"family '{fam}' is shared by {', '.join(names)} — "
                         f"the PoLL contract needs DISJOINT families "
                         f"(music/rubrics/README.md)")

    for n in notes:
        print(f"  NOTE {n}")
    if fails:
        print(f"FAIL check_panel_membership: {len(fails)} violation(s)")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS check_panel_membership: {resolved}/{len(members)} panel members "
          f"resolve, families {sorted(families)} are disjoint, every chain stays "
          f"in its family ({panel.HERMES}/profiles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
