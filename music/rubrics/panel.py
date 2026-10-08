#!/usr/bin/env python3
"""panel.py — the music reviewer panel: corpus-anchored rubrics + measured
evidence in, geometric-median aggregate out.

Research basis (all read, not summarized):
  - PoLL (Verga et al., arXiv:2404.18796): a panel of small judges from
    DISJOINT model families beats one big judge and costs ~7x less.
  - RoPoLL (Acharya et al., arXiv:2606.30931): the arithmetic mean has
    unbounded bias under one contaminated judge; the GEOMETRIC MEDIAN has
    the optimal 1/2 breakdown point and is tuning-free. Computed here via
    the modified Weiszfeld iteration (Vardi & Zhang 2000).
  - Evaluation Illusion (arXiv:2603.11027): judges anchor scores on shared
    surface heuristics when given generic rubrics; knowledge-grounded,
    corpus-anchored rubrics produce substantive assessment. Hence every
    criterion cites real production conventions and numbers, and the
    judges receive MEASURED evidence (measure.py), not vibes.

Design contract with gate_quality.py (music/gates/gate_quality.py, card
t_ef4773bd): this panel writes review.json (verdict/findings/reviewer/
reviewer_model/master.sha256/reviewed_at) that the existing gate validates
unchanged. Full panel detail goes to panel-detail.json next to it.

The pipeline is genre-generic: genre -> family -> rubric file, all data.
The panel membership is profile names resolved from their Hermes profile
configs (model, provider, base_url, key env) — no model is hardcoded
here.

Usage:
  python3 music/rubrics/panel.py --audio <file> --genre <genres.yaml id> \
      [--style-claim <file>] [--lyrics <file>] [--producer-model <name>] \
      [--out-dir <dir>] [--panel a,b,c,d] [--limit 3] [--json]

Exit codes: 0 = review completed (verdict pass or fail), 1 = hard error.
The verdict itself is IN the JSON; the exit code only reports that the
panel ran.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
MUSIC = REPO / "music"
RUBRICS = MUSIC / "rubrics"


def _find_hermes_root() -> Path:
    """The Hermes root that actually contains profiles/ and .env.
    HERMES_HOME may point at a profile dir (e.g. inside a worker
    session); walk up until the real root is found."""
    cand = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    for _ in range(4):
        if (cand / "profiles").is_dir():
            return cand
        if cand.parent == cand:
            break
        cand = cand.parent
    return Path.home() / ".hermes"


HERMES = _find_hermes_root()

DEFAULT_PANEL = ("reviewer-deepseek", "reviewer-longcat",
                 "reviewer-minimax", "reviewer-nemotron")
DISAGREE_SPREAD = 3.0        # max overall spread before human triage
CRITERION_SPREAD_FLAG = 4.0  # per-criterion spread worth flagging
MIN_VALID_JUDGES = 3
CALL_TIMEOUT_S = 180
MAX_ATTEMPTS = 3
BACKOFF_S = 8

sys.path.insert(0, str(RUBRICS))
from measure import measure_track  # noqa: E402


# ── panel member resolution (data, from profile configs) ────────────────────

def load_env_file(path: Path) -> dict:
    env = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _fleet_endpoint(provider: str) -> tuple:
    """(base_url, api_key_env) for a provider, from the sources the
    fleet probe uses: fleet-route.py ENDPOINTS first (it covers nvidia,
    which the JSON spec lacks), then fleet-routing.json providers."""
    fleet_py = REPO / "scripts" / "fleet-route.py"
    if fleet_py.is_file():
        ns: dict = {"__file__": str(fleet_py), "__name__": "fleet_route"}
        exec(compile(fleet_py.read_text(encoding="utf-8"),
                     str(fleet_py), "exec"), ns)
        endpoints = ns.get("ENDPOINTS") or {}
        if provider in endpoints:
            base, env = endpoints[provider]
            return base, env
    spec_path = REPO / "scripts" / "fleet-routing.json"
    if spec_path.is_file():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        entry = (spec.get("providers") or {}).get(provider) or {}
        return entry.get("base_url", ""), entry.get("api_key_env", "")
    return "", ""


def resolve_judge(profile_name: str) -> dict:
    """Model + endpoint + key for one reviewer profile. Never logs keys.
    Resolution order: the profile's own config.yaml provider block first;
    if the profile's provider is missing there, fall back to the fleet
    routing spec (scripts/fleet-routing.json ENDPOINTS — same mapping
    fleet-route.py probes with)."""
    cfg_path = HERMES / "profiles" / profile_name / "config.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"no reviewer profile config: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    model = (cfg.get("model") or {}).get("default", "")
    provider = (cfg.get("model") or {}).get("provider", "")
    prov = (cfg.get("providers") or {}).get(provider) or {}
    base_url = prov.get("base_url", "")
    key_env = prov.get("api_key_env", "")
    if not base_url:
        # Endpoint fallback, same sources the fleet probe uses:
        #   1. fleet-route.py ENDPOINTS (covers nvidia, which the JSON
        #      spec lacks)
        #   2. scripts/fleet-routing.json providers
        base_url, fallback_key_env = _fleet_endpoint(provider)
        key_env = key_env or fallback_key_env
    if not (model and provider and base_url and key_env):
        raise ValueError(
            f"profile {profile_name}: incomplete routing "
            f"(model={model!r} provider={provider!r} base_url={base_url!r})")
    # key: profile .env first, then the shared ~/.hermes/.env
    key = ""
    for env_file in (HERMES / "profiles" / profile_name / ".env",
                     HERMES / ".env"):
        key = load_env_file(env_file).get(key_env, "")
        if key:
            break
    if not key:
        raise ValueError(
            f"profile {profile_name}: {key_env} not set in profile or "
            f"shared .env — cannot call {model}")
    return {"name": profile_name, "provider": provider, "model": model,
            "base_url": base_url.rstrip("/"), "key_env": key_env,
            "key": key}


# ── rubric + genre resolution (all data) ────────────────────────────────────

def genre_family(genre: str) -> str:
    doc = yaml.safe_load((MUSIC / "genres.yaml").read_text(encoding="utf-8"))
    entry = (doc.get("genres") or {}).get(genre)
    if not entry:
        known = ", ".join(sorted((doc.get("genres") or {}).keys()))
        raise SystemExit(
            f"ERROR: genre {genre!r} is not in music/genres.yaml. Known: {known}")
    return str(entry["family"])


def load_rubric(family: str) -> dict:
    path = RUBRICS / f"{family}.json"
    if not path.is_file():
        available = ", ".join(sorted(p.stem for p in RUBRICS.glob("*.json")))
        raise SystemExit(
            f"ERROR: no rubric for family {family!r} ({path}). Available: {available}")
    rubric = json.loads(path.read_text(encoding="utf-8"))
    for key in ("family", "criteria", "pass_threshold", "reject_signals"):
        if key not in rubric:
            raise SystemExit(f"ERROR: rubric {path} missing '{key}'")
    return rubric


# ── judge prompt ─────────────────────────────────────────────────────────────

RULES = """You are a professional mastering engineer and genre specialist on an
independent review panel. You are reviewing ONE music track.

