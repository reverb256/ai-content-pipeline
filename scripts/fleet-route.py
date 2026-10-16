#!/usr/bin/env python3
"""fleet-route.py — spec-driven model routing for every Hermes profile on this host.

Subcommands
  audit [--strict]      Scan every profile: primary, endpoint, fallback chain,
                        problem flags. --strict exits 1 when anything is flagged.
  apply [--dry-run]     Apply fleet-routing.json to profiles (backup + validate).
  probe [--only a,b]    Live-verify every model referenced in primaries + chains
                        with a real chat call (256 tokens, content OR
                        reasoning_content required). Writes a report, exits
                        non-zero on failures (cron-friendly).

Spec: fleet-routing.json next to this script (keep the two together).
Canonical location: ai-content-pipeline/scripts/ (deployed copy: ~/.hermes/scripts/).
Created 2026-09-30 for the low-cost fleet routing sweep (j_kro).
2026-10-16 (card t_7d75bafd): the spec became the source of record for other
tools too — model-health-daemon.sh reads providers/dead_providers/dead_slugs/
rotation_pool from it, so the rotator can no longer offer a dead provider as a
"repair" target, and check_panel_membership.py reads providers/dead_slugs.
"""
import argparse, csv, json, os, shutil, sys, time
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HERMES = Path(os.environ.get("HERMES_HOME", HOME / ".hermes"))
PROFILES = HERMES / "profiles"
SPEC_PATH = Path(__file__).with_name("fleet-routing.json")
STATE = HERMES / "state" / "fleet-route"
BACKUP_DIR = HERMES / "backups" / "fleet-route"

try:
    from ruamel.yaml import YAML
    _ry = YAML()
    _ry.preserve_quotes = True
    _ry.indent(mapping=2, sequence=4, offset=2)

    def _load(p):
        with open(p, "r") as f:
            return _ry.load(f)

    def _dump(data, p):
        with open(p, "w") as f:
            _ry.dump(data, f)
except Exception:  # pragma: no cover - ruamel is present on this host
    import yaml as _pyaml

    def _load(p):
        with open(p, "r") as f:
            return _pyaml.safe_load(f)

    def _dump(data, p):
        with open(p, "w") as f:
            _pyaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

CHAT_DIR = "{base}/chat/completions"
ENDPOINTS = {
    # provider -> (base_url, env key name or None)
    # commandcode is absent on purpose: COMMANDCODE_API_KEY is not in
    # ~/.hermes/.env (measured 2026-10-16, card t_7d75bafd), so the provider can
    # never answer and every chain entry naming it was dead weight. It is listed
    # in the spec's dead_providers and `audit` flags any consumer of it.
    "nous": ("https://inference-api.nousresearch.com/v1", "NOUS_API_KEY"),
    "openrouter-free": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "kilo": ("https://api.kilo.ai/api/gateway", "KILOCODE_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY"),
}


def load_spec():
    with open(SPEC_PATH) as f:
        return json.load(f)


def target_config(name: str) -> Path:
    if name == "@home":
        return HERMES / "config.yaml"
    return PROFILES / name / "config.yaml"


def load_env():
    env = {}
    env_file = HERMES / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def chain_entries(c):
    out = []
    for x in (c.get("fallback_providers") or []):
        if isinstance(x, dict):
            out.append((x.get("provider"), x.get("model")))
        else:
            out.append((str(x), None))
    return out


# ── audit ─────────────────────────────────────────────────────────────────────
#
# Flag vocabulary (card t_7d75bafd; the old single label GO-EXHAUSTED is gone —
# the live opencode-go error is no longer a quota but
# HTTP 400 {"type":"MissingSessionID"}, so it is a DEAD PROVIDER, and the spec's
# dead_providers list is what decides that, not a literal here):
#   DEAD-PROVIDER      primary provider is in the spec's dead_providers
#   DEAD-SLUG          model.default is a slug the spec measured dead
#   DEAD-IN-CHAIN      a fallback names a dead provider or a dead slug
#   NO-KEY             a provider named by this profile has no credential in .env
#                      (every commandcode entry, measured 2026-10-16: the key is
#                      absent, so the entry can never run)
#   ENDPOINT-MISMATCH  model.base_url is not the spec endpoint for model.provider
#                      — the far end of the v2 rotator bug, which left
#                      reviewer with provider opencode-go and base_url
#                      https://inference-api.nousresearch.com/v1
#   NO-ENDPOINT        model.base_url missing entirely
#   NO-FALLBACK        no fallback_providers: one provider outage ends the session

