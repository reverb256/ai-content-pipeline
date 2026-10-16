#!/usr/bin/env python3
"""
music/mix/master.py — music mix and mastering pipeline.

RULER: loudness is EBU R128 integrated loudness in LUFS, measured with
`ffmpeg -af ebur128=peak=true`. This tool does NOT define that ruler. It loads
`music/gates/gate_loudness.py` and calls the gate's own `measure()`, `TARGETS`,
`DEFAULT_TOLERANCE` and `RULER`, so the master stage and the package stage speak
one dialect and one ruler (card t_568c67d2). `volumedetect` mean_volume is still
logged, but only as labelled RMS/crest context: it is an ungated, unweighted
mean and not a loudness result. It was retired as the lane's loudness ruler on
card t_9546841b.

Features:
- Loudness normalization to -14 LUFS (streaming) or -16 LUFS (sync) with true-peak limiting.
  Uses two-pass loudnorm; falls back to one-pass only when the first pass cannot
  be READ (no loudnorm JSON block), and says so loudly.
- Unmeasurable input: an input the EBU R128 ruler cannot measure — shorter than
  the 400 ms gating block, silent, or with no gating block above the -70 LUFS
  absolute gate — is REFUSED with a named cause, and no master is written
  (card t_df793408). A non-finite first-pass measurement (`input_i=-inf`,
  `target_offset=inf`) is never copied into the second pass. Why refusing beats
  the one-pass fallback, measured on ffmpeg 9.0.2: see
  `diagnose_unmeasurable_input`.
- Loudness verification: the normalized master is measured with the gate's
  ebur128 ruler. The integrated LUFS, the true peak and the deviation from the
  target are logged. A deviation outside the gate window (+/-1.0 LUFS) FAILS the
  run (exit 1) unless --allow-loudness-drift downgrades it to a warning.
- Stem handling: verify 12 time-aligned WAV stems, write stem manifest.
- Instrumental version generation (vocals-out) by muting the vocal stem.
- Seamless loop point detection: attempts to find a loop where the start and end are similar
  and the boundary is at a zero-crossing (to avoid clicks). For simplicity, we check if the
  entire file can be looped by verifying the start and end samples are near zero.
- DRY vocal stem check: check the vocal stem for reverb/tail by measuring RMS in the last 50ms.

Usage:
    python music/mix/master.py <input_master> [--stems <stems_dir>] [--mode streaming|sync] [--output <output_master>]

    <input_master>: path to the mastered audio file (WAV) to be normalized.
    --stems: directory containing 12 WAV stems (optional).
    --mode: either 'streaming' (default) or 'sync' for loudness target.
    --output: path for the normalized master (default: input_master with .normalized suffix).
    --allow-loudness-drift: log loudness drift and continue, instead of failing.

The script logs the integrated LUFS of the normalized master, its true peak,
the deviation from the target, and the volumedetect numbers as RMS context.

Exit codes: 0 = normalized and inside the gate's loudness window (or drift
allowed), 1 = failure (normalization failed, the input is one the ruler cannot
measure, loudness not measurable, or drift outside the window), 2 = usage error.

Dependencies: ffmpeg, ffprobe (must be on PATH).
"""

import argparse
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Constants
REPO_ROOT = Path(os.environ.get("REPO", Path.home() / "Projects" / "ai-content-pipeline"))
MUSIC_ROOT = REPO_ROOT / "music"
# The loudness ruler and the loudness target table live in the gate. This tool
# imports them; it must never carry a second loudness dialect (card t_568c67d2).
GATE_LOUDNESS_PATH = MUSIC_ROOT / "gates" / "gate_loudness.py"
DEFAULT_LOUDNESS_STREAMING = -14.0  # LUFS
DEFAULT_LOUDNESS_SYNC = -16.0       # LUFS
TRUE_PEAK_LIMIT = -1.5              # dBTP
# EBU R128 / ffmpeg ebur128 gating block, in milliseconds. The ruler is defined
# only for inputs at least this long: a block is 400 ms with 75% overlap, and
# ffmpeg's ebur128 filter has no option to shorten it (`ffmpeg -h filter=ebur128`
# on 9.0.2 lists no block-size control — measured 2026-10-16, card t_df793408).
GATING_BLOCK_MS = 400.0
STEMS_COUNT = 12
STEMS_TOLERANCE_SECONDS = 0.5       # duration match tolerance
ZERO_CROSSING_THRESHOLD = 0.01      # absolute sample value threshold for zero-crossing (float PCM)
DRY_TAIL_RMS_THRESHOLD = 0.02       # RMS threshold for detecting tail in vocal stem (float PCM)
LOOKAHEAD_MS = 10                   # lookahead for zero-crossing in milliseconds


def log(msg: str) -> None:
    """Print a timestamped log message."""
    print(f"[music-mix-master] {msg}", flush=True)


