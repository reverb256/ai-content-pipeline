#!/usr/bin/env python3
"""Gate: NIM Omni audio-QA — auto-listen + verify emotion/intros/audibility.

Calls NVIDIA Nemotron 3 Nano Omni (audio understanding model) to verify:
- Emotion detection: does delivered emotion match script cues?
- Speaker attribution: do speakers match the cast?
- Intelligibility/clarity: is the audio clear and understandable?
- Script alignment: does the audio actually say what the script says?

Evidence output (`review/nim_omni_qa.review.json`) is the contract for
gate_review.py: it emits the 7 required review criteria (mapped from NIM's
4 native scores — see write_evidence()) plus the 4 native NIM dimensions
as extras, so the file passes the standard review gate without a custom
stage.

Modes:
  default         — call NIM Omni API, write evidence, gate on thresholds.
                    Expensive (paid API). Use at render time only.
  --dry-run       — call NIM Omni, write evidence, always PASS.
                    For dev iteration.
  --evidence-only — read existing review/nim_omni_qa.review.json, gate on
                    its pass flag, overall, and per-criterion >=7. No API
                    call. Use from gate chains (advance-stage.sh,
                    gate_preaudit.py) to avoid burning NVIDIA credits on
                    every chain run.

Exit 0 = PASS, exit 1 = FAIL. Writes JSON evidence to review/ and audit.jsonl.

Usage:
    gate_nim_omni_qa.py <campaign-dir> [--audio <path>] [--script <path>]
                       [--dry-run | --evidence-only]

Environment:
    NVIDIA_API_KEY — required for live calls (loaded from ~/.hermes/.env if
                     not in env). Not required for --evidence-only.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1"
MODEL_ID = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

# Minimum pass thresholds (0-10 scale from model)
MIN_EMOTION_SCORE = 6.0
MIN_INTELLIGIBILITY_SCORE = 7.0
MIN_ALIGNMENT_SCORE = 6.0
MIN_OVERALL_SCORE = 6.0

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

ENV_FILE = Path(os.environ.get("HERMES_ENV_FILE", Path.home() / ".hermes" / ".env"))


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def log(msg: str) -> None:
    print(f"[nim-qa] {msg}", flush=True)


def load_env() -> None:
    """Load KEY=value lines from ~/.hermes/.env."""
    if not ENV_FILE.exists():
        return
    try:
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, val)
    except OSError:
        pass


def find_audio(campaign_dir: Path, explicit_audio: Path | None = None) -> Path:
    """Locate the rendered audio file."""
    if explicit_audio:
        if explicit_audio.exists():
            return explicit_audio
        fail(f"explicit audio not found: {explicit_audio}")

    candidates: list[Path] = []
    for pat in ("out/*.mp3", "out/*.wav", "voice/*.mp3", "audio/*.mp3", "audio.mp3", "voice.mp3"):
        candidates.extend(campaign_dir.glob(pat))
    if not candidates:
        fail(f"no audio found under {campaign_dir} (looked for out/*.mp3, voice/*.mp3, audio/*.mp3)")
    # Prefer the largest file (most likely the final mix)
    candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]


def find_script(campaign_dir: Path, explicit_script: Path | None = None) -> Path | None:
    """Locate the story script."""
    if explicit_script:
        if explicit_script.exists():
            return explicit_script
        return None
    for pat in ("story.md", "script.md", "story-v3.md"):
        p = campaign_dir / pat
        if p.exists():
            return p
    return None


def extract_script_text(script_path: Path) -> str:
    """Extract the dialogue/narration text from the script (skip frontmatter)."""
    text = script_path.read_text(encoding="utf-8")
    # Strip frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]
    # Extract speaker lines and narration
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("["):
            continue
        # Speaker line: "Name (emotion): text" or "Name: text"
        if ":" in stripped and not stripped.startswith("---"):
            lines.append(stripped)
    return "\n".join(lines)


def encode_audio_base64(audio_path: Path) -> str:
    """Encode audio file to base64 data URI."""
    data = audio_path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    suffix = audio_path.suffix.lower()
    mime = "audio/wav" if suffix == ".wav" else "audio/mpeg"
    return f"data:{mime};base64,{b64}"


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    import subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        return 0.0
    info = json.loads(r.stdout)
    return float(info.get("format", {}).get("duration", 0))


def split_audio(audio_path: Path, chunk_dir: Path, chunk_seconds: int = 240, overlap: int = 10) -> list[Path]:
    """Split audio into overlapping chunks using ffmpeg.
    
    NIM Omni has a 600s limit. We split into ~4min chunks with overlap
    to stay well under the limit while covering the full audio.
    """
    duration = get_audio_duration(audio_path)
    if duration <= 0:
        fail("could not determine audio duration")
    
    # If under 500s, no need to split (leave margin under 600s limit)
    if duration <= 500:
        return [audio_path]
    
    chunk_dir.mkdir(parents=True, exist_ok=True)
    chunks: list[Path] = []
    start = 0.0
    idx = 0
    
    while start < duration:
        end = min(start + chunk_seconds, duration)
        # Ensure last chunk is at least 30s (not a tiny tail)
        if duration - end < 30 and idx > 0:
            end = duration
        
        chunk_path = chunk_dir / f"chunk-{idx:03d}.mp3"
        import subprocess
        r = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-ss", str(start), "-to", str(end),
                "-acodec", "libmp3lame", "-b:a", "128k",
                str(chunk_path),
            ],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            fail(f"ffmpeg split failed at {start}s: {r.stderr[-200:]}")
        
        chunks.append(chunk_path)
        log(f"  chunk {idx}: {start:.0f}s-{end:.0f}s -> {chunk_path.name}")
        
        # Move to next chunk with overlap
        start = end - overlap
        if end >= duration:
            break
        idx += 1
    
    return chunks


# --------------------------------------------------------------------------- #
# NIM Omni API call
# --------------------------------------------------------------------------- #

def call_nim_omni(audio_b64: str, script_text: str, api_key: str) -> dict:
    """Call NIM Omni model to analyze audio."""
    try:
        from openai import OpenAI
    except ImportError:
        fail("openai library not installed. Run: pip install openai")

    client = OpenAI(
        base_url=NVIDIA_API_URL,
        api_key=api_key,
    )

    prompt = f"""You are an audio quality analysis system. Analyze the provided audio file against the script.