HARD HONESTY RULES:
1. You CANNOT listen to the audio. You receive MEASURED evidence from
   signal analysis and the producer's own claims. Score ONLY what this
   evidence supports.
2. Never invent measurements. Never assume a craft detail you cannot
   verify — score it and list the criterion id in "unverifiable".
3. The rubric criteria cite real production conventions (corpus anchors).
   Apply the anchor numbers exactly as stated. A track outside the
   anchor numbers is out of genre, however pleasant it sounds.
4. Reject signals are fatal genre violations. Flag one ONLY when the
   measured evidence or the producer's claim actually shows it.
5. Score every criterion 1-10 per its guide. Be strict: 7 = solid
   professional work, 10 = exemplary, 4 = flawed, 1 = absent/broken.

Respond with ONE JSON object and nothing else:
{
  "criteria_scores": {"<criterion_id>": <1-10>, ...},   // every id, once
  "overall": <1-10 weighted mean of your own scores>,
  "findings": ["<specific, evidence-cited findings>"],
  "reject_signals_hit": ["<verbatim strings from reject_signals>"],
  "unverifiable": ["<criterion ids you could not verify>"]
}"""


def build_prompt(rubric: dict, genre: str, evidence: dict,
                 style_claim: str, lyrics: str) -> str:
    crit_lines = []
    for c in rubric["criteria"]:
        crit_lines.append(
            f"- id: {c['id']}\n  name: {c['name']}\n  weight: {c['weight']}\n"
            f"  type: {c['type']}\n  anchor: {c['anchor']}\n"
            f"  evidence to use: {c['evidence']}\n  scoring guide: {c['guide']}")
    return "\n".join([
        RULES,
        "",
        f"GENRE (registry id): {genre}",
        f"GENRE FAMILY: {rubric['family']}",
        "",
        "RUBRIC (criteria, anchors, guides):",
        "\n".join(crit_lines),
        "",
        "REJECT SIGNALS (fatal if the evidence shows them):",
        "\n".join(f"- {s}" for s in rubric["reject_signals"]),
        "",
        "MEASURED EVIDENCE (ffmpeg + numpy signal analysis of the actual file):",
        json.dumps(evidence, indent=2),
        "",
        "PRODUCER'S STYLE CLAIM:",
        style_claim or "(none provided)",
        "",
        "LYRICS (first 60 lines):" if lyrics else "",
        "\n".join(lyrics.splitlines()[:60]) if lyrics else "",
    ])


# ── LLM call ─────────────────────────────────────────────────────────────────

def call_judge(judge: dict, prompt: str) -> dict:
    """One chat-completions call. Returns parsed score dict. Raises on
    unrecoverable failure; retries once on bad JSON."""
    url = judge["base_url"] + "/chat/completions"
    body = json.dumps({
        "model": judge["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 16000,
    }).encode()
    headers = {
        "Authorization": f"Bearer {judge['key']}",
        "Content-Type": "application/json",
        # python-urllib's default UA is Cloudflare-banned on some
        # providers (error 1010); use the same UA the fleet probe uses.
        "User-Agent": "hermes-music-panel/1.0",
    }
    last_err = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(url, data=body, headers=headers,
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=CALL_TIMEOUT_S) as r:
                data = json.loads(r.read().decode())
            content = ((data.get("choices") or [{}])[0]
                       .get("message", {}).get("content", ""))
            if not content:
                content = ((data.get("choices") or [{}])[0]
                           .get("message", {}).get("reasoning_content", ""))
            parsed = extract_json(content)
            if parsed is not None:
                parsed["_raw_content_len"] = len(content)
                return parsed
            last_err = f"no JSON object in response (len={len(content)})"
        except urllib.error.HTTPError as e:
            body_txt = ""
            try:
                body_txt = e.read().decode()[:300]
            except Exception:
                pass
            last_err = f"HTTP {e.code}: {body_txt}"
            # 429/5xx are transient: back off and retry. 4xx (auth,
            # credits) are permanent for this run: do not retry.
            if 400 <= e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = f"network: {e}"
        except json.JSONDecodeError as e:
            last_err = f"bad JSON from API: {e}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S * attempt)
    raise RuntimeError(last_err)


def extract_json(text: str):
    """First balanced JSON object in the text, or None."""
    if not text:
        return None
    m = re.search(r"\{", text)
    if not m:
        return None
    depth, start = 0, m.start()
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start:i + 1])
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    return None
    return None


# ── geometric median (RoPoLL) ───────────────────────────────────────────────

def geometric_median(points: list) -> np.ndarray:
    """Modified Weiszfeld iteration (Vardi & Zhang 2000), per RoPoLL
    arXiv:2606.30931 §4.3. Tuning-free, 1/2 breakdown point."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or len(pts) == 0:
        raise ValueError("geometric_median needs a non-empty 2-D array")
    if len(pts) == 1:
        return pts[0]
    x = pts.mean(axis=0)
    for _ in range(1000):
        d = np.linalg.norm(pts - x, axis=1)
        mask = d < 1e-12
        if mask.any():
            # Vardi-Zhang: coincident point needs the modified step
            others = pts[~mask]
            if len(others) == 0:
                return x
            w = 1.0 / np.linalg.norm(others - x, axis=1)
            eta = float(mask.sum())
            T = (w @ others) / (w.sum() + eta)
            C = pts[mask].mean(axis=0)
            alpha = eta / (w.sum() + eta)
            x_new = (1.0 - alpha) * T + alpha * C
        else:
            w = 1.0 / d
            x_new = (w @ pts) / w.sum()
        if np.linalg.norm(x_new - x) < 1e-10:
            return x_new
        x = x_new
    return x


