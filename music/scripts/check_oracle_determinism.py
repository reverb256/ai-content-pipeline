#!/usr/bin/env python3
"""check_oracle_determinism — the oracle's score must not depend on the NETWORK, and a
failed trend fetch must never score a genre HIGHER than a successful empty one.

WHY THIS EXISTS
---------------
`music/oracle.py` scores every genre's `trend_signal` (weight 0.10) with a live
DuckDuckGo scrape, inside the scoring path:

    def trend_signal_score(genre_name):
        try:
            ... urlopen("https://html.duckduckgo.com/html/?q=<genre> music trend 2026") ...
            count = len(re.findall(r'class="result__snippet"', html))
            if count >= 5:  return 10.0
            elif count == 0: return 3.0
            else:            return 3.0 + (count / 5.0) * 7.0
        except Exception:
            return 5.0                      # <-- the failure branch scores HIGHER

INCIDENT (2026-10-09 emission, measured 2026-10-16 by cards t_d3b9e218 / t_d8cc0a38)
-------------------------------------------------------------------------------
The board carries **two oracle cards for every genre** — 28 cards, 14 genres
(card t_bf0e5edd). Every pair differs by **exactly +0.20**, and
`0.20 == WEIGHTS['trend_signal'] * (5.0 - 3.0)` — i.e. the difference is
`trend_signal` on the exception branch (5.0) minus the same genre on a 200-with-zero-
snippets response (3.0). Measured across all 14 pairs: spread distribution `{0.2: 14}`.
So **the higher-scoring card of every pair is the run whose web fetch BROKE.** The
score is not just noisy; the failure mode is inverted — it rewards the broken run.

The same defect makes the score unreproducible. Measured within one worker session on
2026-10-16 (both from tree HEAD, minutes apart, registry and quota unchanged):

    $ /usr/bin/python3 music/oracle.py --dry-run
      elemental-water: 7.0/10          # fetch succeeded, 0 snippets -> trend 3.0
    $ score_genre("elemental-water", ...)        # fetch timed out
      scores: {... 'trend_signal': 5.0}  total: 7.2

Same genre, same registry, same quota ledger, two answers. Nothing in this lane
detected either the inversion or the unreproducibility; briefs quote oracle scores as
evidence and no check can recompute them.

WHAT IT DOES
------------
It never touches the network. It imports `music/oracle.py`, replaces
`urllib.request.urlopen` with a stub, and measures `trend_signal_score()` on two
branches that differ ONLY in how the fetch behaves:

  * ZERO  — HTTP 200, a real page body, zero `result__snippet` matches (the state this
            lane observes most often: every genre floors at 3.0);
  * FAIL  — `urlopen` raises (timeout / HTTP 403 / DNS).

Assertions:

  A1  FAIL <= ZERO.  A fetch that broke must not outrank a fetch that worked. (LIVE
      DEFECT: FAIL=5.0 > ZERO=3.0 today.)
  A2  `score_genre()` is deterministic given the same fetch behaviour: same registry
      and quota in, same total out, twice.
  A3  `WEIGHTS` sums to 1.0 (a weight edit that breaks closure invalidates every score
      claim in every brief).

Exit codes: 0 = contract holds, 1 = contract violated, 2 = usage error.

Usage:
  /usr/bin/python3 music/scripts/check_oracle_determinism.py [--repo DIR]
  /usr/bin/python3 music/scripts/check_oracle_determinism.py --selftest

Run with /usr/bin/python3: bare `python3` in a worker shell is the Hermes bundled
interpreter with no PyYAML, and `music/oracle.py` imports `yaml`.

cited: t_bf0e5edd (the 28-card double emission + root cause), t_d3b9e218 / t_d8cc0a38
(this genre's twin pair, which measured the 0.20 delta and the 7.0-vs-7.2 split).
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import sys
import urllib.error
from pathlib import Path

PASS_ZERO_SNIPPETS = "PASS-ZERO"
PASS_FETCH_FAILS = "PASS-FAIL"


def load_oracle(repo: Path):
    """Import <repo>/music/oracle.py without touching the network."""
    path = repo / "music" / "oracle.py"
    if not path.exists():
        raise SystemExit(f"FATAL: {path} not found")
    spec = importlib.util.spec_from_file_location("oracle_under_test", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FATAL: cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["oracle_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class _Stub:
    """Replacement for urllib.request.urlopen: 200 with N matching snippets, or raise."""

    def __init__(self, snippets: int, raise_exc: Exception | None = None):
        self.snippets = snippets
        self.raise_exc = raise_exc

    def __call__(self, req, timeout=None):  # noqa: ARG002
        if self.raise_exc is not None:
            raise self.raise_exc
        html = "<html>" + ('<span class="result__snippet">x</span>' * self.snippets) + "</html>"

        class _Resp:
            def read(self_inner):
                return html.encode("utf-8")

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False

        return _Resp()


def measure(oracle, mode: str, genre: str = "elemental-water") -> float:
    """Measure trend_signal_score under one fetch behaviour. No network."""
    real = oracle.urllib.request.urlopen
    try:
        if mode == PASS_ZERO_SNIPPETS:
            oracle.urllib.request.urlopen = _Stub(snippets=0)
        elif mode == PASS_FETCH_FAILS:
            oracle.urllib.request.urlopen = _Stub(
                snippets=0, raise_exc=urllib.error.URLError("stub: fetch failed"))
        else:
            raise ValueError(mode)
        return float(oracle.trend_signal_score(genre))
    finally:
        oracle.urllib.request.urlopen = real


def measure_total(oracle, mode: str, genre: str, quota: dict, genres: dict, lanes: dict) -> float:
    real = oracle.urllib.request.urlopen
    try:
        oracle.urllib.request.urlopen = _Stub(
            snippets=0,
            raise_exc=urllib.error.URLError("stub") if mode == PASS_FETCH_FAILS else None)
        r = oracle.score_genre(genre, genres[genre], lanes, quota)
        return float(r["total"])
    finally:
        oracle.urllib.request.urlopen = real


def contract_errors(zero: float, fail: float, weight: float = 0.10) -> list[str]:
    """A1, isolated so --selftest can prove it fires on an inverted pair."""
    if fail > zero:
        return [
            f"A1 VIOLATED: a FAILED trend fetch scores {fail} but a SUCCESSFUL empty fetch "
            f"scores {zero} — the broken run outranks the working one by {round(fail - zero, 4)} "
            f"on the component, i.e. {round((fail - zero) * weight, 4)} on the 10-point total "
            f"(component delta x WEIGHTS['trend_signal']). This is the defect that produced the "
            f"28-card double emission (t_bf0e5edd): the higher-scoring card of every twin pair "
            f"is the run whose web fetch broke."
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Oracle score determinism / trend-fetch contract.")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--genre", default="elemental-water")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the A1 assertion fires on an inverted pair and passes a correct one")
    args = ap.parse_args(argv)

    if args.selftest:
        good = contract_errors(3.0, 3.0)
        bad = contract_errors(3.0, 5.0)
        ok = (good == [] and len(bad) == 1)
        print(f"SELFTEST {'PASS' if ok else 'FAIL'} check_oracle_determinism: "
              f"correct pair (zero=3.0 fail=3.0) errors={len(good)} (want 0), "
              f"inverted pair (zero=3.0 fail=5.0) errors={len(bad)} (want 1)")
        return 0 if ok else 1

    repo = Path(args.repo).resolve()
    oracle = load_oracle(repo)

    problems: list[str] = []

    zero = measure(oracle, PASS_ZERO_SNIPPETS, args.genre)
    fail = measure(oracle, PASS_FETCH_FAILS, args.genre)
    problems += contract_errors(zero, fail, oracle.WEIGHTS["trend_signal"])

    quota = oracle.load_quota()
    reg = oracle.load_registry()
    genres = reg["genres"]
    lanes = reg["lanes"]

    t1 = measure_total(oracle, PASS_ZERO_SNIPPETS, args.genre, quota, genres, lanes)
    t2 = measure_total(oracle, PASS_ZERO_SNIPPETS, args.genre, quota, genres, lanes)
    if t1 != t2:
        problems.append(f"A2 VIOLATED: score_genre is nondeterministic under a fixed fetch "
                        f"behaviour: {t1} != {t2}")
    tf = measure_total(oracle, PASS_FETCH_FAILS, args.genre, quota, genres, lanes)
    if tf > t1:
        problems.append(f"A2 VIOLATED: a failed trend fetch raises the total for {args.genre} "
                        f"({tf} > {t1}) — scoring depends on the network, not on the genre.")

    w = sum(oracle.WEIGHTS.values())
    if abs(w - 1.0) > 1e-9:
        problems.append(f"A3 VIOLATED: WEIGHTS sums to {w}, not 1.0 — every score claim in "
                        f"every brief is now unreproducible.")

    print(f"oracle under test : {repo / 'music' / 'oracle.py'}")
    print(f"genre             : {args.genre}")
    print(f"trend 200/0-snippet: {zero}   trend fetch-fails: {fail}")
    print(f"total 200/0-snippet: {t1} (= {t2})   total fetch-fails: {tf}")
    print(f"WEIGHTS sum       : {w}")

    if problems:
        for p in problems:
            print(f"  - {p}")
        print("FAIL check_oracle_determinism: the trend fetch is not a pure function of the genre")
        return 1
    print("PASS check_oracle_determinism: trend fetch failure never outscores an empty success; "
          "score_genre is deterministic; WEIGHTS closes at 1.0")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL check_oracle_determinism: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