def log_err(msg: str) -> None:
    """Print a timestamped failure/warning message to stderr.

    Failures go to stderr so a shell pipeline (`master.py ... && next-stage`)
    and the operator both see them without reading the whole stdout log.
    """
    print(f"[music-mix-master] {msg}", file=sys.stderr, flush=True)


def run_ffmpeg(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run an ffmpeg command; raise on failure."""
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=False)  # Capture binary output
    except subprocess.CalledProcessError as e:
        # Try to decode stderr/stdout for logging, but if it's binary, we'll show a hexdump or just say it's binary
        stderr = e.stderr
        stdout = e.stdout
        if stderr is not None:
            try:
                stderr_str = stderr.decode('utf-8', errors='replace')
            except:
                stderr_str = f"<binary data {len(stderr)} bytes>"
        else:
            stderr_str = "<None>"
        if stdout is not None:
            try:
                stdout_str = stdout.decode('utf-8', errors='replace')
            except:
                stdout_str = f"<binary data {len(stdout)} bytes>"
        else:
            stdout_str = "<None>"
        tail_stderr = stderr_str.strip().splitlines()[-8:] if stderr_str else []
        tail_stdout = stdout_str.strip().splitlines()[-8:] if stdout_str else []
        raise RuntimeError(
            f"ffmpeg command failed: {' '.join(cmd)}\\n"
            f"stderr: {'\\n'.join(tail_stderr) if tail_stderr else '(no stderr)'}\\n"
            f"stdout: {'\\n'.join(tail_stdout) if tail_stdout else '(no stdout)'}"
        ) from e


def run_ffprobe(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run an ffprobe command; raise on failure."""
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        tail = (e.stderr or e.stdout or "").strip().splitlines()[-8:]
        raise RuntimeError(
            f"ffprobe command failed: {' '.join(cmd)}\n" + "\n".join(tail)
        ) from e


# ---------------------------------------------------------------------------
# Loudness ruler — imported from the gate, never re-implemented here.
# ---------------------------------------------------------------------------
_GATE_MODULE = None


def loudness_gate():
    """Load `music/gates/gate_loudness.py` — the ONE loudness ruler of this lane.

    The gate owns the ruler (EBU R128 integrated loudness via
    `ffmpeg -af ebur128=peak=true`), the target table and the tolerance. This
    tool imports that module instead of defining its own regexes, so a change to
    the ruler reaches both stages and the two can never disagree (card
    t_568c67d2: "Reuse the gate's ruler — do not add a second dialect").
    """
    global _GATE_MODULE
    if _GATE_MODULE is None:
        if not GATE_LOUDNESS_PATH.is_file():
            raise RuntimeError(
                f"loudness gate not found at {GATE_LOUDNESS_PATH} — the master "
                "stage will not measure loudness with a dialect of its own"
            )
        spec = importlib.util.spec_from_file_location(
            "music_gates_gate_loudness", GATE_LOUDNESS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _GATE_MODULE = module
    return _GATE_MODULE


def loudness_targets() -> dict:
    """Target LUFS per mode, from the gate's TARGETS table (one source of truth)."""
    gate = loudness_gate()
    targets = dict(getattr(gate, "TARGETS", {}) or {})
    if not targets:
        raise RuntimeError(f"{GATE_LOUDNESS_PATH} exposes no TARGETS table")
    for mode, local in (("streaming", DEFAULT_LOUDNESS_STREAMING),
                        ("sync", DEFAULT_LOUDNESS_SYNC)):
        if mode in targets and abs(targets[mode] - local) > 1e-9:
            log(f"WARNING: master.py's {mode} default is {local} LUFS but "
                f"gate_loudness TARGETS[{mode}] is {targets[mode]} LUFS; "
                f"using the gate's value")
    return targets


def measure_loudness_lufs(audio_path: Path) -> dict:
    """Measure a file with the gate's ruler. Returns the gate's result dict.

    ok=True  -> integrated_lufs, true_peak_dbfs, ffmpeg_stderr_tail
    ok=False -> error
    """
    gate = loudness_gate()
    return gate.measure(Path(audio_path))


def verify_master_loudness(
    audio_path: Path,
    target_lufs: float,
    tolerance: Optional[float] = None,
) -> dict:
    """Measure the normalized master and report its deviation from the target.

    Tolerance defaults to the gate's own DEFAULT_TOLERANCE, so the master stage
    and the package gate fail on the same window (card t_568c67d2).
    """
    gate = loudness_gate()
    if tolerance is None:
        tolerance = getattr(gate, "DEFAULT_TOLERANCE", 1.0)
    ruler = getattr(gate, "RULER", "ebur128 integrated loudness (LUFS)")
    result = measure_loudness_lufs(audio_path)
    if not result.get("ok"):
        return {"ok": False, "ruler": ruler, "error": result.get("error"),
                "target_lufs": target_lufs, "tolerance_lufs": tolerance}
    measured = float(result["integrated_lufs"])
    deviation = measured - target_lufs
    return {
        "ok": True,
        "ruler": ruler,
        "file": str(audio_path),
        "integrated_lufs": measured,
        "true_peak_dbfs": result.get("true_peak_dbfs"),
        "target_lufs": target_lufs,
        "tolerance_lufs": tolerance,
        "deviation_lufs": deviation,
        "within_tolerance": abs(deviation) <= tolerance,
    }


def measure_loudness_volumedetect(audio_path: Path) -> dict:
    """
    Run ffmpeg volumedetect filter and parse the output.
    Returns a dict with keys: 'mean_volume', 'max_volume', 'histogram'.

    RMS/crest context only — never the loudness result. volumedetect is a plain
    mean with no K-weighting and no gating, so it is not a LUFS reading; it was
    retired as this lane's loudness ruler on card t_9546841b. The loudness
    verdict comes from `verify_master_loudness`, on the gate's ebur128 ruler.
    """
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(audio_path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    result = run_ffmpeg(cmd)
    # stdout is binary, stderr contains the volumedetect output
    stderr_str = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
    # Parse the stderr output for volumedetect
    mean_volume = None
    max_volume = None
    histogram = []
    for line in stderr_str.splitlines():
        if "mean_volume" in line:
            # Example: [Parsed_volumedetect_0 @ 0x55a5c1c5b0c0] mean_volume: -12.3 dB
            try:
                mean_volume = float(line.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
        elif "max_volume" in line:
            # Example: [Parsed_volumedetect_0 @ 0x55a5c1c5b0c0] max_volume: -1.2 dB
            try:
                max_volume = float(line.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
        elif "histogram" in line:
            # We'll skip detailed histogram parsing for now; just note it's present.
            histogram.append(line.strip())
    return {
        "mean_volume": mean_volume,
        "max_volume": max_volume,
        "histogram": histogram,
    }


LOUDNORM_JSON_RE = re.compile(r"\{[^{}]*\}")


def parse_loudnorm_first_pass(stderr: str) -> dict:
    """Return the loudnorm JSON block from an ffmpeg first-pass run.

    ffmpeg prints the `print_format=json` block and then keeps printing muxer
    stats, so the block is NOT the last line of stderr. On ffmpeg 9.0.2 the tail
    is `[out#0/null ...] video:0KiB audio:...` followed by `size=N/A time=...`,
    so `json.loads(stderr.splitlines()[-1])` always raised and the two-pass
    normalizer silently degraded to one-pass. Measured on this-small-forever
    (card t_568c67d2): the tool's output landed at -28.0 LUFS integrated, 14 LU
    below the -14 LUFS target it was asked for, and the log showed nothing.
    Match the JSON block itself, not its position.
    """
    for blob in reversed(LOUDNORM_JSON_RE.findall(stderr or "")):
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if "input_i" in data:
            return data
    raise ValueError("no loudnorm JSON block found in ffmpeg stderr")


class UnmeasurableInputError(RuntimeError):
    """The input carries no loudness the lane's EBU R128 ruler can measure.

    Raised instead of copying a non-finite loudnorm measurement into the second
    pass, which ffmpeg rejects with a raw dump (card t_df793408). `causes` holds
    one `(cause, advice)` pair per reason the ruler cannot measure the input;
    `fields` holds the raw first-pass values as evidence.
    """

    def __init__(self, input_path: Path, causes, fields: dict):
        self.input_path = Path(input_path)
        self.causes: List[Tuple[str, str]] = list(causes)
        self.fields = dict(fields)
        self.fields_text = " ".join(
            f"{name}={value}" for name, value in self.fields.items())
        super().__init__(
            f"{self.input_path}: "
            + "; ".join(cause for cause, _ in self.causes))


def finite_or_none(value) -> Optional[float]:
    """Parse one loudnorm field; return None when it is not a finite number.

    loudnorm reports a field it could not measure as the literal string `-inf`
    (or `inf`, or `nan`). `float("-inf")` is a real float, so a plain `float()`
    call hides the defect: the value travels straight into the second pass and
    ffmpeg dies with "Value -inf for parameter 'measured_I' out of range
    [-99 - 0]" (measured on ffmpeg 9.0.2, card t_df793408). None means "not a
    number this tool may hand to ffmpeg".
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def audio_duration_seconds(audio_path: Path) -> Optional[float]:
    """Duration in seconds, or None when ffprobe cannot read it."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(audio_path),
    ]
    try:
        result = run_ffprobe(cmd)
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError,
            RuntimeError) as e:
        log(f"WARNING: could not read the duration of {audio_path}: {e}")
        return None


def diagnose_unmeasurable_input(
    data: dict,
    duration_s: Optional[float],
) -> List[Tuple[str, str]]:
    """Name WHY the EBU R128 ruler cannot measure `input_path`.

    Returns [(cause, advice), ...] — one pair per applicable cause, because an
    input can be both silent and shorter than a gating block.

    The ruler needs a 400 ms gating block whose loudness passes the -70 LUFS
    absolute gate. A block is 400 ms and ffmpeg's ebur128 filter cannot shorten
    it (`ffmpeg -h filter=ebur128`, 9.0.2), so an input shorter than 400 ms has
    no measurable loudness by the standard — not by this tool's choice.
    Measured on zephyr 2026-10-16 (ffmpeg 9.0.2, card t_df793408) while writing
    this diagnosis; ebur128 prints -70.0 LUFS (its floor) where loudnorm prints
    -inf, which is why the cause is read from the pass-1 values and the
    duration, never from the floor:

      input                      dur     pass1 input_i  pass1 input_tp  ebur128 I
      440 Hz tone                0.30 s  -inf           -24.06         -70.0 LUFS
      440 Hz tone                0.39 s  -inf           -24.06         -70.0 LUFS
      440 Hz tone                0.40 s  -27.75         -24.06         -27.8 LUFS
      440 Hz tone                2.00 s  -27.75         -24.06         -27.8 LUFS
      440 Hz tone at -75 dBFS    2.00 s  -inf           -77.95         -70.0 LUFS
      digital silence            3.00 s  -inf           -inf           -70.0 LUFS
      0.2 s burst + 3 s silence  3.20 s  -32.10         -24.06         -32.0 LUFS

    The 0.40 s row is deliberately included: master.py must keep mastering it.
    """
    causes: List[Tuple[str, str]] = []
    peak = finite_or_none(data.get("input_tp"))
    duration_ms = None if duration_s is None else duration_s * 1000.0

    if peak is None:
        causes.append((
            "input is silent: loudnorm pass 1 measured no true peak at all "
            f"(input_tp={data.get('input_tp')} dBFS), so there is no signal to "
            "normalize",
            "check the bounce before re-running — a muted vocal stem or an "
            "empty render produces exactly this. Silence has no level to set.",
        ))
    if duration_ms is not None and duration_ms < GATING_BLOCK_MS:
        causes.append((
            "input is shorter than the 400 ms EBU R128 gating block "
            f"({duration_ms:.0f} ms; pass 1 input_i={data.get('input_i')}): the "
            "ruler is defined only for inputs 400 ms and longer",
            "give the item at least 400 ms of audible content — extend the "
            "one-shot, or master it inside the longer item it ships in — and "
            "re-run. A 400 ms gating block is not configurable in ffmpeg's "
            "ebur128/loudnorm, so a shorter item cannot be measured at all.",
        ))
    if not causes and peak is not None:
        length = (f"{duration_ms:.0f} ms long" if duration_ms is not None
                  else "of unreadable duration")
        causes.append((
            "input has no gating block above the EBU R128 absolute gate: "
            f"loudnorm pass 1 returned no finite integrated loudness "
            f"(input_i={data.get('input_i')}) although the input is {length} and "
            f"carries a real true peak ({peak:.2f} dBFS), so every 400 ms "
            "gating block sits below -70 LUFS",
            "raise the bounce or re-render it. loudnorm cannot measure a file "
            "whose every gating block the ruler's -70 LUFS absolute gate "
            "rejects whole.",
        ))
    if not causes:
        causes.append((
            "input has no finite loudness measurement: loudnorm pass 1 returned "
            f"input_i={data.get('input_i')} "
            f"target_offset={data.get('target_offset')}, and the duration could "
            "not be read",
            "inspect the file. master.py refuses rather than pass a non-finite "
            "measurement to ffmpeg, where a second pass with measured_I=-inf "
            "dies with 'Numerical result out of range'.",
        ))
    return causes


def normalize_loudness_two_pass(
    input_path: Path,
    output_path: Path,
    target_lufs: float,
    true_peak: float = TRUE_PEAK_LIMIT,
) -> Path:
    """
    Normalize loudness using ffmpeg loudnorm filter (two-pass).
    Returns the path to the normalized audio.

    An input the lane's EBU R128 ruler cannot measure is REFUSED, not papered
    over (card t_df793408). When pass 1 returns a non-finite measurement —
    `input_i=-inf` and `target_offset=inf` for a sub-400 ms or silent input —
    this raises `UnmeasurableInputError` with the named cause(s) and writes
    nothing. The non-finite values are never copied into the second pass: ffmpeg
    rejects `measured_I=-inf` with "Value -inf for parameter 'measured_I' out of
    range [-99 - 0]" and the run dies with a raw stderr dump instead of a
    diagnosis.

    Why refuse rather than fall back to one-pass loudnorm, measured on zephyr
    with ffmpeg 9.0.2: one-pass on a 0.30 s tone does write a file (rc 0), but
    that file's ebur128 integrated loudness is -70.0 LUFS — the ruler's floor,
    since no 400 ms gating block exists — and gate_loudness FAILS it
    ("measured : integrated -70.00 LUFS (true peak -1.50 dBFS), deviation
    -56.00 LUFS"), with its peak pushed to -1.5 dBFS on the way. A master no
    stage can measure and the package gate must reject is not a deliverable, so
    the tool writes nothing and names the cause instead.
    """
    # First pass: measure the source
    cmd1 = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        f"loudnorm=I={target_lufs}:LRA=11:TP={true_peak}:print_format=json",
        "-f",
        "null",
        "-",
    ]
    try:
        result1 = run_ffmpeg(cmd1)
        # stdout is binary, stderr carries the loudnorm JSON block
        stderr_str = result1.stderr.decode('utf-8', errors='replace') if result1.stderr else ''
        data = parse_loudnorm_first_pass(stderr_str)
    except (json.JSONDecodeError, IndexError, ValueError) as e:
        log(f"WARNING: could not read the loudnorm first-pass measurement: {e}")
        log("WARNING: falling back to one-pass loudnorm — accuracy drops. The "
            "integrated-LUFS verification after normalization is the safety net.")
        return normalize_loudness_one_pass(input_path, output_path, target_lufs, true_peak)

    # Card t_df793408: a field loudnorm could not measure comes back as -inf/inf.
    # Detect it here, before it reaches the second-pass filter string.
    measured = {
        "input_i": finite_or_none(data.get("input_i")),
        "input_lra": finite_or_none(data.get("input_lra")),
        "input_tp": finite_or_none(data.get("input_tp")),
        "input_thresh": finite_or_none(data.get("input_thresh")),
        "target_offset": finite_or_none(data.get("target_offset")),
    }
    if any(value is None for value in measured.values()):
        raise UnmeasurableInputError(
            input_path,
            diagnose_unmeasurable_input(data, audio_duration_seconds(input_path)),
            {name: data.get(name) for name in measured},
        )
    measured_I = measured["input_i"]
    measured_LRA = measured["input_lra"]
    measured_TP = measured["input_tp"]
    measured_thresh = measured["input_thresh"]
    offset = measured["target_offset"]

    # Second pass: apply the normalization with the measured values
    cmd2 = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        f"loudnorm=I={target_lufs}:LRA=11:TP={true_peak}:measured_I={measured_I}:measured_LRA={measured_LRA}:measured_TP={measured_TP}:measured_thresh={measured_thresh}:offset={offset}:linear=true:print_format=summary",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    run_ffmpeg(cmd2)
    return output_path


def normalize_loudness_one_pass(
    input_path: Path,
    output_path: Path,
    target_lufs: float,
    true_peak: float = TRUE_PEAK_LIMIT,
) -> Path:
    """
    Normalize loudness using ffmpeg loudnorm filter (one-pass).
    Returns the path to the normalized audio.

    One-pass loudnorm measures the file internally, so no `measured_*` values
    are passed. The old call passed `measured_I=0.0 ... measured_thresh=0.0`,
    which told loudnorm the file was already at 0 LUFS and left the master
    almost untouched: measured on this-small-forever the output landed at -28.0
    LUFS integrated against a -14 LUFS target (card t_568c67d2). A plain
    one-pass run on the same file lands at -14.3 LUFS.
    """
    log(
        "Using one-pass loudnorm (less accurate than two-pass). "
        "Production work needs a readable first pass."
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        f"loudnorm=I={target_lufs}:LRA=11:TP={true_peak}:print_format=summary",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path


def verify_stems(stems_dir: Path) -> Tuple[bool, List[Path], Optional[dict]]:
    """
    Verify that the stems directory contains exactly 12 WAV stems.
    Check that their durations match within STEMS_TOLERANCE_SECONDS.
    Return (success, list_of_stem_paths, manifest_dict).
    manifest_dict includes stem names and durations.
    """
    if not stems_dir.is_dir():
        return False, [], None

    stem_files = sorted(stems_dir.glob("*.wav"))
    if len(stem_files) != STEMS_COUNT:
        log(
            f"Expected {STEMS_COUNT} WAV stems, found {len(stem_files)} in {stems_dir}"
        )
        return False, [], None

    # Get durations of each stem
    durations = []
    manifest = {}
    for stem_path in stem_files:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(stem_path),
        ]
        result = run_ffprobe(cmd)
        try:
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            log(f"Failed to get duration for {stem_path}: {e}")
            return False, [], None
        durations.append(duration)
        manifest[stem_path.name] = {
            "duration": duration,
            "path": str(stem_path),
        }

    # Check that all durations are within tolerance of the first stem
    base_duration = durations[0]
    for i, dur in enumerate(durations[1:], start=1):
        if abs(dur - base_duration) > STEMS_TOLERANCE_SECONDS:
            log(
                f"Stem {stem_files[i].name} duration {dur:.3f}s deviates from base {base_duration:.3f}s by >{STEMS_TOLERANCE_SECONDS}s"
            )
            return False, [], None

    # All good
    manifest["_summary"] = {
        "count": len(stem_files),
        "base_duration": base_duration,
        "duration_range": f"{min(durations):.3f} - {max(durations):.3f}",
    }
    return True, stem_files, manifest


def write_stem_manifest(manifest: dict, output_path: Path) -> None:
    """Write the stem manifest as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log(f"Wrote stem manifest to {output_path}")


def generate_instrumental(stems_dir: Path, output_path: Path) -> bool:
    """
    Generate an instrumental version by muting the vocal stem.
    We assume the vocal stem is named 'vocals.wav' (case-insensitive).
    If found, we mix all other stems; otherwise, we mix all stems.
    """
    if not stems_dir.is_dir():
        log(f"Stems directory {stems_dir} does not exist.")
        return False

    stem_files = sorted(stems_dir.glob("*.wav"))
    # Identify vocal stem: look for vocals.wav (case-insensitive)
    vocal_stem = None
    for stem in stem_files:
        if stem.name.lower() == "vocals.wav":
            vocal_stem = stem
            break

    # If we found a vocal stem, exclude it; otherwise, use all stems.
    if vocal_stem:
        stems_to_mix = [p for p in stem_files if p != vocal_stem]
        log(f"Excluding vocal stem {vocal_stem.name} for instrumental.")
    else:
        stems_to_mix = stem_files
        log("No vocal stem identified; mixing all stems for instrumental.")

    if not stems_to_mix:
        log("No stems to mix for instrumental.")
        return False

    # Mix the stems using ffmpeg amix
    inputs = []
    for stem in stems_to_mix:
        inputs.extend(["-i", str(stem)])
    filter_complex = f"amix=inputs={len(stems_to_mix)}:duration=longest:normalize=0"
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        run_ffmpeg(cmd)
        log(f"Generated instrumental at {output_path}")
        return True
    except RuntimeError as e:
        log(f"Failed to generate instrumental: {e}")
        return False


def detect_loop_point(input_path: Path) -> Tuple[Optional[float], Optional[float]]:
    """
    Attempt to detect a seamless loop point.
    We check if the start and end of the audio are near zero (within ZERO_CROSSING_THRESHOLD)
    to avoid a click when looping. If so, we consider the entire file as a loop (start=0, end=duration).
    Otherwise, we return None, None.
    """
    # We'll downmix to mono and convert to f32le raw PCM, then read the first and last 4 bytes.
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        "pan=mono|c0=c0",
        "-ar",
        "44100",
        "-ac",
        "1",
        "-f",
        "f32le",
        "-",
    ]
    try:
        result = run_ffmpeg(cmd)
        pcm_data = result.stdout  # This is raw binary PCM data
    except RuntimeError as e:
        log(f"Failed to extract PCM data for loop detection: {e}")
        return None, None

    if len(pcm_data) < 8:  # Need at least two samples (4 bytes each)
        log("Audio too short for loop detection.")
        return None, None

    # Convert the first 4 bytes to a float (little-endian)
    import struct
    first_sample = struct.unpack('<f', pcm_data[:4])[0]
    last_sample = struct.unpack('<f', pcm_data[-4:])[0]

    log(f"First sample: {first_sample:.6f}, Last sample: {last_sample:.6f}")

    # Check if both are close to zero
    if abs(first_sample) < ZERO_CROSSING_THRESHOLD and abs(last_sample) < ZERO_CROSSING_THRESHOLD:
        # Get the duration of the audio
        cmd_duration = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(input_path),
        ]
        try:
            result_duration = run_ffprobe(cmd_duration)
            data = json.loads(result_duration.stdout)
            duration = float(data["format"]["duration"])
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            log(f"Failed to get duration for loop detection: {e}")
            return None, None
        log(f"Loop point detected: start=0.0s, end={duration:.3f}s (zero-crossing at start and end)")
        return 0.0, duration
    else:
        log("No zero-crossing at start and end; cannot guarantee click-free loop.")
        return None, None


def check_vocal_stem_dry(stems_dir: Path) -> bool:
    """
    Check if the vocal stem is DRY (no echo/reverb tail).
    We measure the RMS of the last 50ms of the vocal stem.
    If the RMS is above DRY_TAIL_RMS_THRESHOLD, we consider it wet.
    Returns True if dry, False if wet.
    """
    vocal_stem = None
    for stem in stems_dir.glob("*.wav"):
        if stem.name.lower() == "vocals.wav":
            vocal_stem = stem
            break

    if not vocal_stem:
        log("No vocal stem found for dryness check.")
        return True  # Assume dry if not present? Or we should fail? We'll assume dry and log.

    # We'll use ffmpeg to extract the last 50ms and compute the RMS.
    # First, get the duration of the vocal stem.
    cmd_duration = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(vocal_stem),
    ]
    try:
        result_duration = run_ffprobe(cmd_duration)
        data = json.loads(result_duration.stdout)
        duration = float(data["format"]["duration"])
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        log(f"Failed to get duration for vocal stem: {e}")
        return True

    # Calculate the start time for the last 50ms
    tail_start = max(0, duration - 0.05)  # 50ms
    tail_duration = 0.05

    # Use ffmpeg to extract the tail and convert to mono f32le, then compute the RMS using astats.
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(vocal_stem),
        "-af",
        f"atrim=start={tail_start}:duration={tail_duration},pan=mono|c0=c0",
        "-ar",
        "44100",
        "-ac",
        "1",
        "-f",
        "f32le",
        "-",
    ]
    try:
        result = run_ffmpeg(cmd)
        pcm_data = result.stdout
    except RuntimeError as e:
        log(f"Failed to extract tail PCM for vocal stem: {e}")
        return True

    if len(pcm_data) < 4:
        log("Vocal stem tail too short for RMS calculation.")
        return True

    # Compute RMS of the PCM data (float32 samples)
    import struct
    import math
    samples = []
    for i in range(0, len(pcm_data), 4):
        sample = struct.unpack('<f', pcm_data[i:i+4])[0]
        samples.append(sample)
    if not samples:
        return True
    sum_squares = sum(s * s for s in samples)
    rms = math.sqrt(sum_squares / len(samples))
    log(f"Vocal stem tail RMS: {rms:.6f} (threshold: {DRY_TAIL_RMS_THRESHOLD})")
    if rms > DRY_TAIL_RMS_THRESHOLD:
        log("Vocal stem appears wet (reverb/tail detected).")
        return False
    else:
        log("Vocal stem appears dry.")
        return True


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Music mix and mastering pipeline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_master",
        type=Path,
        help="Path to the mastered audio file (WAV) to be normalized.",
    )
    parser.add_argument(
        "--stems",
        type=Path,
        default=None,
        help="Directory containing 12 WAV stems (optional).",
    )
    parser.add_argument(
        "--mode",
        choices=["streaming", "sync"],
        default="streaming",
        help="Loudness mode: streaming (-14 LUFS) or sync (-16 LUFS).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for normalized master (default: input_master with .normalized suffix).",
    )
    parser.add_argument(
        "--instrumental",
        type=Path,
        default=None,
        help="Output path for instrumental version (requires --stems).",
    )
    parser.add_argument(
        "--verify-stems",
        action="store_true",
        help="Verify stems and write manifest (requires --stems).",
    )
    parser.add_argument(
        "--stem-manifest",
        type=Path,
        default=Path("stem_manifest.json"),
        help="Path to write stem manifest (if --verify-stems is set).",
    )
    parser.add_argument(
        "--allow-loudness-drift",
        action="store_true",
        help="Log loudness drift outside the gate window and continue, "
             "instead of failing the run (exit 1).",
    )
    args = parser.parse_args(argv)

    # Validate input
    if not args.input_master.is_file():
        log(f"Input master file not found: {args.input_master}")
        return 1

    # Determine loudness target — from the gate's TARGETS table, so the master
    # stage and gate_loudness can never disagree on the number (card t_568c67d2).
    try:
        targets = loudness_targets()
    except Exception as e:
        log(f"FAILED: loudness targets unavailable: {e}")
        return 1
    if args.mode not in targets:
        log(f"FAILED: the gate's TARGETS table has no '{args.mode}' entry "
            f"(table: {sorted(targets)})")
        return 1
    target_lufs = targets[args.mode]

    # Set output path
    if args.output:
        output_master = args.output
    else:
        output_master = args.input_master.with_name(
            args.input_master.stem + ".normalized" + args.input_master.suffix
        )

    # Step 1: Normalize loudness (two-pass if possible)
    log(f"Normalizing loudness to {target_lufs} LUFS (true peak {TRUE_PEAK_LIMIT} dBTP)")
    try:
        normalized_master = normalize_loudness_two_pass(
            args.input_master, output_master, target_lufs
        )
        log(f"Normalized master written to {normalized_master}")
    except UnmeasurableInputError as e:
        # Card t_df793408: name the cause, write no master, keep exit 1. The old
        # path handed `measured_I=-inf` to ffmpeg and died with a raw dump.
        try:
            ruler = getattr(loudness_gate(), "RULER",
                            "ebur128 integrated loudness (LUFS)")
        except Exception:
            ruler = "ebur128 integrated loudness (LUFS)"
        log_err(f"FAILED: cannot loudness-normalize {e.input_path} — the lane's "
                f"ruler cannot measure this input, so no master was written")
        for cause, advice in e.causes:
            log_err(f"  cause   : {cause}")
            log_err(f"  fix     : {advice}")
        log_err(f"  pass 1  : {e.fields_text}")
        log_err(f"  ruler   : {ruler} — needs a 400 ms gating block above the "
                f"-70 LUFS absolute gate")
        log_err(f"  refused : writing a master whose loudness cannot be "
                f"measured would hand gate_loudness an artifact it must fail")
        return 1
    except Exception as e:
        log_err(f"Loudness normalization failed: {e}")
        return 1

    # Step 2: verify the loudness the normalizer targeted, with the lane's ruler
    # (EBU R128 integrated loudness, measured by gate_loudness's own `measure()`).
    try:
        ruler = getattr(loudness_gate(), "RULER",
                        "ebur128 integrated loudness (LUFS)")
        log(f"Verifying normalized master loudness with the lane's ruler: {ruler}")
        verdict = verify_master_loudness(normalized_master, target_lufs)
    except Exception as e:
        log_err(f"FAILED: loudness verification could not run: {e}")
        return 1

    if not verdict["ok"]:
        log_err(f"FAILED: loudness is not measurable on {normalized_master}: "
                f"{verdict['error']}")
        return 1

    peak = verdict["true_peak_dbfs"]
    peak_txt = "n/a" if peak is None else f"{peak:.2f} dBFS"
    log(f"integrated loudness: {verdict['integrated_lufs']:.2f} LUFS "
        f"(true peak {peak_txt})")
    log(f"target {verdict['target_lufs']:.1f} LUFS ({args.mode}) | "
        f"deviation {verdict['deviation_lufs']:+.2f} LUFS | "
        f"window +/-{verdict['tolerance_lufs']:.1f} LUFS")

    if verdict["within_tolerance"]:
        log("LOUDNESS OK: inside the window gate_loudness applies at package "
            "time, so the master should pass it unchanged.")
    else:
        drift = verdict["deviation_lufs"]
        direction = "LOUD" if drift > 0 else "QUIET"
        log_err(f"LOUDNESS DRIFT: integrated {verdict['integrated_lufs']:.2f} LUFS "
                f"is {abs(drift):.2f} LUFS {direction} of the "
                f"{verdict['target_lufs']:.1f} LUFS {args.mode} target "
                f"(window +/-{verdict['tolerance_lufs']:.1f} LUFS)")
        log_err(f"  master    : {normalized_master}")
        log_err(f"  ruler     : {verdict['ruler']}")
        log_err("  fix       : re-normalize with a two-pass measured loudnorm "
                "(pass 1 measured_I/TP/LRA, pass 2 with the measured_* values "
                "and offset), then re-run this tool and gate_loudness")
        if args.allow_loudness_drift:
            log("WARNING: --allow-loudness-drift is set — continuing with a "
                "master outside the gate window. gate_loudness WILL fail this "
                "master at package time.")
        else:
            log_err(f"FAILED: master is outside the +/-"
                    f"{verdict['tolerance_lufs']:.1f} LUFS window; drift is "
                    "caught here so it cannot reach a package. Re-run with "
                    "--allow-loudness-drift only if a human accepted the drift.")
            return 1

    # RMS context, kept for crest/headroom reading only — never the loudness
    # result: volumedetect is a plain mean with no K-weighting and no gating.
    try:
        vol_result = measure_loudness_volumedetect(normalized_master)
        log("RMS context (NOT the loudness result — volumedetect has no "
            "K-weighting and no gating):")
        log(f"  volumedetect mean_volume: {vol_result['mean_volume']} dB")
        log(f"  volumedetect max_volume: {vol_result['max_volume']} dB")
        if (vol_result["mean_volume"] is not None
                and vol_result["max_volume"] is not None):
            log(f"  crest factor (max - mean): "
                f"{vol_result['max_volume'] - vol_result['mean_volume']:.1f} dB")
    except Exception as e:
        log(f"WARNING: RMS context (volumedetect) unavailable: {e}")

    # Step 3: Stem handling (if --stems provided)
    if args.stems:
        if not args.stems.is_dir():
            log(f"Stems directory not found: {args.stems}")
            return 1

        if args.verify_stems:
            success, stem_files, manifest = verify_stems(args.stems)
            if not success:
                log("Stem verification failed.")
                return 1
            write_stem_manifest(manifest, args.stem_manifest)

        if args.instrumental:
            instrumental_path = args.instrumental
            if not generate_instrumental(args.stems, instrumental_path):
                log("Instrumental generation failed.")
                return 1

        # Check vocal stem dryness
        dry = check_vocal_stem_dry(args.stems)
        if not dry:
            log("WARNING: Vocal stem is not dry (has reverb/tail). This may not comply with ruling Ruling 2026-09-03-03.")

    # Step 4: Loop point detection (if we have a normalized master)
    loop_start, loop_end = detect_loop_point(normalized_master)
    if loop_start is not None and loop_end is not None:
        log(f"Detected loop point: start={loop_start:.3f}s, end={loop_end:.3f}s")
        # We can also verify the loop point is click-free by checking the zero-crossing (already done in detect_loop_point)
    else:
        log("Loop point detection did not find a seamless loop (no zero-crossing at start and end).")

    log("Music mix and mastering completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())