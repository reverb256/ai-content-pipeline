#!/usr/bin/env python3
"""check_brief_rubric_scope — FAIL when a brief's DECLARED scoring scope disagrees with the live rubric.

WHY THIS EXISTS
---------------
INCIDENT (2026-10-16, card t_1a5b018b; rubric change 56dc465, card t_426a82a3)

`music/rubrics/gamer.json` v1 carried five criteria, no `applies_to` anywhere and **Σw = 11**: the
sub-idiom scope lived only inside a criterion NAME (`Boss/battle energy (elemental-*, epic-orchestral-boss)`).
v2 (56dc465) carries six criteria, `applies_to` on every one, and **Σw = 8 per genre** — each
elemental scores its own craft criterion, `loop_safety`, `asset_packaging`, `loudness_target` and
nothing else.

Three brief sections kept reasoning from the v1 file after that change and sat stale for hours:
`music/briefs/elemental-water.md` §8, `music/briefs/elemental-air/above-the-weather/brief.md` §10
and `music/briefs/elemental-earth.md` §9/§14 (reconciled by 7d3d440, fb612c4, 5f66576 and 2dac605).
Every standing brief check passed the whole time, because not one of them compares a brief's stated
criterion set, weights or reject signals to the live rubric:

    check_brief_figures.py    figures that carry a UNIT and a named artifact     no
    check_brief_drift.py      commit divergence, blueprint census                no
    check_brief_line_refs.py  `file:line` citations resolve                      no
    check_brief_absence.py    "path is absent" claims                            no

A brief is the evidence artifact a human reads before approving a track, so a brief that quotes a
rubric the repo no longer ships is worse than a missing sentence: it is a false record.

WHAT IT DOES — it EXECUTES the artifact, it does not grep for a feature name
---------------------------------------------------------------------------
This lane's rule 5: "Gates must EXECUTE the artifact. A gate that greps a file for a feature name
is a defect." So this check does NOT ask "does the brief mention `applies_to`". It reads the brief's
machine-readable declaration and compares it, field by field, to the truth COMPUTED from the live
rubric by the panel's own resolver:

    panel.applicable_criteria(rubric, genre)   music/rubrics/panel.py:315
    panel.applicable_signals(rubric, genre)    music/rubrics/panel.py:338
    panel._in_scope(...)                       music/rubrics/panel.py:305  ("the one place")
    rubric["pass_threshold"], rubric["version"]

genre -> family is read through `music/registry.py` (`load_genres(load_lanes())`), never by parsing
genres.yaml by hand. `--rubric-dir` repoints panel.load_rubric at another directory, which is how a
PRE-FIX rubric is tested against HEAD's briefs (see PROOF in the completion record for this card).

THE DECLARATION (mechanism (a) of the card that filed this work)
----------------------------------------------------------------
A covered brief carries exactly ONE fenced ```json block whose object has a `rubric_scope` key:

    ```json
    {"rubric_scope": {
      "genre": "elemental-water", "family": "gamer", "rubric_version": 2,
      "pass_threshold": 7.0,
      "criteria": ["elemental_atmosphere", "loop_safety", "asset_packaging", "loudness_target"],
      "weights": {"elemental_atmosphere": 3, "loop_safety": 3, "asset_packaging": 1,
                  "loudness_target": 1},
      "weight_sum": 8,
      "reject_signals": ["elemental_fight_material", "loop_fade_or_truncation", "clipped_master",
                         "no_stated_tempo_key"],
      "reject_signals_unnamed": 0}}
    ```

Every field is a claim about NOW and is recomputed. `--print-truth <genre>` prints this block,
already correct, for the live rubric — the remedy is one command, not a hand-edit.

  * `criteria` / `weights` / `weight_sum` — the applicable set and its arithmetic for THIS genre.
  * `reject_signals` — the ids of the applicable signals that the rubric identifies (`id`).
  * `reject_signals_unnamed` — how many applicable signals the rubric does NOT identify by id
    (a bare string, or a dict with no `id`). Those cannot be named, but a change in how many of
    them apply still has to show. gamer has none; edm names none of its five; anisong names two
    of its five.
  * `rubric_version` — the version this block was reconciled against. A rubric bump re-stales a
    brief's prose (that is exactly this incident), so a version mismatch is a finding, not a
    warning: re-read the section that quotes the rubric and re-stamp the block.

COVERAGE — which briefs must declare, decided from the rubric data, not from a list in this file
------------------------------------------------------------------------------------------------
A brief is COVERED when EITHER side says scope is data:

  * its own path names a registry genre whose family rubric carries per-genre scope data (an
    `applies_to` key on any criterion or reject signal), or
  * the brief carries a `rubric_scope` block.

Measured 2026-10-16: gamer, edm and anisong carry the data (10 briefs); acoustic, ambient, utility
and vocal do not — each of those rubrics has one genre and no scope data, so every genre in the
family scores the same set and there is nothing for a declaration to disagree with. Those briefs
are SKIPPED and printed.

Both halves are load-bearing, and the second one was added after a test found the hole:

  * A covered brief with NO block is a finding, never a silent pass. A check that only verifies
    declarations that happen to exist is opt-in, and opt-in is how the stale sections survived
    four checks in the first place.
  * A brief that CARRIES a block stays covered even if the rubric stops declaring `applies_to`.
    Without that half, running this check against the PRE-FIX gamer rubric (v1, no `applies_to`)
    made all six gamer briefs uncovered and the run PASSED — the check went quiet exactly when the
    rubric had moved out from under them. Measured while writing this: `--rubric-dir` on v1 printed
    `PASS ... 4 declaration(s) across 4 covered brief(s)`. A disappearing `applies_to` is a rubric
    change like any other, and the brief holding the claim is the one that must fail.

HISTORY MUST NOT FAIL — and here that is a property, not a rule to remember
---------------------------------------------------------------------------
The sibling checks skip a claim ANCHORED to a revision or a clock time on the same line, because an
anchored historical count is a fact and an unanchored one is a claim about now
(`check_brief_drift.py` rule 3, `check_brief_line_refs.py` rule 3). This check never reads prose at
all: the declaration is the brief's statement about now, and the pre-fix record around it — "v1",
"56dc465^", "pre-fix", "superseded", "Σw = 11", "41/11 = 3.73", a `HH:MM` stamp — is history and
stays passing (proved at HEAD on the three incident briefs, and in `--selftest` case
"prose history is not read"). The consequence is deliberate: there is NO anchoring escape hatch
inside a `rubric_scope` block. A brief that wants to record an old scope writes it in prose, where
a reader can see what it is; a block that carried a pre-fix number would be a claim the panel no
longer honours.

Exit codes: 0 = every covered brief's declaration matches the live rubric, 1 = at least one
finding, 2 = usage error or this check cannot compute (registry/panel/rubric unreadable).

Usage:
  /usr/bin/python3 music/scripts/check_brief_rubric_scope.py
  /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --rev 7d3d440^
  /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --rubric-dir /tmp/prefix-rubrics
  /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth elemental-water
  /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --briefs music/briefs/elemental-water.md
  /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --selftest

Run it with `/usr/bin/python3` (the Hermes-managed `python3` does not carry numpy/PyYAML, and
panel.py imports both).

Related checks (deliberately not duplicated here)
-------------------------------------------------
  * `music/scripts/check_brief_figures.py`  — figures WITH a unit and a named artifact.
  * `music/scripts/check_brief_drift.py`    — commit divergence and the blueprint census.
  * `music/scripts/check_brief_absence.py`  — "path is absent" claims.
  * `music/rubrics/test_panel_math.py`      — the rubric's own invariants
    (`rubric_scope_defects()`, the pre-fix arithmetic case). That one guards the DATA; this one
    guards the brief that quotes it.

cited: t_1a5b018b (this incident), t_426a82a3 (the rubric fix, 56dc465), t_00ac4f10 (this card),
7d3d440 / fb612c4 / 5f66576 / 2dac605 (the three reconciled sections), t_207dc413 (the runner that
has to call this), t_354d5d25 / t_8fa97d4e / t_dd248457 (the surviving-card passes).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BRIEF_GLOB = "music/briefs/**/*.md"
MARKER = "rubric_scope"
FENCE = "```"

DECL_KEYS = ("genre", "family", "rubric_version", "pass_threshold", "criteria", "weights",
             "weight_sum", "reject_signals", "reject_signals_unnamed")

TAG = "[STALE RUBRIC SCOPE]"


# ── truth, computed from the live rubric by the panel's own resolver ───────────

class CannotCompute(Exception):
    """This check cannot read the registry, the panel or a rubric. rc 2, never a silent pass."""


def load_registry_genres(repo: Path) -> dict:
    """genre -> spec, through music/registry.py (never a hand-rolled YAML read).

    `registry.load_genres(load_lanes())` and not `load_registry()`: the full registry load also
    validates stage gates and derived products, which belong to other checks. A broken asset-pack
    stage must not turn this check red — that is a false finding on someone else's surface.
    """
    music = repo / "music"
    if not (music / "genres.yaml").is_file():
        raise CannotCompute(f"no music/genres.yaml under {repo}")
    sys.path.insert(0, str(music))
    try:
        import registry  # noqa: PLC0415
    except ImportError as exc:  # PyYAML
        raise CannotCompute(f"music/registry.py is not importable: {exc}") from exc
    try:
        return registry.load_genres(registry.load_lanes())
    except Exception as exc:  # registry.RegistryError and anything it raises
        raise CannotCompute(f"music/registry.py refused the registry: {exc}") from exc


def load_panel(repo: Path, rubric_dir: Path | None):
    """The panel module, by file path (music/rubrics is not a package). Its RUBRICS constant is
    the only place the rubric directory is decided, so `--rubric-dir` repoints it and the
    computation stays panel.load_rubric + applicable_criteria + applicable_signals."""
    path = repo / "music" / "rubrics" / "panel.py"
    if not path.is_file():
        raise CannotCompute(f"no panel module at {path}")
    spec = importlib.util.spec_from_file_location("music_rubric_panel", path)
    if spec is None or spec.loader is None:
        raise CannotCompute(f"panel module at {path} will not load")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:  # numpy/yaml
        raise CannotCompute(f"music/rubrics/panel.py is not importable: {exc}") from exc
    if rubric_dir is not None:
        module.RUBRICS = Path(rubric_dir)
    return module


def family_has_scope(rubric: dict) -> bool:
    """True when the rubric declares per-genre scope as data (an `applies_to` key anywhere).

    This is the coverage rule, and it is read off the rubric rather than listed in this file: when
    a family starts scoping criteria by genre, its briefs start being covered, with no edit here.
    """
    for c in rubric.get("criteria") or []:
        if isinstance(c, dict) and "applies_to" in c:
            return True
    for s in rubric.get("reject_signals") or []:
        if isinstance(s, dict) and "applies_to" in s:
            return True
    return False


def truth_for(panel, genres: dict, genre: str) -> dict:
    """The scoring scope the LIVE rubric gives one genre. Every field here is recomputed."""
    rubric = panel.load_rubric(genres[genre]["family"])
    criteria = panel.applicable_criteria(rubric, genre)
    signals = rubric.get("reject_signals") or []
    scoped_entries = [
        s for s in signals
        if panel._in_scope(s.get("applies_to") if isinstance(s, dict) else None, genre)
    ]
    named = [s["id"] for s in scoped_entries
             if isinstance(s, dict) and isinstance(s.get("id"), str) and s["id"].strip()]
    applicable_texts = panel.applicable_signals(rubric, genre)
    weights = {c["id"]: c.get("weight") for c in criteria}
    return {
        "genre": genre,
        "family": genres[genre]["family"],
        "rubric_rel": f"music/rubrics/{genres[genre]['family']}.json",
        "rubric_version": rubric.get("version"),
        "pass_threshold": rubric.get("pass_threshold"),
        "criteria": [c["id"] for c in criteria],
        "weights": weights,
        "weight_sum": sum(w for w in weights.values() if isinstance(w, int)),
        "reject_signals": named,
        "reject_signals_unnamed": len(scoped_entries) - len(named),
        "applicable_texts": len(applicable_texts),
        "scoped": family_has_scope(rubric),
    }


# ── the declaration block ─────────────────────────────────────────────────────

def fenced_blocks(lines: list[str]) -> list[tuple[int, str, str]]:
    """[(opening line number, info string, body)] for every closed ``` fence."""
    out: list[tuple[int, str, str]] = []
    start, info, body = 0, "", None
    for lineno, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith(FENCE):
            if body is None:
                start, info, body = lineno, stripped[3:].strip(), []
            else:
                out.append((start, info, "\n".join(body)))
                body = None
        elif body is not None:
            body.append(line)
    return out


def declarations(text: str) -> list[tuple[int, dict | None, str | None]]:
    """[(line, declared object, parse error)] for fenced blocks carrying the `rubric_scope` marker.

    A fence whose text mentions the marker but does not parse is REPORTED (a block that looks like
    the declaration and cannot be read is a defect, not something to skip silently). A fence that
    parses without the marker is somebody else's JSON and is ignored.
    """
    out: list[tuple[int, dict | None, str | None]] = []
    for start, _info, body in fenced_blocks(text.splitlines()):
        if MARKER not in body:
            continue
        try:
            obj = json.loads(body)
        except ValueError as exc:
            out.append((start, None, str(exc)))
            continue
        if isinstance(obj, dict) and MARKER in obj:
            out.append((start, obj[MARKER], None))
    return out


def print_truth_block(truth: dict) -> str:
    """The declaration block, already correct, as it should appear in a brief."""
    decl = {
        "genre": truth["genre"],
        "family": truth["family"],
        "rubric_version": truth["rubric_version"],
        "pass_threshold": truth["pass_threshold"],
        "criteria": truth["criteria"],
        "weights": truth["weights"],
        "weight_sum": truth["weight_sum"],
        "reject_signals": truth["reject_signals"],
        "reject_signals_unnamed": truth["reject_signals_unnamed"],
    }
    body = json.dumps({MARKER: decl}, indent=2, ensure_ascii=False)
    return f"```json\n{body}\n```"


# ── the comparison (pure, so --selftest can drive every branch) ───────────────

def compare(decl, truth: dict) -> list[str]:
    """Every way one declaration can disagree with the computed truth. [] = agrees."""
    if not isinstance(decl, dict):
        return [f"the {MARKER} block must be a JSON object, got {type(decl).__name__}"]

    findings: list[str] = []
    absent = [k for k in DECL_KEYS if k not in decl]
    if absent:
        findings.append("the block does not carry " +
                        ", ".join(f"'{k}'" for k in absent))

    d_genre = decl.get("genre")
    if isinstance(d_genre, str) and d_genre != truth["genre"]:
        findings.append(f"genre {d_genre!r} — this brief is filed for the genre "
                        f"{truth['genre']!r}")
    d_family = decl.get("family")
    if isinstance(d_family, str) and d_family != truth["family"]:
        findings.append(f"family {d_family!r} — the live family of genre {truth['genre']!r} is "
                        f"{truth['family']!r} ({truth['rubric_rel']})")
    d_version = decl.get("rubric_version")
    if isinstance(d_version, int) and d_version != truth["rubric_version"]:
        findings.append(f"rubric_version {d_version} — {truth['rubric_rel']} is version "
                        f"{truth['rubric_version']}; this block was reconciled against an older "
                        f"file. Recompute the block and re-read the prose that quotes the rubric")
    d_threshold = decl.get("pass_threshold")
    if isinstance(d_threshold, (int, float)) and not isinstance(d_threshold, bool) \
            and d_threshold != truth["pass_threshold"]:
        findings.append(f"pass_threshold {d_threshold} — live {truth['pass_threshold']}")

    d_criteria = decl.get("criteria")
    if isinstance(d_criteria, list):
        claimed = [c for c in d_criteria if isinstance(c, str)]
        missing = [c for c in truth["criteria"] if c not in claimed]
        extra = [c for c in claimed if c not in truth["criteria"]]
        if missing:
            findings.append(f"criteria: does not list {', '.join(missing)} — the live rubric scores "
                            f"it for this genre")
        if extra:
            findings.append(f"criteria: lists {', '.join(extra)}, which the live rubric does not "
                            f"score for this genre")

    d_weights = decl.get("weights")
    if isinstance(d_weights, dict):
        for cid in truth["criteria"]:
            if cid in d_weights and d_weights[cid] != truth["weights"][cid]:
                findings.append(f"weights: {cid} declared {d_weights[cid]!r}, live "
                                f"{truth['weights'][cid]}")

    if isinstance(d_criteria, list) and isinstance(d_weights, dict):
        left = sorted(c for c in d_criteria if isinstance(c, str))
        right = sorted(k for k in d_weights if isinstance(k, str))
        if left != right:
            findings.append(f"the block disagrees with itself: criteria {left} vs weights {right}")

    d_sum = decl.get("weight_sum")
    if isinstance(d_sum, int) and not isinstance(d_sum, bool) and d_sum != truth["weight_sum"]:
        findings.append(f"weight_sum {d_sum} — live {truth['weight_sum']} (the weights the live "
                        f"rubric scores for this genre)")

    d_signals = decl.get("reject_signals")
    if isinstance(d_signals, list):
        claimed = [s for s in d_signals if isinstance(s, str)]
        missing = [s for s in truth["reject_signals"] if s not in claimed]
        extra = [s for s in claimed if s not in truth["reject_signals"]]
        if missing:
            findings.append(f"reject_signals: does not list {', '.join(missing)} — the live rubric "
                            f"applies it to this genre")
        if extra:
            findings.append(f"reject_signals: lists {', '.join(extra)}, which the live rubric does "
                            f"not apply to this genre")

    d_unnamed = decl.get("reject_signals_unnamed")
    if isinstance(d_unnamed, int) and not isinstance(d_unnamed, bool) \
            and d_unnamed != truth["reject_signals_unnamed"]:
        findings.append(f"reject_signals_unnamed {d_unnamed} — live "
                        f"{truth['reject_signals_unnamed']} (applicable reject signals the rubric "
                        f"does not identify by id)")

    return findings


def check_text(label: str, text: str, truth: dict, required: bool = True) -> tuple[list[str], int]:
    """(findings, declarations checked) for one brief's text against one genre's truth."""
    found = declarations(text)
    if not found:
        if not required:
            return [], 0
        return ([f"{label}  no {MARKER} block — family {truth['family']} scopes criteria per genre "
                 f"({truth['rubric_rel']} carries `applies_to`), so a brief of this family must "
                 f"declare its scoring scope as data  {TAG}"], 0)
    if len(found) > 1:
        where = ", ".join(f"line {lineno}" for lineno, _o, _e in found)
        return ([f"{label}:{found[0][0]}  {len(found)} {MARKER} blocks ({where}) — exactly one is "
                 f"read, so the rest can silently disagree  {TAG}"], 0)
    lineno, decl, error = found[0]
    if error is not None:
        return ([f"{label}:{lineno}  the {MARKER} block does not parse as JSON: {error}  {TAG}"], 0)
    anomalies = []
    if truth["applicable_texts"] != len(truth["reject_signals"]) + truth["reject_signals_unnamed"]:
        # The panel's own two resolvers must agree on how many reject signals apply.
        anomalies.append(
            f"{label}:{lineno}  {truth['rubric_rel']}: panel.applicable_signals() returns "
            f"{truth['applicable_texts']} signal(s) for {truth['genre']} while the scope entries "
            f"say {len(truth['reject_signals']) + truth['reject_signals_unnamed']} — the rubric's "
            f"reject-signal data needs the review panel's attention (card t_426a82a3 surface)  "
            f"{TAG}")
    for msg in compare(decl, truth):
        anomalies.append(f"{label}:{lineno}  {msg}  {TAG}")
    return anomalies, 1


# ── the brief set ─────────────────────────────────────────────────────────────

def brief_genre(rel: str) -> str | None:
    """The registry genre id a brief path names, or None.

    `music/briefs/<genre>.md` and `music/briefs/<genre>/<track>/brief.md` are the two shapes this
    lane uses. The rule is mechanical (the first path component under music/briefs), so nothing
    here guesses which genre a brief is about.
    """
    parts = Path(rel).parts
    if len(parts) < 3 or parts[0] != "music" or parts[1] != "briefs":
        return None
    head = parts[2]
    return head[:-3] if len(parts) == 3 and head.endswith(".md") else head


def briefs_worktree(repo: Path) -> list[str]:
    return sorted(str(p.relative_to(repo)) for p in repo.glob(BRIEF_GLOB) if p.is_file())


def briefs_rev(repo: Path, rev: str) -> list[str]:
    res = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", rev],
                         capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise CannotCompute(f"FATAL: {rev} is not a revision in {repo}")
    return sorted(f for f in res.stdout.splitlines()
                  if f.startswith("music/briefs/") and f.endswith(".md"))


def read(repo: Path, rel: str, rev: str | None) -> str:
    if rev:
        res = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"],
                             capture_output=True, text=True, check=False)
        return res.stdout if res.returncode == 0 else ""
    return (repo / rel).read_text(encoding="utf-8")


# ── selftest ──────────────────────────────────────────────────────────────────

GAMER_WATER = {
    "genre": "elemental-water",
    "family": "gamer",
    "rubric_rel": "music/rubrics/gamer.json",
    "rubric_version": 2,
    "pass_threshold": 7.0,
    "criteria": ["elemental_atmosphere", "loop_safety", "asset_packaging", "loudness_target"],
    "weights": {"elemental_atmosphere": 3, "loop_safety": 3, "asset_packaging": 1,
                "loudness_target": 1},
    "weight_sum": 8,
    "reject_signals": ["elemental_fight_material", "loop_fade_or_truncation", "clipped_master",
                       "no_stated_tempo_key"],
    "reject_signals_unnamed": 0,
    "applicable_texts": 4,
    "scoped": True,
}

V2_BLOCK = {
    "rubric_scope": {
        "genre": "elemental-water",
        "family": "gamer",
        "rubric_version": 2,
        "pass_threshold": 7.0,
        "criteria": ["elemental_atmosphere", "loop_safety", "asset_packaging", "loudness_target"],
        "weights": {"elemental_atmosphere": 3, "loop_safety": 3, "asset_packaging": 1,
                    "loudness_target": 1},
        "weight_sum": 8,
        "reject_signals": ["elemental_fight_material", "loop_fade_or_truncation", "clipped_master",
                           "no_stated_tempo_key"],
        "reject_signals_unnamed": 0,
    }
}

# The PRE-FIX declaration: what the stale sections asserted, written as data. This is the case the
# check exists for — it must fail, and it must name what moved.
PREFIX_BLOCK = {
    "rubric_scope": {
        "genre": "elemental-water",
        "family": "gamer",
        "rubric_version": 1,
        "pass_threshold": 7.0,
        "criteria": ["chip_timbre_authenticity", "battle_energy", "loop_safety",
                     "asset_packaging", "loudness_target"],
        "weights": {"chip_timbre_authenticity": 3, "battle_energy": 3, "loop_safety": 3,
                    "asset_packaging": 1, "loudness_target": 1},
        "weight_sum": 11,
        "reject_signals": [],
        "reject_signals_unnamed": 5,
    }
}


def _block(obj: dict) -> str:
    return "```json\n" + json.dumps(obj, indent=2) + "\n```\n"


def selftest() -> int:
    """Every branch of the comparison, plus the two escapes that matter: prose history is not
    read, and an unscoped family needs no declaration. Combinations are built from the block
    shapes above, with one field changed (or dropped) per case."""
    def mutate(**kw):
        decl = json.loads(json.dumps(V2_BLOCK))
        decl["rubric_scope"].update(kw)
        return _block(decl)

    def drop(key):
        decl = json.loads(json.dumps(V2_BLOCK))
        del decl["rubric_scope"][key]
        return _block(decl)

    prefix = _block(PREFIX_BLOCK)
    good = _block(V2_BLOCK)
    history_prose = (
        "**What was broken — the pre-fix record, kept as evidence.** `git show 56dc465^:"
        "music/rubrics/gamer.json` -> version 1, five criteria and no `applies_to`:\n\n"
        "| v1 criterion | Weight | Scope as that file wrote it |\n|---|---|---|\n"
        "| `battle_energy` | 3 | name `Boss/battle energy (elemental-*, epic-orchestral-boss)` |\n\n"
        "**Σw = 11**, and the panel scored all five on every gamer genre. The measured consequence, "
        "kept as the incident record: a correct 92 BPM `elemental-air` track scored **41/11 = 3.73** "
        "against the 7.0 threshold (superseded; measured 16:07 CDT).\n\n"
        "```\nNon-battle scope (loop 3 + packaging 1 + loudness 1 = weight 5, need 35 pts)\n```\n\n")

    cases: list[tuple[str, str, bool, int]] = [
        # name, text, required, want findings
        ("current declaration passes", good, True, 0),
        ("no declaration in a covered family FAILS", "## 8. Rubric\n\nprose only\n", True, 1),
        ("no declaration is fine in an unscoped family", "## 8. Rubric\n", False, 0),
        ("prose history is not read", history_prose + good, True, 0),
        ("a second block is a finding", good + good, True, 1),
        ("a block that does not parse is a finding",
         "```json\n{\"rubric_scope\": {\"genre\": \"elemental-water\",}\n```\n", True, 1),
        ("other JSON without the marker is ignored",
         "```json\n{\"note\": \"not a declaration\"}\n```\n" + good, True, 0),
        ("pre-fix declaration FAILS (the incident)", prefix, True, 6),
        ("wrong family", mutate(family="edm"), True, 1),
        ("stale rubric version", mutate(rubric_version=1), True, 1),
        ("stale pass_threshold", mutate(pass_threshold=6.5), True, 1),
        ("missing an applicable criterion",
         mutate(criteria=["loop_safety", "asset_packaging", "loudness_target"],
                weights={"loop_safety": 3, "asset_packaging": 1, "loudness_target": 1},
                weight_sum=5), True, 2),
        ("an out-of-scope criterion is listed",
         mutate(criteria=["elemental_atmosphere", "loop_safety", "asset_packaging",
                          "loudness_target", "battle_energy"],
                weights={"elemental_atmosphere": 3, "loop_safety": 3, "asset_packaging": 1,
                         "loudness_target": 1, "battle_energy": 3},
                weight_sum=11), True, 2),
        ("a changed weight", mutate(weights={"elemental_atmosphere": 2, "loop_safety": 3,
                                             "asset_packaging": 1, "loudness_target": 1},
                                    weight_sum=7), True, 2),
        ("criteria and weights disagree with each other",
         mutate(weights={"elemental_atmosphere": 3, "loop_safety": 3, "asset_packaging": 1}),
         True, 1),
        ("a reject signal that does not apply",
         mutate(reject_signals=["elemental_fight_material", "loop_fade_or_truncation",
                                "clipped_master", "no_stated_tempo_key",
                                "battle_no_fast_tempo"]), True, 1),
        ("unnamed reject-signal count drift", mutate(reject_signals_unnamed=5), True, 1),
        ("a field the block does not carry", drop("weight_sum"), True, 1),
    ]

    failures: list[str] = []
    for name, text, required, want in cases:
        findings, checked = check_text("fixture.md", text, GAMER_WATER, required=required)
        if len(findings) != want:
            failures.append(f"  {name}: want {want} finding(s), got {len(findings)}")
            for f in findings:
                failures.append(f"      {f}")
        if name in ("current declaration passes", "prose history is not read",
                    "other JSON without the marker is ignored") and checked != 1:
            failures.append(f"  {name}: want 1 declaration checked, got {checked}")

    # the pre-fix case must name what moved, not just count
    pre_findings, pre_checked = check_text("fixture.md", prefix, GAMER_WATER)
    joined = " | ".join(pre_findings)
    for needle in ("rubric_version 1", "chip_timbre_authenticity", "battle_energy",
                   "weight_sum 11", "elemental_atmosphere", "reject_signals_unnamed 5"):
        if needle not in joined:
            failures.append(f"  pre-fix case does not name {needle!r}")
    if pre_checked != 1:
        failures.append(f"  pre-fix case: want 1 declaration checked, got {pre_checked}")

    # coverage, second half (the pre-fix-rubric hole in the docstring): a brief that CARRIES a
    # block is checked even when the live rubric declares no scope data at all, so a rubric that
    # drops `applies_to` cannot make its briefs disappear from this check.
    unscoped = dict(GAMER_WATER, scoped=False)
    f_unscoped, c_unscoped = check_text("fixture.md", mutate(weight_sum=11), unscoped,
                                        required=True)
    if len(f_unscoped) != 1 or c_unscoped != 1:
        failures.append("  a wrong block in an unscoped family: want 1 finding and 1 declaration "
                        f"checked, got {len(f_unscoped)} and {c_unscoped}")

    print(f"SELFTEST {'PASS' if not failures else 'FAIL'} check_brief_rubric_scope: "
          f"{len(cases) + 1} case(s) — the comparator's branches, the pre-fix incident "
          f"declaration, the coverage half that keeps a block checked, and the two escapes "
          f"(prose history, unscoped family with no block)")
    for f in failures:
        print(f)
    return 0 if not failures else 1


