#!/usr/bin/env python3
"""music/stage_state.py — where does a GENRE's stage chain actually stand?

INCIDENT (2026-10-16, card t_6599927d)
--------------------------------------
`music/oracle.py` wrote one fixed stage marker into every card body it emitted:

    stage: brief

The oracle's dedupe guard is "one OPEN card per genre" (`open_oracle_genres`),
so a card that reaches `done` leaves the open set and the next wave re-emits the
genre — that part is by design. But the re-emitted card re-entered the brief
stage although the genre's brief already existed on disk. Measured 2026-10-16,
every one of the lane's 14 genres had a brief artifact:

    music/briefs/<genre>.md                    (12 genres)
    music/briefs/<genre>/<slug>/brief.md       (sentimental-piano, trance,
                                                elemental-air)

So the 13 cards of the 14:05 wave (`t_2c5b59f2` … `t_354d5d25`) each sent a
`music-producer` run back through the brief stage to rediscover a brief that was
already delivered — the same cost the 2026-10-09 twin cards paid one round
earlier (`t_05b640f6`, `t_1a6a7d74`, …). Briefs in this lane are keyed by GENRE,
so both cards of a twin pair resolve to ONE artifact.

THE RULE
--------
A card must start at the FIRST stage of `music/stages.yaml` whose output is not
on disk. The stage ORDER comes from `music/stages.yaml` — the same file that
declares it — read at call time, so adding, removing or reordering a stage needs
no edit here (the decision shape recorded on card t_6599927d: the emitter may
position a card only if it can read the order from the declaring file).

Only stages whose output this module can MEASURE declare a proof (`PROOFS`). A
stage with no declared proof counts as UNPROVED, and that direction is the whole
safety argument: the walk stops at the first stage it cannot clear, so this rule
can never skip work that has not actually been done. Today that bounds every
answer to:

    no brief artifact   -> brief          (the chain has not started)
    brief artifact      -> genre-select   (brief is delivered)

`genre-select` declares no proof because it produces no artifact — it resolves
and verifies the registry entry. A chain therefore cannot be resumed past it by
this rule. That limitation is DELIBERATE and recorded in
`brain/playbooks/music-lane-architecture.md` §4.2: resuming past a stage that
leaves no artifact needs the board's own advance marker, which is the driver /
stage-semantics decision on card t_2eaa39ba, not this rule's to guess.

ONE RULE, THREE CALLERS — do not re-implement it anywhere:
  * `music/oracle.py`                      -> the `stage:` marker in a card body
  * the `brief` stage prompt (`music/stages.yaml`) -> idempotency: a brief that
    already exists is verified and the card advances, with no writing work
  * `music/scripts/check_oracle_board.py`  -> invariant B3 (no open card sits
    behind its genre's resume stage)

cited: t_6599927d (this rule) · t_bf0e5edd (one open card per genre) ·
       t_5a93164a (advance channel) · t_2eaa39ba (§4 board ownership, open)

Usage:
  /usr/bin/python3 music/stage_state.py --genre <genre> [--repo DIR]
  /usr/bin/python3 music/test_stage_state.py

Exit codes: 0 = resolved, 2 = could not resolve (missing / empty stages.yaml,
unknown argument). A failure is LOUD: the caller must never fall back to a
hard-coded stage, which is exactly the defect above.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MUSIC_DIR = Path(__file__).resolve().parent
REPO = MUSIC_DIR.parent
STAGES_YAML = MUSIC_DIR / "stages.yaml"

# ── Proofs ──────────────────────────────────────────────────────────────────
# stage -> glob patterns, relative to the repo root, `{genre}` substituted.
# A pattern proves the stage PRODUCED for that genre. Only what this lane can
# measure on disk is declared:
#
#   brief  : a brief is keyed by genre — `music/briefs/<genre>.md`, or
#            `music/briefs/<genre>/<slug>/brief.md`. The same convention
#            music/scripts/check_brief_bpm_solutions.py::genre_of() encodes.
#   lyrics : the gated lyric sheet. `gate_lyrics_original.py --track-dir` reads
#            `<track dir>/lyrics.suno.txt`, so that file is the proof — not the
#            bare directory, which `generate` and later stages also write into.
#
# NOT declared (unprovable, so the walk stops there): genre-select (no artifact),
# generate, curate, stems, master, gate, package, visual, publish, track.
PROOFS: dict[str, tuple[str, ...]] = {
    "brief": ("music/briefs/{genre}.md", "music/briefs/{genre}/*/brief.md"),
    "lyrics": ("music/lyrics/{genre}/*/lyrics.suno.txt",),
}


class StageStateError(RuntimeError):
    """The lane's stage state cannot be resolved. Never guess — fail loud."""


