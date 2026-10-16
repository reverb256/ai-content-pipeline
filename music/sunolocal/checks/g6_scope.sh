#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path

root = Path("music/sunolocal")
readme = (root / "README.md").read_text(encoding="utf-8")
assert "## Scope" in readme and "## Deferred" in readme, "README missing scope/deferred sections"

banned = ("TODO", "FIXME", "XXX:")
mods = sorted(root.glob("*.py")) + sorted((root / "adapters").glob("*.py"))
assert mods, "no modules found"
for f in mods:
    text = f.read_text(encoding="utf-8")
    hits = [b for b in banned if b in text]
    assert not hits, (f.name, hits)

studio = (root / "studio.py").read_text(encoding="utf-8")
for ep in ("/api/v1/lyrics", "/api/v1/stems", "/api/v1/extend", "/api/v1/cover"):
    assert ep in studio, f"deferred endpoint missing: {ep}"
assert "501" in studio, "no explicit 501 for deferred endpoints"
assert "not_implemented" in studio, "deferred endpoints missing not_implemented marker"

print("G6-OK")
PY
