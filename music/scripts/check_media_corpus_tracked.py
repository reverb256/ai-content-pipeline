#!/usr/bin/env python3
"""check_media_corpus_tracked.py - the media a record NAMES must be IN the repo.

WHY THIS EXISTS (incident 2026-10-16, cards t_9682a610 / t_8f515be3)
-------------------------------------------------------------------
`campaigns/virtual-reflections/` kept its record in git and its media outside it.
Eleven media files (274.5 MB) lived only in the WIP ref
`origin/wip/atlas-backup-20261014` @ 3882292; five more - both copies of
`sincerely.wav`, both copies of `this-small-forever.wav` and
`this-small-forever.mp4` - were in NO ref at all, only untracked files in one
checkout, where a `git clean -xdf` deletes the only copy. All the while the
campaign's own `MANIFEST.json` named `audio_file` / `master_file` paths that git
did not hold, and its track 4 still read `exported: false` with a failure reason
months after that export had succeeded. Nothing failed: a record that points at
files nobody holds looks exactly like a record whose files are somewhere else.

Three smaller shapes of the same defect were measured in the same corpus:

  * `music/packages/streaming/t_verify_streaming/master.wav` was a SYMLINK (mode
    120000, 82 B) whose target was a pruned scratch dir under another profile's
    cache. `git cat-file -s` on it returns the LENGTH OF THE TARGET STRING, 82 -
    a package that ships a link ships no bytes.
  * the demo in `music/lanes/streaming.py` packed its throwaway track INTO the
    repo's `music/packages/streaming/`, so a verification run leaves a package
    dir behind. That is how the fixture above was made.

RULES - each one is the shape of one of those findings
  R1 named but not tracked   an exported track's `audio_file`, `master_file` and
                             `source_mp4_file` must be in the tree at the checked
                             revision, as a regular non-empty blob. A track that
                             is not exported must name no file.
  R2 stale failure record    a track with `exported: false` whose candidate
                             audio/masters file EXISTS (tracked, or on disk in a
                             live check) is a record that contradicts the disk.
  R3 a symlink is not media  every tracked media path under `campaigns/<c>/audio/`,
                             `campaigns/<c>/masters/` and
                             `music/packages/streaming/<pkg>/` must be mode
                             100644. git stores a link's target, not its bytes.
  R4 untracked but on disk   (live checks only) a media file present in the
                             working tree that git does not hold is one `git
                             clean` away from gone; the report names the refs
                             that DO carry it, so the fix is a commit, not a
                             re-extract.

Usage:
  /usr/bin/python3 music/scripts/check_media_corpus_tracked.py [--repo PATH] [--rev REV]
  /usr/bin/python3 music/scripts/check_media_corpus_tracked.py --selftest
Exit: 0 when the record and the repo agree; 1 when they do not; 3 when nothing
could be read (no checkout, unreadable manifest) - rc 3 is never a pass.

Cited: t_8f515be3 (this check), t_9682a610 (the stranded-ref reconcile that left
the media behind), t_21efbff9 (the export whose record was stranded),
t_5adf0c2a (the spec-2 sweep that found the stray `t_verify_streaming` package).
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MEDIA_EXT = {".wav", ".mp3", ".m4a", ".flac", ".aif", ".aiff", ".ogg",
             ".mp4", ".mov", ".m4v", ".webm", ".jpg", ".jpeg", ".png", ".webp"}
PACKAGE_ROOT = "music/packages/streaming"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=False).stdout


def tree(repo: Path, rev: str) -> dict[str, tuple[str, int]]:
    """path -> (mode, size) for every blob in `rev`'s tree."""
    out: dict[str, tuple[str, int]] = {}
    for line in _git(repo, "ls-tree", "-r", "-l", rev).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) < 4 or not path:
            continue
        out[path] = (parts[0], int(parts[3]))
    return out


def refs_carrying(repo: Path, rel: str) -> list[str]:
    """Refs whose tree contains `rel` (empty list when no ref does)."""
    hits = []
    for ref in _git(repo, "for-each-ref", "--format=%(refname:short)").splitlines():
        if not ref or ref == "HEAD":
            continue
        if rel in _git(repo, "ls-tree", "-r", "--name-only", ref).splitlines():
            hits.append(ref)
    return hits


def slug(title: str) -> str:
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", (title or "").lower()))


def manifest_paths(paths) -> list[str]:
    return sorted(p for p in paths
                  if p.startswith("campaigns/") and p.endswith("/MANIFEST.json"))


def named_files(data: dict, campaign: str) -> list[tuple[str, str]]:
    """(relpath, field) for every file the manifest names for one of its tracks."""
    out = []
    for track in data.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        for field in ("audio_file", "master_file", "source_mp4_file"):
            value = track.get(field)
            if isinstance(value, str) and value:
                out.append((f"{campaign}/{value}", field))
    return out


