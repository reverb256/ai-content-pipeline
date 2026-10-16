# sunolocal

Local, Suno-shaped tooling for our own music models. One small service that accepts
Suno-style generation requests and renders them on our GPUs with ACE-Step 1.5 (through
the existing ComfyUI window) or YuE2-3B (through the `yue2-zephyr` service).

Status: **v0.1**. Acceptance gates live in `GATES.md`; run them with the unlazy checker
before trusting anything.

## Scope (v0.1)

| Endpoint | Behavior |
|---|---|
| `POST /api/v1/generate` | Accepts a Suno-shaped body (`customMode`, `style`, `lyrics`, `prompt`, `title`, `instrumental`, `duration`, `negativeTags`, `vocalGender` `m`/`f`, `styleWeight`, `weirdnessConstraint`, `audioWeight`, `variety`, `model`, `seed`, `callBackUrl`) plus a `engine` extension field. Queues a job and renders in the background. |
| `GET /api/v1/task/{id}` | Job status and result (`audio_url`, `manifest`, `engine`). |
| `GET /api/v1/audio?path=` | Serves a rendered artifact. Path-guarded to the artifacts dir. |
| `GET /api/v1/models` | Lists available engines. |
| `GET /health` | Readiness. |
| `POST /api/v1/lyrics` | `501 not_implemented` — deferred to v0.2. |
| `POST /api/v1/stems` | `501 not_implemented` — deferred to v0.2. |
| `POST /api/v1/extend` | `501 not_implemented` — deferred to v0.2. |
| `POST /api/v1/cover` | `501 not_implemented` — deferred to v0.2. |

Engines: `ace` (default; subprocess to `acestep_plan.py` → ComfyUI window → `~/Music/acestep/`),
`yue2` (HTTP to `yue2-zephyr`), `fixture` (test double used by the checks only — emits a
short silent WAV; it exists so plumbing can be tested without a GPU).

## Deferred (v0.2+)

- Live-engine end-to-end verification on the real GPU windows (a real ACE render and a
  real YuE2 call). Requires window/GPU coordination; not part of the v0.1 ledger.
- Real lyrics/stems/extend/cover implementations.
- CLI and MCP surfaces (not shipped in v0.1; no stubs left behind).
- Helm chart + ArgoCD deployment, and wiring into the `music-pipeline` render step.
- `research/` holds unverified capture experiments; not part of v0.1.

## Layout

    music/sunolocal/
      spec.py            # internal request/response models
      store.py           # SQLite job store
      translate.py       # Suno fields -> ACE plan / YuE2 kwargs
      studio.py          # FastAPI app (the service)
      adapters/          # ace_comfy.py, yue2_http.py, fixture.py
      checks/            # gate runners (see GATES.md)
      research/          # quarantined, unverified experiments

## Env vars

| Var | Default | Use |
|---|---|---|
| `SUNOLOCAL_DB` | `~/.local/share/sunolocal/jobs.sqlite3` | job store |
| `SUNOLOCAL_ARTIFACTS` | `~/.local/share/sunolocal/artifacts` | audio output dir |
| `SUNOLOCAL_ENGINE` | `ace` | default engine |
| `SUNOLOCAL_ACESTEP_SCRIPT` | mining-k8s `acestep_plan.py` | ACE renderer script |
| `SUNOLOCAL_ACESTEP_OUTPUT` | `~/Music/acestep` | where the ACE renderer writes |
| `SUNOLOCAL_COMFY_URL` | `http://localhost:32188` | ComfyUI (zephyr NodePort) |
| `YUE2_BASE_URL` | `http://yue2-zephyr.mining.svc.cluster.local` | YuE2 service |

## Run

    python3 -m uvicorn music.sunolocal.studio:app --host 127.0.0.1 --port 8123

Example request:

    curl -s localhost:8123/api/v1/generate -H 'content-type: application/json' \
      -d '{"customMode": true, "style": "synthwave", "lyrics": "[Chorus]\nshine", "duration": 30, "engine": "ace"}'

## Checks

    node ~/.hermes/skills/unlazy/scripts/gate-check.cjs --status   music/sunolocal/GATES.md
    node ~/.hermes/skills/unlazy/scripts/gate-check.cjs --approve  music/sunolocal/GATES.md
    node ~/.hermes/skills/unlazy/scripts/gate-check.cjs --reverify music/sunolocal/GATES.md