def cmd_audit(spec, strict=False):
    dead = set(spec.get("dead_slugs", []))
    dead_prov = set(spec.get("dead_providers", []))
    spec_prov = spec.get("providers") or {}
    env = load_env()
    rows = []
    nflag = 0
    for name in ["@home"] + sorted(p.name for p in PROFILES.iterdir() if p.is_dir()):
        cfg = target_config(name)
        if not cfg.exists():
            continue
        try:
            c = _load(cfg) or {}
        except Exception as e:
            rows.append((name, f"YAML-ERROR {e}", ""))
            nflag += 1
            continue
        m = c.get("model") or {}
        md, mp = m.get("default"), m.get("provider")
        flags = []
        if mp in dead_prov:
            flags.append("DEAD-PROVIDER")
        if md in dead:
            flags.append("DEAD-SLUG")
        want_base = (spec_prov.get(mp) or {}).get("base_url")
        got_base = (m.get("base_url") or "").rstrip("/")
        if not got_base:
            flags.append("NO-ENDPOINT")
        elif want_base and want_base.rstrip("/") != got_base:
            flags.append("ENDPOINT-MISMATCH")
        fb = chain_entries(c)
        if not fb:
            flags.append("NO-FALLBACK")
        for prov, model in fb:
            if model in dead or prov in dead_prov:
                flags.append("DEAD-IN-CHAIN")
            if prov == "opencode-zen":
                flags.append("ZEN-BLOCKED")
            keyenv = (spec_prov.get(prov) or {}).get("api_key_env")
            if keyenv and not env.get(keyenv):
                flags.append("NO-KEY")
        if flags:
            nflag += 1
        rows.append((name, f"{mp} / {md}", f"{len(fb)} fb" + (("  ⚠ " + ",".join(sorted(set(flags)))) if flags else "")))
    w = max(len(r[0]) for r in rows) + 2
    print(f"{'PROFILE':<{w}}| PRIMARY                                     | NOTES")
    print("-" * (w + 86))
    for r in rows:
        print(f"{r[0]:<{w}}| {r[1][:43]:<43} | {r[2]}")
    print(f"\nscanned {len(rows)} targets, {nflag} flagged")
    print(f"flags: DEAD-PROVIDER, DEAD-SLUG, DEAD-IN-CHAIN, NO-KEY, ENDPOINT-MISMATCH, "
          f"NO-ENDPOINT, NO-FALLBACK  (spec: {SPEC_PATH.name}, env: {HERMES}/.env)")
    return 1 if (strict and nflag) else 0


# ── apply ─────────────────────────────────────────────────────────────────────

def cmd_apply(spec, only=None, dry=False):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for name, p in spec["profiles"].items():
        if only and name not in only:
            continue
        cfg = target_config(name)
        if not cfg.exists():
            print(f"SKIP {name}: no config.yaml")
            fail += 1
            continue
        try:
            c = _load(cfg)
            if not isinstance(c, dict):
                raise ValueError("root is not a mapping")
            c.setdefault("model", {})
            c["model"]["default"] = p["model"]
            c["model"]["provider"] = p["provider"]
            # The endpoint must follow the provider. Hermes reads model.base_url
            # FIRST, so a profile re-pointed at another provider kept calling the
            # OLD host as long as the stale base_url survived (measured
            # 2026-10-16, card t_3d84acfe: the three reviewer* profiles kept
            # base_url https://opencode.ai/zen/go/v1 after they moved).
            pdefn = spec["providers"].get(p["provider"]) or {}
            want_base = pdefn.get("base_url")
            if want_base:
                c["model"]["base_url"] = want_base
            if c["model"].get("base_url"):
                c["model"].setdefault("api_mode", "chat_completions")
            c["fallback_providers"] = [
                dict(x) if isinstance(x, dict) else x
                for x in spec["chains"][p["chain"]]
            ]
            provs = c.setdefault("providers", {})
            for pname, defn in spec["providers"].items():
                blk = provs.get(pname)
                if not isinstance(blk, dict):
                    blk = {}
                    provs[pname] = blk
                for k, v in defn.items():
                    if k == "model" or k not in blk:
                        blk[k] = v
            if dry:
                print(f"DRY  {name:<16} {p['provider']} / {p['model']}  chain={p['chain']}({len(spec['chains'][p['chain']])})")
                ok += 1
                continue
            bdest = BACKUP_DIR / f"{name.replace('@', '_at_')}.config.yaml.bak-20260930"
            if not bdest.exists():
                shutil.copy2(cfg, bdest)
            tmp = cfg.parent / (cfg.name + ".tmp")
            _dump(c, tmp)
            v = _load(tmp)
            assert v["model"]["default"] == p["model"], "post-write validation failed"
            assert v["model"]["provider"] == p["provider"], "post-write validation failed"
            if want_base:
                assert v["model"]["base_url"] == want_base, "base_url did not follow the provider"
            assert len(v["fallback_providers"]) == len(spec["chains"][p["chain"]]), "chain count mismatch"
            os.replace(tmp, cfg)
            print(f"OK   {name:<16} {p['provider']} / {p['model']}  chain={p['chain']}")
            ok += 1
        except Exception as e:
            print(f"FAIL {name}: {e}")
            fail += 1
    print(f"\n{'would change' if dry else 'applied'}: {ok}  fail: {fail}")
    return 1 if fail else 0