def inside(rel: str, root: str) -> bool:
    """True when `rel` stays under `root` (a manifest may not name ../../etc)."""
    return posixpath.normpath(rel).startswith(root.rstrip("/") + "/")


def run(repo: Path, rev: str | None, live: bool) -> int:
    use = rev or "HEAD"
    if not (repo / ".git").exists() and not _git(repo, "rev-parse", "--git-dir").strip():
        print(f"FAIL check_media_corpus_tracked: no git checkout at {repo}")
        return 3
    entries = tree(repo, use)
    if not entries:
        print(f"FAIL check_media_corpus_tracked: cannot read a tree at {use} in {repo}")
        return 3

    tracked = set(entries)
    problems: list[str] = []
    scanned: list[str] = []
    named_total = 0

    # ---- R1 / R2: the manifest's own claim about each track ---------------------
    for man in manifest_paths(tracked):
        campaign = posixpath.dirname(man)
        raw = _git(repo, "show", f"{use}:{man}")
        if not raw.strip():
            print(f"FAIL check_media_corpus_tracked: {man} is not readable at {use}")
            return 3
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            problems.append(f"R1 {man}: manifest is not JSON ({exc})")
            continue
        tracks = data.get("tracks")
        if not isinstance(tracks, list):
            continue
        for i, track in enumerate(tracks, 1):
            if not isinstance(track, dict):
                continue
            title = track.get("title") or f"track {i}"
            exported = bool(track.get("exported"))
            names = [(f, track.get(f)) for f in ("audio_file", "master_file", "source_mp4_file")]
            if not exported:
                named = [f for f, v in names if isinstance(v, str) and v]
                if named:
                    problems.append(
                        f"R1 {man}: track {i} ({title}) is not exported but still names "
                        f"{', '.join(named)} - a failed export names no file")
                s = slug(track.get("title", ""))
                if s:
                    for cand in (f"{campaign}/audio/{s}.wav", f"{campaign}/masters/{s}.wav",
                                 f"{campaign}/audio/{s}.mp4"):
                        if cand in tracked or (live and (repo / cand).exists()):
                            problems.append(
                                f"R2 {man}: track {i} ({title}) says exported=false, but "
                                f"{cand} exists - the record contradicts the disk")
                continue
            for field, value in names:
                if field == "source_mp4_file" and not value:
                    continue
                if not isinstance(value, str) or not value:
                    problems.append(
                        f"R1 {man}: track {i} ({title}) is exported=true but names no {field}")
                    continue
                named_total += 1
                rel = f"{campaign}/{value}"
                if not inside(rel, campaign):
                    problems.append(
                        f"R1 {man}: track {i} ({title}) names {value} outside {campaign}/")
                    continue
                if rel not in tracked:
                    carried = refs_carrying(repo, rel)
                    hint = (f" - carried by {', '.join(carried)}" if carried
                            else " - NO ref in this repo carries it")
                    problems.append(
                        f"R1 {man}: track {i} ({title}) names {rel}, which is not tracked "
                        f"at {use}{hint}")
                elif entries[rel][1] <= 0:
                    problems.append(f"R1 {rel}: tracked but zero bytes")
                elif field in ("audio_file", "master_file"):
                    scanned.append(rel)

    # ---- R3: a link is not media -------------------------------------------------
    for path, (mode, size) in sorted(entries.items()):
        if Path(path).suffix.lower() not in MEDIA_EXT:
            continue
        if not (path.startswith(PACKAGE_ROOT + "/")
                or re.match(r"^campaigns/[^/]+/(audio|masters)/", path)):
            continue
        if mode != "100644":
            kind = "SYMLINK" if mode == "120000" else f"mode {mode}"
            hint = f" -> {_git(repo, 'cat-file', '-p', f'{use}:{path}').strip()}" if mode == "120000" else ""
            problems.append(
                f"R3 {path}: tracked as {kind}, {size} B - git stores the target, not the "
                f"bytes{hint}")

    # ---- R4: media on disk that git does not hold (live checks only) -------------
    if live:
        dirs = [PACKAGE_ROOT]
        for man in manifest_paths(tracked):
            campaign = posixpath.dirname(man)
            dirs += [f"{campaign}/audio", f"{campaign}/masters"]
        for d in sorted(set(dirs)):
            base = repo / d
            if not base.is_dir():
                continue
            for p in sorted(base.rglob("*")):
                if not p.is_file() and not p.is_symlink():
                    continue
                if p.suffix.lower() not in MEDIA_EXT:
                    continue
                rel = str(p.relative_to(repo))
                if rel in tracked:
                    continue
                carried = refs_carrying(repo, rel)
                hint = (f" - carried by {', '.join(carried)}" if carried
                        else " - NO ref in this repo carries it")
                problems.append(
                    f"R4 {rel}: in the working tree, not tracked in HEAD{hint}")

    if problems:
        print("FAIL check_media_corpus_tracked: the campaign record and the repo disagree")
        for p in problems:
            print(f"  {p}")
        print("  Fix: commit the media the manifest names (the manifest is the record), "
              "or correct the manifest. Never re-extract media by hand: an untracked "
              "master is one `git clean` from gone.")
        return 1

    print(f"PASS check_media_corpus_tracked: {named_total} named media file(s) tracked "
          f"at {use}, no package symlink, no untracked media under "
          f"campaigns/*/{{audio,masters}} or {PACKAGE_ROOT}/")
    return 0


