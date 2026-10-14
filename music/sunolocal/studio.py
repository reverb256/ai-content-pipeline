"""
sunolocal studio service — a Suno-shaped API over our local engines (v0.1).

Endpoints generate/task/audio/models/health are implemented. The lyrics,
stems, extend and cover endpoints are explicitly deferred and answer 501
with a structured not_implemented marker; they are implemented in v0.2.

The service never renders on the request path: it queues a job, renders in
a background worker, and stores results in the SQLite job store.
"""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict

from .adapters.ace_comfy import render_acestep
from .adapters.fixture import render_fixture
from .adapters.yue2_http import render_yue2
from .spec import SunoGenerateRequest
from .store import create_job, get_job, init_db, update_job_status
from .translate import suno_to_aceplan, suno_to_yue2


def _default_engine() -> str:
    return (os.environ.get("SUNOLOCAL_ENGINE", "ace").strip().lower() or "ace")


def _artifacts_dir() -> Path:
    default = Path.home() / ".local" / "share" / "sunolocal" / "artifacts"
    path = Path(os.environ.get("SUNOLOCAL_ARTIFACTS", str(default)))
    path.mkdir(parents=True, exist_ok=True)
    return path


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="sunolocal", version="0.1.0", lifespan=_lifespan)


class GenerateBody(BaseModel):
    """Suno-shaped body (camelCase, as the public API uses) plus an `engine` extension."""

    model_config = ConfigDict(protected_namespaces=())

    prompt: Optional[str] = None
    style: Optional[str] = None
    lyrics: Optional[str] = None
    title: Optional[str] = None
    instrumental: bool = False
    model: Optional[str] = None
    customMode: bool = False
    negativeTags: Optional[str] = None
    vocalGender: Optional[Literal["m", "f"]] = None
    duration: Optional[int] = None
    styleWeight: Optional[float] = None
    weirdnessConstraint: Optional[float] = None
    audioWeight: Optional[float] = None
    variety: Optional[int] = None
    callBackUrl: Optional[str] = None
    seed: Optional[int] = None
    engine: Optional[str] = None


def _to_internal(body: GenerateBody) -> SunoGenerateRequest:
    return SunoGenerateRequest(
        prompt=body.prompt,
        style=body.style,
        lyrics=body.lyrics,
        title=body.title,
        instrumental=body.instrumental,
        model=body.model or "v6",
        custom_mode=body.customMode,
        negative_tags=body.negativeTags,
        vocal_gender=("male" if body.vocalGender == "m" else "female" if body.vocalGender == "f" else None),
        duration=body.duration,
        style_weight=body.styleWeight,
        weirdness_constraint=body.weirdnessConstraint,
        audio_weight=body.audioWeight,
        variety=body.variety,
        callback_url=body.callBackUrl,
        seed=body.seed,
        engine=body.engine,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/models")
def models() -> dict:
    return {
        "engines": {
            "ace": {"kind": "ACE-Step 1.5", "via": "acestep_plan.py -> comfyui-zephyr window"},
            "yue2": {"kind": "YuE2-3B", "via": "yue2-zephyr http"},
        },
        "default": _default_engine(),
    }


@app.post("/api/v1/generate")
def generate(body: GenerateBody, background_tasks: BackgroundTasks) -> dict:
    request = _to_internal(body)
    job_id = create_job(request)
    background_tasks.add_task(_run_job, job_id, request)
    return {"task_id": job_id, "status": "pending"}


@app.get("/api/v1/task/{task_id}")
def task(task_id: str) -> dict:
    job = get_job(task_id)
    if job is None:
        raise HTTPException(status_code=404, detail="task not found")
    payload: dict = {"task_id": task_id, "status": job["status"]}
    if job.get("result"):
        try:
            payload.update(json.loads(job["result"]))
        except (TypeError, json.JSONDecodeError):
            payload["raw"] = job["result"]
    return payload


@app.get("/api/v1/audio")
def audio(path: str) -> Response:
    artifact = Path(path).resolve()
    root = _artifacts_dir().resolve()
    if not artifact.is_file() or not artifact.is_relative_to(root):
        raise HTTPException(status_code=404, detail="artifact not found")
    media = {"wav": "audio/wav", "flac": "audio/flac", "mp3": "audio/mpeg"}.get(
        artifact.suffix.lstrip("."), "application/octet-stream"
    )
    return Response(content=artifact.read_bytes(), media_type=media)


def _deferred(endpoint: str) -> None:
    raise HTTPException(
        status_code=501,
        detail={"status": "not_implemented", "endpoint": endpoint, "note": "deferred to v0.2; see README scope"},
    )


@app.post("/api/v1/lyrics")
def lyrics() -> None:
    _deferred("/api/v1/lyrics")


@app.post("/api/v1/stems")
def stems() -> None:
    _deferred("/api/v1/stems")


@app.post("/api/v1/extend")
def extend() -> None:
    _deferred("/api/v1/extend")


@app.post("/api/v1/cover")
def cover() -> None:
    _deferred("/api/v1/cover")


def _run_job(job_id: str, request: SunoGenerateRequest) -> None:
    """Render one job. Runs in a worker thread after the HTTP response is sent."""
    try:
        update_job_status(job_id, "processing")
        engine = (request.engine or _default_engine()).strip().lower()
        stem = f"suno-{job_id}"
        if engine == "fixture":
            audio_bytes, mime, meta = render_fixture(request.duration)
            ext = "wav"
        elif engine == "yue2":
            kwargs = suno_to_yue2(request)
            kwargs["id"] = stem
            audio_bytes, mime, meta = render_yue2(kwargs)
            ext = "flac"
        elif engine == "ace":
            audio_bytes, mime, meta = render_acestep(suno_to_aceplan(request), seed=request.seed)
            ext = "wav"
        else:
            raise ValueError(f"unknown engine: {engine!r} (expected ace, yue2, or fixture)")
        audio_path = _artifacts_dir() / f"{stem}.{ext}"
        audio_path.write_bytes(audio_bytes)
        update_job_status(
            job_id,
            "completed",
            {
                "engine": engine,
                "mime": mime,
                "audio_url": f"/api/v1/audio?path={audio_path}",
                "bytes": len(audio_bytes),
                "manifest": meta,
            },
        )
    except Exception as exc:
        update_job_status(job_id, "failed", {"error": f"{type(exc).__name__}: {exc}"})