def _load_doc(path: Path | str) -> dict:
    """Read the stage map. One reader, so the order and the gates never diverge."""
    path = Path(path)
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - the driver resolves this too
        raise StageStateError(
            f"this interpreter has no PyYAML, so {path} cannot be read; "
            f"re-run with /usr/bin/python3 (the interpreter the lane's "
            f"checks and the pipeline driver's config parse use)") from exc
    if not path.is_file():
        raise StageStateError(f"no stage map at {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise StageStateError(f"{path} is not a stage map (expected a mapping)")
    return doc


def load_stage_order(path: Path | str = STAGES_YAML) -> list[str]:
    """The declared stage order, in file order, from stages.yaml."""
    entries = [e for e in (_load_doc(path).get("stages") or []) if isinstance(e, dict)]
    order = [str(e["stage"]) for e in entries if e.get("stage")]
    if not order:
        raise StageStateError(f"{path} declares no stages — the stage order is unknown")
    return order


def human_gates(path: Path | str = STAGES_YAML) -> set[str]:
    """Stages flagged `human_gate: true` — never auto-dispatched."""
    return {
        str(e["stage"])
        for e in (_load_doc(path).get("stages") or [])
        if isinstance(e, dict) and e.get("stage") and e.get("human_gate")
    }


def default_stage(path: Path | str = STAGES_YAML) -> str:
    """`default_stage:` — the stage a card with NO marker is read as.

    The pipeline driver reads the same key for its own fallback, so a card with
    no marker yet and this module agree on where the card stands.
    """
    value = _load_doc(path).get("default_stage")
    if not value:
        raise StageStateError(f"{path} declares no default_stage")
    return str(value)


def proved_stages(repo: Path | str, genre: str) -> dict[str, list[str]]:
    """stage -> the existing artifacts that prove the stage produced for `genre`."""
    repo = Path(repo)
    out: dict[str, list[str]] = {}
    for stage, patterns in PROOFS.items():
        hits: list[str] = []
        for pattern in patterns:
            for path in sorted(repo.glob(pattern.format(genre=genre))):
                if path.is_file():
                    hits.append(str(path.relative_to(repo)))
        if hits:
            out[stage] = hits
    return out


def resume_stage(repo: Path | str = REPO, genre: str = "",
                 stages_yaml: Path | str = STAGES_YAML) -> tuple[str, dict]:
    """The stage a new card for `genre` must start at, plus its evidence.

    The first stage in the declared order with no proof on disk. The order AND
    the human gates come from `stages_yaml` (default: the lane's `stages.yaml`),
    so a reordered or extended stage list moves the answer with it and this
    module carries no stage list of its own.

    A human gate declares no proof (nothing produces it), so a fully delivered
    chain stops at the first human gate in the order — which is right: the
    outstanding step is then j_kro's approval and the card parks.

    Returns (stage, evidence); evidence carries the proved artifacts, the first
    unproved stage, the walked order and the declared human gates. Raises
    StageStateError rather than guessing.
    """
    if not genre or "/" in genre or genre.strip() != genre:
        raise StageStateError(f"not a genre name: {genre!r}")
    order = load_stage_order(stages_yaml)
    proved = proved_stages(repo, genre)
    gates = sorted(human_gates(stages_yaml))
    for stage in order:
        if stage not in proved:
            return stage, {"genre": genre, "proved": proved, "unproved": stage,
                           "order": order, "gates": gates, "chain_complete": False,
                           "stages_yaml": str(stages_yaml)}
    # Every declared stage is proved. A human gate is never proved (nothing
    # produces it), so the walk above returns at the first gate whenever the
    # declared order holds one; this arm is the no-gate case.
    return order[-1], {"genre": genre, "proved": proved, "unproved": None,
                       "order": order, "gates": gates, "chain_complete": True,
                       "stages_yaml": str(stages_yaml)}


def resume_note(stage: str, evidence: dict) -> str:
    """One sentence for a card body: why this card starts at `stage`."""
    proved = evidence.get("proved") or {}
    if evidence.get("chain_complete"):
        return (f"Every declared stage already has its artifact on disk for this genre, "
                f"so the card resumes at the terminal stage `{stage}` "
                f"(music/stage_state.py; card t_6599927d).")
    if stage in (evidence.get("gates") or []):
        return (f"Every stage that declares an artifact is already on disk, so the only "
                f"step left is the human gate `{stage}` — the card parks for j_kro "
                f"(music/stage_state.py; card t_6599927d).")
    if not proved:
        return (f"No artifact for this genre is on disk yet, so the chain starts at "
                f"`{stage}` (music/stage_state.py; card t_6599927d).")
    listed = "; ".join(f"{s} -> {', '.join(paths)}" for s, paths in sorted(proved.items()))
    return (f"Already delivered for this genre: {listed}. `{stage}` is the first stage "
            f"with no artifact on disk, so this card does NOT start at `brief` again "
            f"(music/stage_state.py; card t_6599927d).")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Resolve which stage a new card for a genre must start at.")
    ap.add_argument("--genre", required=False, help="genre key (music/genres.yaml)")
    ap.add_argument("--repo", default=str(REPO), help="repo root (default: this lane)")
    args = ap.parse_args(argv)

    if not args.genre:
        print("usage: stage_state.py --genre <genre> [--repo DIR]", file=sys.stderr)
        return 2

    try:
        stage, ev = resume_stage(args.repo, args.genre)
    except StageStateError as exc:
        print(f"FATAL stage_state: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"repo    : {Path(args.repo).resolve()}")
    print(f"genre   : {args.genre}")
    print(f"order   : {', '.join(ev['order'])}")
    print(f"          (declared by {ev['stages_yaml']})")
    if ev["proved"]:
        for proved_stage, paths in sorted(ev["proved"].items()):
            for path in paths:
                print(f"proved  : {proved_stage} -> {path}")
    else:
        print("proved  : nothing — no declared artifact exists for this genre")
    if ev["unproved"]:
        print(f"unproved: {ev['unproved']} (no proof on disk)")
    else:
        print("unproved: every stage is proved; the chain is at its human gate")
    print(f"resume  : {stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
