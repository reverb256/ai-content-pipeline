#!/usr/bin/env python3
"""fleet-default-model.py — set the fleet default model in every Hermes profile on this host.

Directive (j_kro, 2026-10-16): default = deepseek-v4.1-flash @ opencode-go, fleet-wide.
Sets model.default / model.provider / model.base_url / model.api_mode in the root config and
every profiles/*/config.yaml. Text-surgical: only those keys are touched; all other lines,
comments, and key order are preserved. Backups to ~/.hermes/backups/fleet-default-model/<ts>/,
post-edit YAML validation (pyyaml; lightweight check if unavailable).

Usage (invoke through the terminal tool):
  python3 ~/.hermes/scripts/fleet-default-model.py --dry-run
  python3 ~/.hermes/scripts/fleet-default-model.py
  python3 ~/.hermes/scripts/fleet-default-model.py --create-missing --only monitoring
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

TARGET = {
    "default": "deepseek-v4.1-flash",
    "provider": "opencode-go",
    "base_url": "https://opencode.ai/zen/go/v1",
    "api_mode": "chat_completions",
}

HOME = Path.home()
HERMES = Path(__import__("os").environ.get("HERMES_HOME", HOME / ".hermes"))
BACKUP = HERMES / "backups" / "fleet-default-model"


def validate(text):
    try:
        import yaml
    except ImportError:
        good = ("opencode-go" in text) and ("deepseek-v4.1-flash" in text)
        return good, (None if good else "yaml module missing; lightweight check failed")
    try:
        d = yaml.safe_load(text) or {}
        m = d.get("model") or {}
        ok = m.get("default") == TARGET["default"] and m.get("provider") == TARGET["provider"]
        return ok, None if ok else "model.default/provider mismatch after edit"
    except Exception as e:  # noqa: BLE001
        return False, f"yaml parse error: {e}"


def block_lines():
    return [f"  {k}: {v}" for k, v in TARGET.items()]


def edit(text, create_missing):
    lines = text.split("\n")
    idx = None
    for i, l in enumerate(lines):
        if l.rstrip() == "model:":
            idx = i
            break
    if idx is None:
        if not create_missing:
            return None, "no-model-block"
        new = ["model:", *block_lines(), ""] + lines
        return "\n".join(new), "inserted"
    j = idx + 1
    block = []
    while j < len(lines) and lines[j].strip() and lines[j].startswith((" ", "\t")):
        block.append(j)
        j += 1
    if not block:
        new = lines[: idx + 1] + block_lines() + lines[idx + 1 :]
        return "\n".join(new), "inserted"
    first = lines[block[0]]
    indent = first[: len(first) - len(first.lstrip())]
    seen = set()
    for i in block:
        s = lines[i].strip()
        if ":" in s:
            k = s.split(":", 1)[0].strip()
            if k in TARGET:
                lines[i] = f"{indent}{k}: {TARGET[k]}"
                seen.add(k)
    add = [f"{indent}{k}: {TARGET[k]}" for k, v in TARGET.items() if k not in seen]
    if add:
        lines[block[-1] + 1 : block[-1] + 1] = add
    return "\n".join(lines), "updated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--create-missing", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    only = set(x for x in args.only.split(",") if x)

    targets = [("@home", HERMES / "config.yaml")]
    pdir = HERMES / "profiles"
    if pdir.is_dir():
        for d in sorted(pdir.iterdir()):
            f = d / "config.yaml"
            if d.is_dir() and f.exists():
                targets.append((d.name, f))

    results = []
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    for name, cfg in targets:
        if only and name not in only:
            continue
        try:
            orig = cfg.read_text()
        except Exception as e:  # noqa: BLE001
            results.append((name, "READ-FAIL", str(e)))
            continue
        new, status = edit(orig, args.create_missing)
        if new is None:
            results.append((name, "SKIP", status))
            continue
        if new == orig:
            results.append((name, "OK", ""))
            continue
        ok, err = validate(new)
        if not ok:
            results.append((name, "VALIDATE-FAIL", err or ""))
            continue
        if args.dry_run:
            results.append((name, "WOULD-CHANGE", status))
            continue
        bd = BACKUP / ts / name.replace("@", "_at_")
        bd.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cfg, bd / "config.yaml.bak")
        cfg.write_text(new)
        ok2, err2 = validate(cfg.read_text())
        results.append((name, "CHANGED" if ok2 else "POST-VALIDATE-FAIL", err2 or ""))

    if args.json:
        import json
        print(json.dumps([{"name": n, "status": s, "note": e} for n, s, e in results], indent=1))
    else:
        for n, s, e in results:
            print(f"{s:<20} {n} {e}")
        from collections import Counter
        c = Counter(s for _, s, _ in results)
        print("---")
        print(" ".join(f"{k}={v}" for k, v in sorted(c.items())))
    fails = [r for r in results if "FAIL" in r[1]]
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