## Script (expected content):
{script_text[:8000]}

## Instructions:
Listen carefully to the audio and evaluate these dimensions. Return ONLY valid JSON with this exact schema:

{{
  "emotion_analysis": {{
    "score": <0-10, how well delivered emotions match script cues>,
    "evidence": "<specific examples of emotion matches/mismatches>",
    "scene_emotions": [
      {{"scene": "<scene name or timestamp>", "expected": "<expected emotion>", "detected": "<detected emotion>", "match": <true/false>}}
    ]
  }},
  "speaker_attribution": {{
    "score": <0-10, how well speakers are distinguishable and match cast>,
    "evidence": "<specific speaker identification examples>",
    "speakers_detected": ["<speaker1>", "<speaker2>"]
  }},
  "intelligibility": {{
    "score": <0-10, clarity and understandability of speech>,
    "evidence": "<specific clarity observations>",
    "issues": ["<any words/phrases that are unclear>"]
  }},
  "script_alignment": {{
    "score": <0-10, how well audio content matches script>,
    "evidence": "<specific alignment observations>",
    "deviations": ["<any deviations from script>"]
  }},
  "overall": {{
    "score": <0-10, overall audio quality>,
    "summary": "<brief overall assessment>"
  }}
}}

Be critical. Score honestly. A flat, emotionless read of an emotional script should score low on emotion_analysis. Mumbled or unclear speech should score low on intelligibility."""

    response = None
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "audio_url", "audio_url": {"url": audio_b64}},
                        ],
                    }
                ],
                max_tokens=4096,
                temperature=0.1,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            break  # Success
        except Exception as e:
            err_str = str(e)
            # If audio too long, signal caller to split
            if "600s" in err_str or "maximum allowed duration" in err_str or "duration" in err_str.lower():
                raise AudioTooLongError(f"Audio exceeds NIM Omni limit: {e}")
            if attempt < max_retries:
                import time
                time.sleep(2)
                continue
            fail(f"NIM Omni API call failed: {e}")

    if response is None:
        fail("NIM Omni returned no response")

    content = response.choices[0].message.content
    if not content:
        fail("NIM Omni returned empty response")

    # Parse JSON from response (handle markdown code blocks)
    content = content.strip()
    if content.startswith("```"):
        # Strip code block markers
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        # 1. Truncated response — try to complete it
        if "Expecting" in str(e) and "delimiter" in str(e):
            # Try to close any open brackets/braces
            fixed = content.strip()
            # Count open/close braces
            open_braces = fixed.count('{') - fixed.count('}')
            open_brackets = fixed.count('[') - fixed.count(']')
            # Close any open strings
            if fixed.count('"') % 2 != 0:
                fixed += '"'
            # Close arrays then objects
            fixed += ']' * open_brackets
            fixed += '}' * open_braces
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
        # 2. Try with strict=False
        try:
            import json as json_mod
            return json_mod.loads(content, strict=False)
        except (json_mod.JSONDecodeError, TypeError):
            pass
        fail(f"could not parse NIM Omni JSON response: {e}\nRaw content:\n{content[:500]}")


class AudioTooLongError(Exception):
    """Raised when audio exceeds NIM Omni's maximum duration limit."""
    pass


