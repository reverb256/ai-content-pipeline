#!/usr/bin/env python3
"""probe_judges.py — LIVE liveness probe of the reviewer panel.

Why this exists
---------------
Card t_3d84acfe, measured 2026-10-16: the panel wrote `verdict: fail` for every
track because NO judge was reachable, and nothing detected it. The panel runs
only when a human (or an agent) runs it, so the REVIEW stage had silently become
an autofail, and `music/gates/gate_quality.py` — which validates exactly that
review.json — could not pass for any asset.

This is the live half of the pair; `music/scripts/check_panel_membership.py` is
the offline half (shape of the configs, no tokens). This probe asks each panel
member's CHAIN the same question the panel asks, and fails loudly when fewer
than `panel.MIN_VALID_JUDGES` members answer, or when the live judges are not
from disjoint model families.

What counts as live
-------------------
Not "HTTP 200": a member is live only when it returns a parseable JSON object
with an `overall` key. Measured 2026-10-16, `meituan/longcat-2.5-preview:free`
answered HTTP 200 with EMPTY content (its reasoning consumed the budget), which
a 1-token probe would have called OK while the panel recorded a dead judge.

Usage:
  /usr/bin/python3 music/rubrics/probe_judges.py [--members a,b] [--timeout S]
                      [--json]   # also print a machine-readable result

Exit codes: 0 = at least MIN_VALID_JUDGES members live from disjoint families;
1 = the panel would autofail (or the live families collide).
Run it with an interpreter that has PyYAML (the Hermes bundled one does not).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel  # noqa: E402

PROMPT = (
    'You are a music mastering judge. Reply with ONE JSON object and nothing '
    'else: {"criteria_scores": {"loop_safety": 7}, "overall": 7, '
    '"findings": ["probe"], "reject_signals_hit": [], "unverifiable": []}'
)


def probe(cand: dict, timeout: float) -> dict:
    """One real judge-shaped call. Returns the candidate annotated with
    ok/served/latency/error. Never logs keys."""
    if cand.get("error"):
        return {**cand, "ok": False, "error": cand["error"]}
    body = json.dumps({
        "model": cand["model"],
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.0,
        "max_tokens": 4000,
    }).encode()
    req = urllib.request.Request(
        cand["base_url"] + "/chat/completions", data=body, method="POST",
        headers={"Authorization": f"Bearer {cand['key']}",
                 "Content-Type": "application/json",
                 "User-Agent": "hermes-music-panel/1.0"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        latency = round(time.time() - t0, 1)
        msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
        content = (msg.get("content") or msg.get("reasoning_content") or "")
        parsed = panel.extract_json(content)
        ok = bool(parsed and "overall" in parsed)
        return {**cand, "ok": ok, "served": data.get("model", "?"),
                "latency_s": latency,
                "error": "" if ok else
                         f"no JSON with an 'overall' key (len={len(content)})"}
    except urllib.error.HTTPError as e:
        try:
            txt = e.read().decode()[:200].replace("\n", " ")
        except Exception:  # noqa: BLE001 — the body is optional evidence
            txt = ""
        return {**cand, "ok": False, "latency_s": round(time.time() - t0, 1),
                "error": f"HTTP {e.code}: {txt}"}
    except Exception as e:  # noqa: BLE001 — every failure is this probe's output
        return {**cand, "ok": False, "latency_s": round(time.time() - t0, 1),
                "error": f"{type(e).__name__}: {e}"[:200]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="live liveness probe of the "
                                            "reviewer panel's judges")
    ap.add_argument("--members", default=",".join(panel.DEFAULT_PANEL),
                    help="comma-separated reviewer profile names")
    ap.add_argument("--timeout", type=float, default=120.0,
                    help="per-call timeout in seconds")
    ap.add_argument("--json", action="store_true",
                    help="also print a machine-readable result")
    args = ap.parse_args(argv)

    members = [m.strip() for m in args.members.split(",") if m.strip()]
    live: list[dict] = []
    attempts: list[dict] = []
    for name in members:
        try:
            candidates = panel.judge_candidates(name)
        except Exception as e:  # noqa: BLE001 — a broken profile is a result
            attempts.append({"member": name, "role": "profile", "model": "-",
                             "ok": False,
                             "error": f"{type(e).__name__}: {e}"[:200]})
            print(f"FAIL  {name:<22} {'profile':<11} {'-':<44} "
                  f"no profile config", flush=True)
            continue
        winner = None
        for cand in candidates:
            res = probe(cand, args.timeout)
            attempts.append({"member": name,
                             **{k: v for k, v in res.items() if k != "key"}})
            state = "OK  " if res["ok"] else "FAIL"
            print(f"{state}  {name:<22} {str(res['role']):<11} "
                  f"{str(res.get('model')):<44} "
                  f"{res.get('latency_s', 0):>6}s "
                  f"served={res.get('served', '-')} "
                  f"{res.get('error', '')[:70]}", flush=True)
            if res["ok"]:
                winner = {**res, "member": name}
                break
        if winner:
            live.append(winner)

    families: dict = {}
    for w in live:
        families.setdefault(panel.judge_family(w["model"]), []).append(
            w["member"])
    collisions = {f: n for f, n in families.items() if len(n) > 1}
    enough = len(live) >= panel.MIN_VALID_JUDGES

    if args.json:
        print(json.dumps({
            "probed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "members": members,
            "live": [{"member": w["member"], "role": w["role"],
                      "provider": w["provider"], "model": w["model"],
                      "served": w.get("served"),
                      "latency_s": w.get("latency_s")} for w in live],
            "live_count": len(live),
            "needed": panel.MIN_VALID_JUDGES,
            "families": families,
            "family_collisions": collisions,
            "attempts": attempts,
        }, indent=2))

    if not enough:
        print(f"FAIL probe_judges: only {len(live)} of {len(members)} panel "
              f"members answered a judge-shaped call (need "
              f"{panel.MIN_VALID_JUDGES}) — the REVIEW stage would write "
              f"verdict: fail for every track (card t_3d84acfe)",
              file=sys.stderr)
        return 1
    if collisions:
        print("FAIL probe_judges: the live panel is NOT disjoint — "
              + "; ".join(f"{f} = {', '.join(n)}"
                          for f, n in collisions.items())
              + " (music/rubrics/README.md PoLL contract)", file=sys.stderr)
        return 1
    print(f"PASS probe_judges: {len(live)}/{len(members)} members live, "
          f"families {sorted(families)} disjoint")
    return 0


if __name__ == "__main__":
    sys.exit(main())