def aggregate(rubric: dict, judge_scores: list) -> dict:
    """Geometric median across the panel over the criterion-score vectors.
    Returns aggregate per-criterion scores, weighted overall, spread info."""
    crit_ids = [c["id"] for c in rubric["criteria"]]
    weights = {c["id"]: float(c["weight"]) for c in rubric["criteria"]}
    # Sanitize: a judge may emit null/string scores (parser drift). A
    # missing/null criterion is scored 1 (absent) and flagged — it must
    # not crash the aggregation, and it must be visible in the detail.
    sanitized, defects = [], []
    for js in judge_scores:
        cs = js.get("criteria_scores") or {}
        vec, defect_ids = [], []
        for cid in crit_ids:
            v = cs.get(cid)
            try:
                vec.append(float(v))
            except (TypeError, ValueError):
                vec.append(1.0)
                defect_ids.append(cid)
        if defect_ids:
            defects.append({"judge": js.get("judge"),
                            "bad_scores": defect_ids})
            js["criteria_scores"] = {cid: vec[i]
                                     for i, cid in enumerate(crit_ids)}
        sanitized.append(vec)
    vectors = sanitized
    gm = geometric_median(vectors)
    agg = {cid: round(float(v), 2) for cid, v in zip(crit_ids, gm)}
    overall = sum(agg[cid] * weights[cid] for cid in crit_ids) \
        / sum(weights.values())
    arr = np.asarray(vectors)
    spread = {cid: round(float(arr[:, i].max() - arr[:, i].min()), 2)
              for i, cid in enumerate(crit_ids)}
    overalls = [float(js.get("overall",
                             np.average([js["criteria_scores"][c]
                                          for c in crit_ids],
                                         weights=[weights[c]
                                                  for c in crit_ids])))
                for js in judge_scores]
    return {
        "aggregate_criteria": agg,
        "aggregate_overall": round(float(overall), 2),
        "judge_overalls": [round(o, 2) for o in overalls],
        "overall_spread": round(float(max(overalls) - min(overalls)), 2),
        "criterion_spread": spread,
        "wide_criteria": [cid for cid, s in spread.items()
                          if s >= CRITERION_SPREAD_FLAG],
        "score_defects": defects,
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="panel.py — music reviewer panel with geometric-median "
                    "aggregation (RoPoLL) over corpus-anchored rubrics")
    ap.add_argument("--audio", required=True)
    ap.add_argument("--genre", required=True,
                    help="genre id from music/genres.yaml")
    ap.add_argument("--style-claim", default=None,
                    help="file with the producer's style claim / prompt")
    ap.add_argument("--lyrics", default=None, help="lyrics file (vocal familes)")
    ap.add_argument("--producer-model", default=None,
                    help="model that produced the track (independence check)")
    ap.add_argument("--out-dir", default=".",
                    help="where to write review.json + panel-detail.json")
    ap.add_argument("--panel", default=",".join(DEFAULT_PANEL),
                    help="comma-separated reviewer profile names")
    ap.add_argument("--limit", type=int, default=0,
                    help="use only the first N panel members (testing)")
    ap.add_argument("--json", action="store_true",
                    help="print the final review JSON")
    args = ap.parse_args(argv)

    audio = Path(args.audio)
    if not audio.is_file():
        print(f"ERROR: no such audio file: {audio}", file=sys.stderr)
        return 1
    family = genre_family(args.genre)
    rubric = load_rubric(family)

    # 1. measure the artifact (gates execute, never trust names)
    evidence = measure_track(audio)
    evidence["claimed_genre"] = args.genre
    evidence["claimed_family"] = family

    style_claim = (Path(args.style_claim).read_text(encoding="utf-8")
                   if args.style_claim else "")
    lyrics = (Path(args.lyrics).read_text(encoding="utf-8")
              if args.lyrics else "")
    prompt = build_prompt(rubric, args.genre, evidence, style_claim, lyrics)

    # 2. run the panel (PoLL: disjoint model families)
    members = [m.strip() for m in args.panel.split(",") if m.strip()]
    if args.limit:
        members = members[:args.limit]
    print(f"[panel] genre={args.genre} family={family} "
          f"rubric={family}.json "
          f"members={members}", flush=True)
    judge_scores, failures = [], []
    for name in members:
        judge = resolve_judge(name)
        t0 = time.time()
        try:
            score = call_judge(judge, prompt)
        except Exception as e:  # noqa: BLE001 — record, continue
            failures.append({"judge": name, "model": judge["model"],
                             "error": str(e)[:400]})
            print(f"[panel] {name} ({judge['model']}): FAILED — "
                  f"{str(e)[:120]}", flush=True)
            continue
        score["judge"] = name
        score["model"] = judge["model"]
        score["elapsed_s"] = round(time.time() - t0, 1)
        missing = [c["id"] for c in rubric["criteria"]
                   if c["id"] not in (score.get("criteria_scores") or {})]
        if missing:
            failures.append({"judge": name, "model": judge["model"],
                             "error": f"incomplete scores, missing {missing}"})
            print(f"[panel] {name}: incomplete scores {missing}", flush=True)
            continue
        judge_scores.append(score)
        print(f"[panel] {name} ({judge['model']}): overall="
              f"{score.get('overall')} "
              f"rejects={len(score.get('reject_signals_hit') or [])} "
              f"({score['elapsed_s']}s)", flush=True)

    if len(judge_scores) < MIN_VALID_JUDGES:
        print(f"[panel] only {len(judge_scores)} valid judges "
              f"(need {MIN_VALID_JUDGES}); failures: {failures}",
              file=sys.stderr)

    # 3. aggregate (RoPoLL: geometric median over the score vectors).
    #    With zero judges this is a hard failure: write an honest
    #    fail-verdict record with the failures, exit non-zero.
    if not judge_scores:
        review = {
            "master": {"sha256": hashlib.sha256(
                audio.read_bytes()).hexdigest(), "path": str(audio)},
            "reviewer_model": "panel[none-reachable]",
            "producer_model": args.producer_model or "unknown",
            "verdict": "fail",
            "findings": ["PANEL UNREACHABLE — no judge returned a valid "
                         "score; human triage required"]
                        + [f"[{f['judge']}] {f['error']}" for f in failures],
            "reviewed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "reviewer": "reviewer-panel",
            "aggregate_overall": 0.0,
            "pass_threshold": rubric["pass_threshold"],
        }
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "review.json").write_text(
            json.dumps(review, indent=2, ensure_ascii=False),
            encoding="utf-8")
        print("[panel] VERDICT fail (no judges reachable) — wrote "
              f"{out / 'review.json'}", flush=True)
        return 1

    agg = aggregate(rubric, judge_scores)

    # 4. reject signals: majority-hit = fatal (robust to one contaminated
    #    judge; geometric median alone cannot encode categorical rules)
    signal_votes: dict = {}
    for js in judge_scores:
        for s in (js.get("reject_signals_hit") or []):
            signal_votes[s] = signal_votes.get(s, 0) + 1
    majority = max(1, len(judge_scores) // 2 + 1)
    fatal_signals = [s for s, n in signal_votes.items() if n >= majority]

    # 5. verdict
    findings = []
    for js in judge_scores:
        for f in (js.get("findings") or [])[:5]:
            findings.append(f"[{js['judge']}] {f}")
    triage = (agg["overall_spread"] >= DISAGREE_SPREAD
              or len(judge_scores) < MIN_VALID_JUDGES)
    passed = (agg["aggregate_overall"] >= float(rubric["pass_threshold"])
              and not fatal_signals and not triage)
    verdict = "pass" if passed else "fail"
    if fatal_signals:
        findings.insert(0, "REJECT SIGNALS (majority of panel): "
                     + "; ".join(fatal_signals))
    if triage:
        findings.insert(0, f"PANEL DISAGREEMENT — human triage required "
                     f"(overall spread {agg['overall_spread']}, "
                     f"valid judges {len(judge_scores)})")

    # 6. write review.json (gate_quality.py contract) + panel-detail.json
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    models = "+".join(js["model"] for js in judge_scores)
    review = {
        "master": {"sha256": digest, "path": str(audio)},
        "reviewer_model": f"panel[{models}]",
        "producer_model": args.producer_model or "unknown",
        "verdict": verdict,
        "findings": findings,
        "reviewed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "reviewer": "reviewer-panel",
        "aggregate_overall": agg["aggregate_overall"],
        "pass_threshold": rubric["pass_threshold"],
    }
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    detail = {
        "genre": args.genre,
        "family": family,
        "rubric_file": f"music/rubrics/{family}.json",
        "evidence": evidence,
        "judges": judge_scores,
        "judge_failures": failures,
        "aggregation": {
            "method": "geometric median (modified Weiszfeld, Vardi-Zhang 2000; "
                      "RoPoLL arXiv:2606.30931)",
            **agg,
            "reject_signal_votes": signal_votes,
            "fatal_signals": fatal_signals,
            "majority_needed": majority,
            "triage": triage,
        },
        "review": review,
    }
    (out / "panel-detail.json").write_text(
        json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "review.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[panel] aggregate overall = {agg['aggregate_overall']} "
          f"(threshold {rubric['pass_threshold']}) "
          f"judge overalls = {agg['judge_overalls']} "
          f"spread = {agg['overall_spread']}")
    print(f"[panel] fatal signals = {fatal_signals} triage = {triage} "
          f"-> VERDICT {verdict}")
    print(f"[panel] wrote {out / 'review.json'} and {out / 'panel-detail.json'}")
    if args.json:
        print(json.dumps(review, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