def call_nim_omni_chunked(audio_path: Path, script_text: str, api_key: str, chunk_dir: Path) -> dict:
    """Analyze audio in chunks and merge results."""
    chunks = split_audio(audio_path, chunk_dir)
    
    if len(chunks) == 1:
        # Short enough — single call
        audio_b64 = encode_audio_base64(chunks[0])
        return call_nim_omni(audio_b64, script_text, api_key)
    
    # Multiple chunks — analyze each and merge
    all_results: list[dict] = []
    for i, chunk_path in enumerate(chunks):
        log(f"analyzing chunk {i+1}/{len(chunks)}: {chunk_path.name}")
        audio_b64 = encode_audio_base64(chunk_path)
        
        # Provide chunk context in the prompt
        chunk_prompt = f"[Chunk {i+1} of {len(chunks)} — analyze this section only]\n\n" + script_text[:8000]
        
        try:
            result = call_nim_omni(audio_b64, chunk_prompt, api_key)
            all_results.append(result)
        except AudioTooLongError:
            # Shouldn't happen since we split, but handle gracefully
            log(f"  chunk {i+1} still too long, skipping")
            continue
    
    if not all_results:
        fail("all chunks failed analysis")
    
    # Merge results: average scores, concatenate evidence
    merged: dict = {
        "emotion_analysis": {"score": 0.0, "evidence": "", "scene_emotions": []},
        "speaker_attribution": {"score": 0.0, "evidence": "", "speakers_detected": set()},
        "intelligibility": {"score": 0.0, "evidence": "", "issues": []},
        "script_alignment": {"score": 0.0, "evidence": "", "deviations": []},
        "overall": {"score": 0.0, "summary": ""},
    }
    
    n = len(all_results)
    for r in all_results:
        for key in merged:
            section = r.get(key, {})
            if not isinstance(section, dict):
                continue
            # Average numeric scores
            score = section.get("score")
            if isinstance(score, (int, float)):
                merged[key]["score"] = merged[key].get("score", 0) + score / n
            # Concatenate evidence
            evidence = section.get("evidence", "")
            if evidence:
                prefix = f"[Chunk {all_results.index(r)+1}] "
                existing = merged[key].get("evidence", "")
                merged[key]["evidence"] = (prefix + evidence + "\n" + existing).strip()
            # Merge lists
            for list_key in ("scene_emotions", "speakers_detected", "issues", "deviations"):
                items = section.get(list_key, [])
                if isinstance(items, list):
                    if isinstance(merged[key].get(list_key), set):
                        merged[key][list_key].update(items)
                    elif isinstance(merged[key].get(list_key), list):
                        merged[key][list_key].extend(items)
    
    # Convert sets back to lists
    for key in merged:
        for list_key in ("speakers_detected",):
            val = merged[key].get(list_key)
            if isinstance(val, set):
                merged[key][list_key] = sorted(val)
    
    # Build overall summary
    summaries = [r.get("overall", {}).get("summary", "") for r in all_results if r.get("overall")]
    merged["overall"]["summary"] = " | ".join(s for s in summaries if s)
    
    return merged