def selftest() -> int:
    """Build the incident in a throwaway repo and prove the check catches it."""
    tmp = Path(tempfile.mkdtemp(prefix="check_media_corpus_"))
    for cmd in (["init", "-q"], ["config", "user.email", "t@example.invalid"],
                ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(tmp), *cmd], capture_output=True, check=True)
    camp = tmp / "campaigns" / "demo"
    (camp / "audio").mkdir(parents=True)
    (camp / "masters").mkdir(parents=True)
    man = {"schema": "demo-v1", "tracks": [
        {"track_number": 1, "title": "Demo Song", "exported": True,
         "audio_file": "audio/demo-song.wav", "master_file": "masters/demo-song.wav"},
        {"track_number": 2, "title": "Failed Song", "exported": False,
         "audio_file": None, "master_file": None},
    ]}
    (camp / "MANIFEST.json").write_text(json.dumps(man, indent=2))
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-qm", "manifest only"],
                   capture_output=True, check=True)

    # R1: the manifest names two files git does not hold -> FAIL, and it must say so.
    rc = run(tmp, "HEAD", live=False)
    assert rc == 1, f"R1 must fail on a manifest that names files git does not hold (rc={rc})"

    # Now hold the bytes: R1 is satisfied and the check passes.
    (camp / "audio" / "demo-song.wav").write_bytes(b"RIFF....WAVE" + b"\0" * 64)
    (camp / "masters" / "demo-song.wav").write_bytes(b"RIFF....WAVE" + b"\0" * 128)
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-qm", "media"], capture_output=True, check=True)
    rc = run(tmp, "HEAD", live=False)
    assert rc == 0, f"a manifest whose files ARE tracked must pass (rc={rc})"

    # R3: a package that ships a symlink is not a package.
    pkg = tmp / PACKAGE_ROOT / "demo-pkg"
    pkg.mkdir(parents=True)
    (pkg / "master.wav").symlink_to("/nonexistent/scratch/test_master.wav")
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-qm", "symlink package"],
                   capture_output=True, check=True)
    rc = run(tmp, "HEAD", live=False)
    assert rc == 1, f"R3 must fail on a tracked symlink where media belongs (rc={rc})"

    # R2: a track that says the export failed, with the file on disk, is stale.
    (pkg / "master.wav").unlink()
    man["tracks"][1] = {"track_number": 2, "title": "Failed Song", "exported": False,
                        "audio_file": None, "master_file": None}
    (camp / "audio" / "failed-song.wav").write_bytes(b"RIFF....WAVE" + b"\0" * 32)
    (camp / "MANIFEST.json").write_text(json.dumps(man, indent=2))
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-qm", "stale failure record"],
                   capture_output=True, check=True)
    rc = run(tmp, "HEAD", live=False)
    assert rc == 1, f"R2 must fail on exported=false with the file present (rc={rc})"

    # R4: live check, media on disk that no commit holds.
    (camp / "masters" / "stray.wav").write_bytes(b"RIFF....WAVE" + b"\0" * 16)
    rc = run(tmp, "HEAD", live=True)
    assert rc == 1, f"R4 must fail on untracked media in the working tree (rc={rc})"

    print("selftest OK: R1 (manifest names a file git does not hold), R3 (symlink where "
          "media belongs), R2 (exported=false with the file present), R4 (untracked media "
          "on disk) each FAIL, and the corrected tree PASSes")
    return 0


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(
        description="The media a campaign record names must be tracked in the repo.")
    ap.add_argument("--repo", default=str(here.parents[2]))
    ap.add_argument("--rev", default=None,
                    help="read the manifest and the tree at this revision (default HEAD)")
    ap.add_argument("--check", action="store_true", help="the live check (the default)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    return run(Path(args.repo).resolve(), args.rev, live=args.rev is None)


if __name__ == "__main__":
    sys.exit(main())