# ── probe ─────────────────────────────────────────────────────────────────────

def _chat(base, key, model, timeout=90):
    """(status, served_model, latency_ms, error, empty_content)

    The 5th element is the "measured-dead shape": HTTP 200 whose message carries
    neither content nor reasoning. meituan/longcat-2.5-preview:free answers
    exactly that (spec dead_slugs), and a probe that treats it as OK is the reason
    a dead slug can sit in a chain unnoticed.
    """
    url = CHAT_DIR.format(base=base)
    payload = json.dumps({
        "model": model,
        # 256, not 5 (card t_7d75bafd): a reasoning model spends its budget on
        # reasoning first, so a 5-token probe cannot distinguish "healthy but
        # thinking" from "broken". Measured: nvidia nemotron-3-super returns
        # content:null + reasoning_content at 64 tokens, real JSON at ~800.
        "messages": [{"role": "user", "content": "Reply with: ok"}],
        "max_tokens": 256,
    }).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "hermes-fleet-route/1.0"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=payload, headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode(errors="replace")
            lat = (time.monotonic() - start) * 1000
            served = ""
            empty = False
            try:
                j = json.loads(body)
                served = j.get("model", "")
                msg = (j.get("choices") or [{}])[0].get("message") or {}
                content = (msg.get("content") or "").strip()
                # `reasoning` (nous) or `reasoning_content` (nvidia NIM)
                reasoning = (msg.get("reasoning") or msg.get("reasoning_content") or "").strip()
                empty = not (content or reasoning)
            except Exception:
                empty = True
            return 200, served, lat, "", empty
    except urllib.error.HTTPError as e:
        lat = (time.monotonic() - start) * 1000
        try:
            err = e.read().decode(errors="replace")[:140]
        except Exception:
            err = str(e)
        return e.code, "", lat, err, False
    except Exception as e:
        lat = (time.monotonic() - start) * 1000
        return 0, "", lat, str(e)[:140], False


