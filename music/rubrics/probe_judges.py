"""probe_judges.py — raw one-token probe of each panel judge endpoint.
Prints status, served model, and a truncated body. Never prints keys."""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from panel import resolve_judge

for name in ("reviewer-deepseek", "reviewer-longcat",
             "reviewer-minimax", "reviewer-nemotron"):
    try:
        j = resolve_judge(name)
    except Exception as e:
        print(f"{name}: RESOLVE FAIL {e}")
        continue
    body = json.dumps({
        "model": j["model"],
        "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
        "max_tokens": 200,
    }).encode()
    req = urllib.request.Request(
        j["base_url"] + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {j['key']}",
                 "Content-Type": "application/json",
                 "User-Agent": "hermes-music-panel/1.0"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode())
        ch = (data.get("choices") or [{}])[0]
        msg = ch.get("message", {})
        print(f"{name} ({j['model']}): OK served={data.get('model')!r} "
              f"content={msg.get('content')!r} "
              f"reasoning_len={len(msg.get('reasoning_content') or '')} "
              f"finish={ch.get('finish_reason')!r}")
    except urllib.error.HTTPError as e:
        print(f"{name} ({j['model']}): HTTP {e.code} "
              f"{e.read().decode()[:200]}")
    except Exception as e:
        print(f"{name} ({j['model']}): {type(e).__name__} {e}")
