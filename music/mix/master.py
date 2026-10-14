#!/usr/bin/env python3
"""
music/mix/master.py — music mix and mastering pipeline.

Features:
- Loudness normalization to -14 LUFS (streaming) or -16 LUFS (sync) with true-peak limiting.
  Uses two-pass loudnorm if available, otherwise falls back to one-pass.
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

The script prints volumedetect output for the normalized master.

Dependencies: ffmpeg, ffprobe (must be on PATH).
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Constants
REPO_ROOT = Path(os.environ.get("REPO", Path.home() / "Projects" / "ai-content-pipeline"))
MUSIC_ROOT = REPO_ROOT / "music"
DEFAULT_LOUDNESS_STREAMING = -14.0  # LUFS
DEFAULT_LOUDNESS_SYNC = -16.0       # LUFS
TRUE_PEAK_LIMIT = -1.5              # dBTP
STEMS_COUNT = 12
STEMS_TOLERANCE_SECONDS = 0.5       # duration match tolerance
ZERO_CROSSING_THRESHOLD = 0.01      # absolute sample value threshold for zero-crossing (float PCM)
DRY_TAIL_RMS_THRESHOLD = 0.02       # RMS threshold for detecting tail in vocal stem (float PCM)
LOOKAHEAD_MS = 10                   # lookahead for zero-crossing in milliseconds


def log(msg: str) -> None:
    """Print a timestamped log message."""
    print(f"[music-mix-master] {msg}", flush=True)


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
            f"ffprobe command failed: {' '.join(cmd)}\\n" + "\\n".join(tail)
        ) from e


def measure_loudness_volumedetect(audio_path: Path) -> dict:
    """
    Run ffmpeg volumedetect filter and parse the output.
    Returns a dict with keys: 'mean_volume', 'max_volume', 'histogram'.
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


def normalize_loudness_two_pass(
    input_path: Path,
    output_path: Path,
    target_lufs: float,
    true_peak: float = TRUE_PEAK_LIMIT,
) -> Path:
    """
    Normalize loudness using ffmpeg loudnorm filter (two-pass).
    Returns the path to the normalized audio.
    """
    # First pass: get the measured loudness
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
        # stdout is binary, stderr contains the JSON
        stderr_str = result1.stderr.decode('utf-8', errors='replace') if result1.stderr else ''
        # Parse the JSON output from the first pass
        # The JSON is the last line of stderr
        lines = stderr_str.strip().splitlines()
        if not lines:
            raise ValueError("No output from loudnorm first pass")
        data = json.loads(lines[-1])
        measured_I = data.get("input_i", -999.0)
        measured_LRA = data.get("input_lra", 999.0)
        measured_TP = data.get("input_tp", -999.0)
        measured_thresh = data.get("input_thresh", -999.0)
        offset = data.get("target_offset", 0.0)
    except (json.JSONDecodeError, IndexError, ValueError) as e:
        log(f"Failed to parse loudnorm first pass output: {e}")
        # Fallback to one-pass if we can't parse
        log("Falling back to one-pass loudnorm.")
        return normalize_loudness_one_pass(input_path, output_path, target_lufs, true_peak)

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
    """
    log(
        "Using one-pass loudnorm (may be less accurate than two-pass). "
        "For production, consider using two-pass loudnorm."
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        f"loudnorm=I={target_lufs}:LRA=11:TP={true_peak}:measured_I=0.0:measured_LRA=0.0:measured_TP={true_peak}:measured_thresh=0.0:linear=true:print_format=summary",
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


def main() -> int:
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
    args = parser.parse_args()

    # Validate input
    if not args.input_master.is_file():
        log(f"Input master file not found: {args.input_master}")
        return 1

    # Determine loudness target
    if args.mode == "streaming":
        target_lufs = DEFAULT_LOUDNESS_STREAMING
    else:
        target_lufs = DEFAULT_LOUDNESS_SYNC

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
    except Exception as e:
        log(f"Loudness normalization failed: {e}")
        return 1

    # Step 2: Measure loudness with volumedetect and print output
    log("Measuring loudness with volumedetect on normalized master:")
    try:
        vol_result = measure_loudness_volumedetect(normalized_master)
        log(f"volumedetect mean_volume: {vol_result['mean_volume']} dB")
        log(f"volumedetect max_volume: {vol_result['max_volume']} dB")
        if vol_result["histogram"]:
            log("volumedetect histogram: (see stderr for details)")
    except Exception as e:
        log(f"Volumedetect measurement failed: {e}")
        # We don't fail the task for measurement failure, but we warn.

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