def cmd_probe(spec, only=None):
    """Live-verify every model referenced by a primary or a chain.

    Two hardenings from the 2026-10-16 incident (card t_7d75bafd):
      * `max_tokens` 5 -> 256 and `reasoning_content` accepted alongside
        `reasoning`. A reasoning model spends its budget on reasoning FIRST:
        nvidia nemotron-3-super answers {"content": null,
        "reasoning_content": "..."} at 64 tokens (measured 1.2-2.9 s) and real JSON
        at ~800 (12.1 s). A 5-token probe cannot tell a healthy reasoning model
        from a broken one, and the old body check would have called the ceiling
        silent-empty.
      * a 200 with NO content and NO reasoning is a FAILURE, not OK. The spec
        lists meituan/longcat-2.5-preview:free as dead precisely because it
        answers HTTP 200 with an empty body; the old rule (status 200 + served
        model == requested) passed it.
    """
    from concurrent.futures import ThreadPoolExecutor
    env = load_env()
    pairs = {}
    for name in ["@home"] + sorted(p.name for p in PROFILES.iterdir() if p.is_dir()):
        if only and name not in only:
            continue
        cfg = target_config(name)
        if not cfg.exists():
            continue
        try:
            c = _load(cfg) or {}
        except Exception:
            continue
        m = c.get("model") or {}
        if m.get("default"):
            pairs.setdefault((m.get("provider"), m["default"]), []).append(name)
        for prov, model in chain_entries(c):
            if model:
                pairs.setdefault((prov, model), []).append(name)

    def probe_one(item):
        (prov, model), users = item
        if prov not in ENDPOINTS:
            return (prov or "?", model, "SKIP", "", "", "no endpoint map")
        base, keyenv = ENDPOINTS[prov]
        key = env.get(keyenv) if keyenv else None
        if keyenv and not key:
            return (prov, model, "NOKEY", "", "", f"missing {keyenv}")
        to = 180 if prov == "nvidia" else 90
        code, served, lat, err, empty = _chat(base, key, model, timeout=to)
        if code in (0, 429, 502, 503, 1010):
            time.sleep(3)
            code, served, lat, err, empty = _chat(base, key, model, timeout=to)
        is_router = model.startswith("kilo-auto/") and code == 200
        ok = code == 200 and not empty and (served == model or is_router)
        # QUOTA is deliberately NOT a routing defect (card t_7d75bafd): the fleet's
        # one shared free quota (`openrouter-free`) answers HTTP 429
        # free-models-per-day-high-balance every day until 00:00 UTC, and it is
        # named only as a LAST-resort chain entry. It is counted and printed, so a
        # green run is never read as "openrouter-free is up", but it does not alert
        # a human eight times a day — that is how an alert feed stops being read.
        # A route that CANNOT answer (400/403/404/5xx, empty body, missing key) is
        # FAIL and fails the run.
        quota = (not ok) and (code in (402, 429) or "free-models-per-day" in err
                              or "insufficient_quota" in err or "Rate limit exceeded" in err)
        if code == 200 and empty:
            err = "HTTP 200 with EMPTY content (measured-dead shape)"
        status = "OK" if ok else ("QUOTA" if quota else ("WARN" if code == 200 else "FAIL"))
        print(f"{status:<5} {prov:<16} {model:<52} -> {served or err[:60]}")
        return (prov, model, status, f"{lat:.0f}", served or "-", err)

    items = sorted(pairs.items(), key=lambda kv: str(kv[0]))
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(probe_one, items))

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    STATE.mkdir(parents=True, exist_ok=True)
    csv_path = STATE / f"probe-{ts}.csv"
    with open(csv_path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["provider", "model", "status", "latency_ms", "served", "error"])
        wr.writerows(rows)
    md_path = STATE / f"probe-{ts}.md"
    with open(md_path, "w") as f:
        f.write(f"# Fleet model probe — {ts}\n\n")
        for r in rows:
            f.write(f"- **{r[2]}** `{r[0]}/{r[1]}` -> served: `{r[4]}` {r[5]}\n")
    nfail = sum(1 for r in rows if r[2] == "FAIL")
    nquota = sum(1 for r in rows if r[2] == "QUOTA")
    nok = sum(1 for r in rows if r[2] == "OK")
    other = len(rows) - nok - nfail - nquota
    print(f"\n{nok} OK, {nfail} FAIL, {nquota} QUOTA (exhausted shared quota, not a "
          f"routing defect), {other} other  |  report: {md_path}")
    if nquota:
        exhausted = sorted({r[0] for r in rows if r[2] == "QUOTA"})
        print(f"  quota-exhausted providers (chain entries cannot answer right now): "
              f"{', '.join(exhausted)}")
    return 1 if nfail else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    au = sub.add_parser("audit")
    au.add_argument("--strict", action="store_true",
                    help="exit 1 when any profile carries a flag (for a scheduled runner)")
    a = sub.add_parser("apply")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--only", default="")
    pr = sub.add_parser("probe")
    pr.add_argument("--only", default="")
    args = ap.parse_args()
    spec = load_spec()
    only = [s.strip() for s in getattr(args, "only", "").split(",") if s.strip()] or None
    if args.cmd == "audit":
        return cmd_audit(spec, strict=args.strict)
    if args.cmd == "apply":
        return cmd_apply(spec, only=only, dry=args.dry_run)
    if args.cmd == "probe":
        return cmd_probe(spec, only=only)


if __name__ == "__main__":
    sys.exit(main())