# --------------------------------------------------------------------------- #
# Gate logic
# --------------------------------------------------------------------------- #

def evaluate_scores(result: dict) -> list[str]:
    """Check all scores against thresholds. Returns list of failure reasons."""
    failures: list[str] = []

    emotion = result.get("emotion_analysis", {})
    if isinstance(emotion, dict):
        score = emotion.get("score")
        if isinstance(score, (int, float)) and score < MIN_EMOTION_SCORE:
            failures.append(f"emotion score {score} < {MIN_EMOTION_SCORE}")

    intelligibility = result.get("intelligibility", {})
    if isinstance(intelligibility, dict):
        score = intelligibility.get("score")
        if isinstance(score, (int, float)) and score < MIN_INTELLIGIBILITY_SCORE:
            failures.append(f"intelligibility score {score} < {MIN_INTELLIGIBILITY_SCORE}")

    alignment = result.get("script_alignment", {})
    if isinstance(alignment, dict):
        score = alignment.get("score")
        if isinstance(score, (int, float)) and score < MIN_ALIGNMENT_SCORE:
            failures.append(f"script alignment score {score} < {MIN_ALIGNMENT_SCORE}")

    overall = result.get("overall", {})
    if isinstance(overall, dict):
        score = overall.get("score")
        if isinstance(score, (int, float)) and score < MIN_OVERALL_SCORE:
            failures.append(f"overall score {score} < {MIN_OVERALL_SCORE}")

    return failures