# ── main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="FAIL when a brief's declared scoring scope disagrees with the live rubric")
    ap.add_argument("--repo", default="/home/j_kro/ai-content-pipeline")
    ap.add_argument("--rev", default=None,
                    help="read the BRIEFS as of this revision (the rubric is the live one, "
                         "unless --rubric-dir points elsewhere)")
    ap.add_argument("--briefs", action="append", default=None,
                    help="only these repo-relative briefs")
    ap.add_argument("--rubric-dir", default=None,
                    help="read the rubrics from here instead of <repo>/music/rubrics — how a "
                         "pre-fix rubric is tested against HEAD's briefs")
    ap.add_argument("--print-truth", default=None, metavar="GENRE",
                    help="print the declaration block the live rubric requires for GENRE")
    ap.add_argument("--quiet-skips", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    rubric_dir = Path(args.rubric_dir).resolve() if args.rubric_dir else None
    try:
        genres = load_registry_genres(repo)
        panel = load_panel(repo, rubric_dir)
    except CannotCompute as exc:
        print(f"CANNOT COMPUTE check_brief_rubric_scope: {exc}", file=sys.stderr)
        return 2

    if args.print_truth:
        if args.print_truth not in genres:
            print(f"CANNOT PRINT check_brief_rubric_scope: no genre {args.print_truth!r} in the "
                  f"registry (known: {', '.join(sorted(genres))})", file=sys.stderr)
            return 2
        try:
            truth = truth_for(panel, genres, args.print_truth)
        except SystemExit as exc:
            print(f"CANNOT PRINT check_brief_rubric_scope: {exc}", file=sys.stderr)
            return 2
        print(print_truth_block(truth))
        return 0

    try:
        rels = args.briefs or (briefs_rev(repo, args.rev) if args.rev
                               else briefs_worktree(repo))
    except CannotCompute as exc:
        print(f"CANNOT COMPUTE check_brief_rubric_scope: {exc}", file=sys.stderr)
        return 2
    if not rels:
        print("CANNOT COMPUTE check_brief_rubric_scope: no briefs found", file=sys.stderr)
        return 2

    truths: dict[str, dict] = {}
    findings: list[str] = []
    skips: list[str] = []
    checked = 0
    covered = 0
    checked_families: dict[str, object] = {}

    for rel in rels:
        genre = brief_genre(rel)
        if genre is None or genre not in genres:
            skips.append(f"{rel}: the path does not name a genre in music/genres.yaml")
            continue
        if genre not in truths:
            try:
                truths[genre] = truth_for(panel, genres, genre)
            except SystemExit as exc:
                print(f"CANNOT COMPUTE check_brief_rubric_scope: {exc}", file=sys.stderr)
                return 2
        truth = truths[genre]
        text = read(repo, rel, args.rev)
        has_decl = bool(declarations(text))
        if not truth["scoped"] and not has_decl:
            skips.append(f"{rel}: family {truth['family']} carries no `applies_to` scope data "
                         f"({truth['rubric_rel']}) and the brief declares none — every genre in "
                         f"it scores the same set, so there is no declared scope to disagree with")
            continue
        covered += 1
        checked_families[truth["family"]] = truth["rubric_version"]
        f, c = check_text(rel, text, truth, required=True)
        findings.extend(f)
        checked += c

    where = f"revision {args.rev}" if args.rev else "worktree"
    rubrics = ", ".join(f"{fam} v{ver}" for fam, ver in sorted(checked_families.items()))
    source = f"{rubric_dir}" if rubric_dir else f"{repo / 'music' / 'rubrics'}"

    if skips and not args.quiet_skips:
        print(f"SKIP check_brief_rubric_scope: {len(skips)} brief(s) not covered:")
        for s in skips:
            print("  " + s)

    if findings:
        print(f"FAIL check_brief_rubric_scope: {len(findings)} finding(s) in {checked} "
              f"declaration(s) across {covered} covered brief(s) ({where})")
        for f in findings:
            print("  " + f)
        print(f"  rubrics read: {rubrics or 'none'} from {source}")
        print("  Fix: run `--print-truth <genre>` for the correct block and replace the brief's "
              "one; if the rubric version moved, re-read the brief's prose section that quotes the "
              "rubric first — the block is the claim about now, the prose keeps the history.")
        return 1

    print(f"PASS check_brief_rubric_scope: {checked} declaration(s) across {covered} covered "
          f"brief(s) agree with the live rubric in {where} (rubrics read: {rubrics or 'none'} "
          f"from {source})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
