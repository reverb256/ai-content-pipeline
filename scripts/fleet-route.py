#!/usr/bin/env python3
"""fleet-route.py — spec-driven model routing for every Hermes profile on this host.

Subcommands
  audit                 Scan every profile: primary, fallback chain, problem flags.
  apply [--dry-run]     Apply fleet-routing.json to profiles (backup + validate).
  probe [--only a,b]    Live-verify every model referenced in primaries + chains
                        with a 1-token raw API call. Writes a report, exits non-zero
                        on failures (cron-friendly).

Spec: fleet-routing.json next to this script (keep the two together).
Canonical location: ai-content-pipeline/scripts/ (deployed copy: ~/.hermes/scripts/).
Created 2026-09-30 for the low-cost fleet routing sweep (j_kro).
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
    "nous": ("https://inference-api.nousresearch.com/v1", "NOUS_API_KEY"),
    "openrouter-free": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "commandcode": ("https://api.commandcode.ai/provider/v1", "COMMANDCODE_API_KEY"),
    "kilo": ("https://api.kilo.ai/api/gateway", "KILOCODE_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY"),
    "pair": ("http://127.0.0.1:1235/v1", None),
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

def cmd_audit(spec):
    dead = set(spec.get("dead_slugs", []))
    rows = []
    for name in ["@home"] + sorted(p.name for p in PROFILES.iterdir() if p.is_dir()):
        cfg = target_config(name)
        if not cfg.exists():
            continue
        try:
            c = _load(cfg) or {}
        except Exception as e:
            rows.append((name, f"YAML-ERROR {e}", ""))
            continue
        m = c.get("model") or {}
        md, mp = m.get("default"), m.get("provider")
        flags = []
        if mp == "opencode-go":
            flags.append("GO-EXHAUSTED")
        if md in dead:
            flags.append("DEAD-SLUG")
        fb = chain_entries(c)
        for prov, model in fb:
            if model in dead:
                flags.append("DEAD-IN-CHAIN")
            if prov == "opencode-zen":
                flags.append("ZEN-BLOCKED")
            if prov == "opencode-go":
                flags.append("GO-IN-CHAIN")
        rows.append((name, f"{mp} / {md}", f"{len(fb)} fb" + (("  ⚠ " + ",".join(sorted(set(flags)))) if flags else "")))
    w = max(len(r[0]) for r in rows) + 2
    print(f"{'PROFILE':<{w}}| PRIMARY                                     | NOTES")
    print("-" * (w + 78))
    for r in rows:
        print(f"{r[0]:<{w}}| {r[1][:43]:<43} | {r[2]}")
    print(f"\nscanned {len(rows)} targets")


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

def _chat(base, key, model, timeout=45):
    url = CHAT_DIR.format(base=base)
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with: ok"}],
        "max_tokens": 5,
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
            try:
                served = json.loads(body).get("model", "")
            except Exception:
                pass
            return 200, served, lat, ""
    except urllib.error.HTTPError as e:
        lat = (time.monotonic() - start) * 1000
        try:
            err = e.read().decode(errors="replace")[:140]
        except Exception:
            err = str(e)
        return e.code, "", lat, err
    except Exception as e:
        lat = (time.monotonic() - start) * 1000
        return 0, "", lat, str(e)[:140]


def cmd_probe(spec, only=None):
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
        to = 120 if prov == "nvidia" else 60
        code, served, lat, err = _chat(base, key, model, timeout=to)
        if code in (0, 429, 502, 503, 1010):
            time.sleep(3)
            code, served, lat, err = _chat(base, key, model, timeout=to)
        is_router = model.startswith("kilo-auto/") and code == 200
        ok = code == 200 and (served == model or is_router)
        status = "OK" if ok else ("WARN" if code == 200 else "FAIL")
        print(f"{status:<4} {prov:<16} {model:<52} -> {served or err[:60]}")
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
    nok = sum(1 for r in rows if r[2] == "OK")
    print(f"\n{nok} OK, {nfail} FAIL, {len(rows)-nok-nfail} other  |  report: {md_path}")
    return 1 if nfail else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("audit")
    a = sub.add_parser("apply")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--only", default="")
    pr = sub.add_parser("probe")
    pr.add_argument("--only", default="")
    args = ap.parse_args()
    spec = load_spec()
    only = [s.strip() for s in getattr(args, "only", "").split(",") if s.strip()] or None
    if args.cmd == "audit":
        return cmd_audit(spec)
    if args.cmd == "apply":
        return cmd_apply(spec, only=only, dry=args.dry_run)
    if args.cmd == "probe":
        return cmd_probe(spec, only=only)


if __name__ == "__main__":
    sys.exit(main())