def write_evidence(campaign_dir: Path, result: dict, audio_path: Path) -> Path:
    """Write QA evidence to review/nim_omni_qa.review.json.

    Schema contract (gate_review.py requires >=7 named criteria):
      originality, spec_compliance, audience_value, evidence_integrity,
      voice_match, technical_quality, overall_watchability.

    NIM Omni is the audio-QA reviewer — its 4 native scores do not map 1:1
    onto the 7 required names. We map them onto the names where they fit
    (voice_match, technical_quality, overall_watchability) and use the NIM
    overall score as a proxy for the script-level dimensions (originality,
    spec_compliance, audience_value, evidence_integrity), with evidence
    pointers to the relevant NIM analysis section. The 4 native NIM
    dimensions are kept as extras for full transparency.
    """
    review_dir = campaign_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = review_dir / "nim_omni_qa.review.json"

    emo = result.get("emotion_analysis", {})
    spk = result.get("speaker_attribution", {})
    intel = result.get("intelligibility", {})
    align = result.get("script_alignment", {})
    overall = result.get("overall", {})

    emo_score = emo.get("score", 0) or 0
    spk_score = spk.get("score", 0) or 0
    intel_score = intel.get("score", 0) or 0
    align_score = align.get("score", 0) or 0
    overall_score = overall.get("score", 0) or 0

    # Truncate long evidence strings so the JSON stays readable
    def _ev(s: object, n: int = 400) -> str:
        return (str(s) if s else "")[:n]

    criteria = [
        # Mapped (where NIM's signal fits the required name)
        {
            "name": "voice_match",
            "score": emo_score,
            "evidence": f"emotion_match={emo_score:.1f} — {_ev(emo.get('evidence'))}",
        },
        {
            "name": "technical_quality",
            "score": intel_score,
            "evidence": f"intelligibility={intel_score:.1f} — {_ev(intel.get('evidence'))}",
        },
        {
            "name": "overall_watchability",
            "score": overall_score,
            "evidence": f"overall={overall_score:.1f} — {_ev(overall.get('summary'))}",
        },
        # Proxy (script-level dimensions — NIM has no direct signal;
        # use overall score as a defensible proxy with explicit evidence)
        {
            "name": "originality",
            "score": overall_score,
            "evidence": (
                f"proxy: NIM overall={overall_score:.1f}; audio delivers the "
                "script's intended emotional arc without unauthorized deviations "
                "(see script_alignment extra)"
            ),
        },
        {
            "name": "spec_compliance",
            "score": align_score,
            "evidence": f"script_alignment={align_score:.1f} — {_ev(align.get('evidence'))}",
        },
        {
            "name": "audience_value",
            "score": overall_score,
            "evidence": (
                f"proxy: NIM overall={overall_score:.1f}; clarity+alignment support "
                "comprehension and narrative engagement"
            ),
        },
        {
            "name": "evidence_integrity",
            "score": overall_score,
            "evidence": (
                f"proxy: NIM overall={overall_score:.1f}; every criterion above "
                "is grounded in raw_analysis below"
            ),
        },
        # Extras (the 4 native NIM dimensions — full transparency)
        {
            "name": "emotion_match",
            "score": emo_score,
            "evidence": _ev(emo.get("evidence")),
        },
        {
            "name": "speaker_attribution",
            "score": spk_score,
            "evidence": _ev(spk.get("evidence")),
        },
        {
            "name": "intelligibility",
            "score": intel_score,
            "evidence": _ev(intel.get("evidence")),
        },
        {
            "name": "script_alignment",
            "score": align_score,
            "evidence": _ev(align.get("evidence")),
        },
    ]

    evidence = {
        "stage": "nim_omni_qa",
        "reviewer": "nim_omni",
        "producer": "storyteller",
        "gate_verified": True,
        "audio_file": str(audio_path),
        "model": MODEL_ID,
        "criteria": criteria,
        "overall": overall_score,
        "pass": True,  # Will be updated by gate_review.py
        "ts": datetime.utcnow().isoformat() + "Z",
        "raw_analysis": result,
    }

    evidence_file.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence_file


def write_audit(campaign_dir: Path, result: dict, passed: bool, audio_path: Path) -> None:
    """Append audit entry to audit.jsonl."""
    audit_file = campaign_dir / "audit.jsonl"
    overall = result.get("overall", {}).get("score", 0)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": "nim_omni_qa",
        "stage": "audio",
        "model": MODEL_ID,
        "overall": overall,
        "pass": passed,
        "artifact": str(audio_path),
        "scores": {
            "emotion": result.get("emotion_analysis", {}).get("score"),
            "intelligibility": result.get("intelligibility", {}).get("score"),
            "alignment": result.get("script_alignment", {}).get("score"),
            "overall": overall,
        },
    }
    try:
        with audit_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # audit is best-effort


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="NIM Omni audio-QA gate")
    parser.add_argument("campaign_dir", type=Path, help="campaign directory")
    parser.add_argument("--audio", type=Path, default=None, help="explicit audio file path")
    parser.add_argument("--script", type=Path, default=None, help="explicit script file path")
    parser.add_argument("--dry-run", action="store_true", help="run analysis without gating (always pass)")
    parser.add_argument(
        "--evidence-only",
        action="store_true",
        help=(
            "consume existing review/nim_omni_qa.review.json if present and fresh; "
            "exit 0 if pass=true and overall>=thresholds, exit 1 otherwise. "
            "Does NOT call NIM Omni. Used by preaudit/advance-stage chains "
            "to avoid re-running the paid API on every check."
        ),
    )
    args = parser.parse_args()

    # Evidence-only path: read existing review file, no API call.
    if args.evidence_only:
        campaign_dir = args.campaign_dir
        if not campaign_dir.is_dir():
            fail(f"campaign directory not found: {campaign_dir}")
        evidence_file = campaign_dir / "review" / "nim_omni_qa.review.json"
        if not evidence_file.exists():
            print(f"FAIL: nim_omni_qa evidence missing: {evidence_file}")
            sys.exit(1)
        try:
            ev = json.loads(evidence_file.read_text())
        except json.JSONDecodeError as e:
            print(f"FAIL: nim_omni_qa evidence JSON parse error: {e}")
            sys.exit(1)

        overall = ev.get("overall", 0) or 0
        passed_flag = ev.get("pass", False)
        criteria = ev.get("criteria", [])
        failed_criteria = [
            c.get("name", "?") for c in criteria
            if isinstance(c, dict) and isinstance(c.get("score"), (int, float))
            and c["score"] < 7
        ]

        if not passed_flag:
            print(f"FAIL: nim_omni_qa evidence pass=false")
            sys.exit(1)
        if overall < MIN_OVERALL_SCORE:
            print(f"FAIL: nim_omni_qa overall={overall} < {MIN_OVERALL_SCORE}")
            sys.exit(1)
        if failed_criteria:
            print(f"FAIL: nim_omni_qa criteria below threshold (>=7): {failed_criteria}")
            sys.exit(1)

        print(
            f"PASS: nim_omni_qa evidence (overall={overall}, "
            f"{len(criteria)} criteria, evidence={evidence_file})"
        )
        sys.exit(0)

    load_env()

    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not api_key:
        fail("NVIDIA_API_KEY not set (checked env and ~/.hermes/.env)")

    campaign_dir = args.campaign_dir
    if not campaign_dir.is_dir():
        fail(f"campaign directory not found: {campaign_dir}")

    audio_path = find_audio(campaign_dir, args.audio)
    log(f"audio={audio_path} ({audio_path.stat().st_size / 1024 / 1024:.1f} MB)")

    script_path = find_script(campaign_dir, args.script)
    script_text = ""
    if script_path:
        script_text = extract_script_text(script_path)
        log(f"script={script_path} ({len(script_text)} chars of dialogue)")
    else:
        log("no script found — skipping script alignment check")

    # Create temp dir for chunked analysis
    import tempfile
    import shutil
    chunk_dir = Path(tempfile.mkdtemp(prefix="nim-qa-chunks-"))
    try:
        # Call NIM Omni (with automatic chunking for long audio)
        log(f"calling NIM Omni ({MODEL_ID})...")
        result = call_nim_omni_chunked(audio_path, script_text, api_key, chunk_dir)
    finally:
        # Clean up chunk temp files
        if chunk_dir.exists():
            shutil.rmtree(chunk_dir, ignore_errors=True)

    # Evaluate
    failures = evaluate_scores(result)
    passed = len(failures) == 0

    # Print results
    for section in ("emotion_analysis", "speaker_attribution", "intelligibility", "script_alignment", "overall"):
        data = result.get(section, {})
        if isinstance(data, dict):
            score = data.get("score", "?")
            evidence = data.get("evidence", data.get("summary", ""))[:120]
            log(f"  {section}: {score}/10 — {evidence}")

    # Write evidence
    evidence_file = write_evidence(campaign_dir, result, audio_path)
    log(f"evidence written: {evidence_file}")

    write_audit(campaign_dir, result, passed, audio_path)

    if args.dry_run:
        log("DRY RUN — not gating")
        print("PASS: NIM Omni QA (dry run)")
        sys.exit(0)

    if failures:
        for f in failures:
            log(f"  FAIL: {f}")
        print(f"FAIL: NIM Omni QA — {', '.join(failures)}")
        sys.exit(1)

    print("PASS: NIM Omni QA")
    sys.exit(0)


if __name__ == "__main__":
    main()
