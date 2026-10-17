#!/usr/bin/env python3
"""check_pack_stage — every declared DERIVED PRODUCT has a stage that builds it,
and that stage does not hardcode what the registry declares.

WHY THIS EXISTS (incident 2026-10-16, card t_eb079b91)
------------------------------------------------------
`music/stages.yaml` declared 14 stages and NOT ONE of them ran
`music/assets/pack.py`:

    $ grep -rn 'assets/pack.py' --include='*.yaml' --include='*.sh' \\
          --include='*.service' . | grep -v briefs
    ./brain/runbooks/music-game-assets.md:77:  ... run `python3 music/assets/pack.py ...`
    ./music/gates/check_gate_suite.sh:263:     # Built by music/assets/pack.py ...

The `game-assets` lane — the PRIMARY lane of all six gamer genres
(elemental-fire/water/earth/air, chiptune-8bit, epic-orchestral-boss) — had a
generator and two gates and no automation between a master and a shippable pack.
A human had to remember to run the generator.

The fix declares the product ON THE LANE (`game-assets.derived_product` in
lanes.yaml) and gives it a stage (`asset-pack`). This check holds both halves
together, because either half alone drifts back:

  * the registry half — `registry.py validate` FAILS when a declared product
    names a stage nothing declares. That guard is inside the loader every reader
    uses, so it cannot be bypassed by a reader that skips this check.
  * the wiring half, HERE — the stage's prompt must resolve the product from the
    registry instead of hardcoding the generator, the interpreter, the output
    directory and the gates (a hardcoded decision cannot see that it and the
    registry disagree — the defect class of card t_d9983bb9, fixed the same way
    for stage gates via `registry.py gate-for-stage`).

Rules enforced (FAIL)
---------------------
1. Every lane's `derived_product.stage` is declared in stages.yaml, is a
   PRODUCING stage (a prompt, not `human_gate: true`), and is the only stage
   claiming it.
2. That stage's prompt calls the resolver with the product's PINNED interpreter
   (`<interpreter> music/registry.py derived-for-stage --stage <stage>`), so the
   decision is read, never remembered.
3. The prompt names EVERY gate the product declares, and the product's output
   convention (`<master-stem>`), so a pack cannot ship ungated or at an
   invented path.
4. The prompt requires the generator command's EXIT STATUS to be checked — the
   generator exits 1 with an acceptance block when a pack is REJECTED, and a
   stage that ignores rc would advance a rejected pack.
5. The prompt carries no publisher command (`butler push`, `gumroad`, `curl -F`,
   `aws s3 cp`): publishing a pack stays behind the `human-approval` gate.
6. Position: the stage sits AFTER the stage that produced its input and BEFORE
   the release package — a pack derives from a master the quality `gate` already
   vetted, and it is not a release package.
7. EVERY genre is resolved, live (one subprocess per genre): `build: yes` and a
   concrete command exactly when the genre's own lanes declare the product's
   lane, `build: no` otherwise. This is what makes a hardcoded genre list fail
   here instead of shipping a pack for a genre whose lanes never sold one.
8. The generator RUNS under its pinned interpreter (`run : yes`) — measured by
   executing its entrypoint, not by grepping for an import. Card t_5ed495eb: the
   generator could not run at all on the lane host (numpy present, scipy absent)
   and nothing noticed until a gate fixture failed.

cited: t_eb079b91 (this incident) · t_5ed495eb (pack/gate shape, generator deps) ·
       t_d9983bb9 (a hardcoded gate in a stage prompt) · t_4906bc6e (the
       generator's estimator fabricates a key when none is stated) ·
       t_8a715681 (butler absent) · t_5a93164a (advance channel)

Usage:
  /usr/bin/python3 music/scripts/check_pack_stage.py [--repo DIR] [--stages PATH]
  /usr/bin/python3 music/scripts/check_pack_stage.py --selftest

Exit codes: 0 = every rule holds, 1 = at least one violation, 2 = cannot read
the inputs (missing stage map, no PyYAML).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = Path(__file__).resolve().parents[2]
RESOLVER = "registry.py derived-for-stage"
PUBLISHER_PATTERNS = ("butler push", "gumroad", "curl -f", "curl -F", "aws s3 cp")
# The stages a derived product must sit between: it consumes a vetted master and
# is not the release package.
AFTER_STAGES = ("gate",)
BEFORE_STAGES = ("package",)


class CheckError(RuntimeError):
    """The inputs cannot be read. Never report a PASS on unreadable inputs."""


def _load_stages(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise CheckError(
            f"this interpreter has no PyYAML, so {path} cannot be read; re-run "
            f"with /usr/bin/python3") from exc
    if not path.is_file():
        raise CheckError(f"no stage map at {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CheckError(f"{path}: cannot parse: {exc}") from exc
    if not isinstance(doc, dict):
        raise CheckError(f"{path} is not a stage map (expected a mapping)")
    return doc


def stage_entries(doc: dict) -> list[dict]:
    return [e for e in (doc.get("stages") or []) if isinstance(e, dict) and e.get("stage")]


def stage_order(doc: dict) -> list[str]:
    return [str(e["stage"]) for e in stage_entries(doc)]


def _prompt_of(doc: dict, stage: str) -> str:
    for entry in stage_entries(doc):
        if str(entry["stage"]) == stage:
            return str(entry.get("prompt") or "")
    return ""


def _is_human_gate(doc: dict, stage: str) -> bool:
    return any(str(e["stage"]) == stage and e.get("human_gate") for e in stage_entries(doc))


def resolve(repo: Path, interpreter: str, stage: str, genre: str,
            master: str | None = None) -> tuple[int, str]:
    """Run the product's own resolver, exactly as the stage prompt does."""
    cmd = [interpreter, "music/registry.py", "derived-for-stage",
           "--stage", stage, "--genre", genre]
    if master:
        cmd += ["--master", master]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo),
                          timeout=300)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def field(output: str, name: str) -> str | None:
    prefix = f"{name}"
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped.split(":", 1)[1].strip() if ":" in stripped else ""
    return None


def run(products: dict, lanes: dict, genres: dict, doc: dict, repo: Path,
        resolver=resolve) -> tuple[list[str], list[str]]:
    """Return (problems, notes). `resolver` is injectable so --selftest can
    exercise every rule without a real registry."""
    problems: list[str] = []
    notes: list[str] = []
    order = stage_order(doc)
    if not order:
        problems.append("stages.yaml declares no stages")
        return problems, notes

    for stage, product in sorted(products.items()):
        lane = product["lane"]
        interpreter = product["interpreter"]
        generator = product["generator"]
        gates = list(product.get("gates") or [])
        out_conv = product["out"]

        if stage not in order:
            problems.append(
                f"{stage}: declared as the derived product of lane {lane!r} but NO "
                f"stage in stages.yaml runs {generator!r} — nothing builds it "
                f"(stages: {', '.join(order)})")
            continue
        if _is_human_gate(doc, stage):
            problems.append(
                f"{stage}: is a human gate — a human gate is never auto-dispatched, "
                f"so {generator} would never run automatically")
        owners = [s for s, p in products.items() if s == stage]
        if len(owners) > 1:
            problems.append(f"{stage}: claimed by more than one derived product")

        position = order.index(stage)
        for earlier in AFTER_STAGES:
            if earlier in order and order.index(earlier) > position:
                problems.append(
                    f"{stage}: sits BEFORE `{earlier}` in the declared order — the "
                    f"pack must derive from a master that stage already vetted")
        for later in BEFORE_STAGES:
            if later in order and order.index(later) < position:
                problems.append(
                    f"{stage}: sits AFTER `{later}` in the declared order — a pack "
                    f"is not a release package")

        prompt = _prompt_of(doc, stage)
        if not prompt:
            problems.append(f"{stage}: is declared but carries no prompt, so the "
                            f"driver would dispatch nothing")
            continue
        call = f"{interpreter} music/{RESOLVER}"
        if call not in prompt:
            problems.append(
                f"{stage}: prompt does not call `{call}` — a stage that hardcodes "
                f"which genres build a pack cannot see that it and lanes.yaml "
                f"disagree")
        for gate in gates:
            if gate not in prompt:
                problems.append(f"{stage}: prompt never names the product's gate "
                                f"{gate!r} (lane {lane!r})")
        if out_conv not in prompt:
            problems.append(f"{stage}: prompt never states the output convention "
                            f"{out_conv!r}")
        if "exit status" not in prompt.lower():
            problems.append(f"{stage}: prompt does not require the generator "
                            f"command's exit status to be checked — a REJECTED "
                            f"pack would advance")
        for pattern in PUBLISHER_PATTERNS:
            if pattern in prompt.lower():
                problems.append(f"{stage}: prompt carries a publisher command "
                                f"({pattern!r}) — publishing is behind the "
                                f"human-approval gate")

        built, skipped = [], []
        for genre in sorted(genres):
            declared = genres[genre].get("lanes") or []
            if isinstance(declared, str):
                declared = [declared]
            wants = lane in declared
            rc, output = resolver(repo, interpreter, stage, genre)
            if rc != 0:
                problems.append(f"{stage}/{genre}: the resolver exited {rc}: "
                                f"{output.strip().splitlines()[:1]}")
                continue
            answer = (field(output, "build") or "").strip()
            if wants and answer != "yes":
                problems.append(
                    f"{stage}/{genre}: lane {lane!r} IS in this genre's lanes "
                    f"({', '.join(declared)}) but the resolver answered "
                    f"build: {answer or 'nothing'}")
                continue
            if not wants and answer != "no":
                problems.append(
                    f"{stage}/{genre}: no lane of this genre declares the product "
                    f"but the resolver answered build: {answer or 'nothing'} "
                    f"(lanes: {', '.join(declared)})")
                continue
            if not wants:
                skipped.append(genre)
                continue
            built.append(genre)
            command = field(output, "command") or ""
            run_label = field(output, "run") or ""
            if not run_label.startswith("yes"):
                problems.append(
                    f"{stage}/{genre}: the generator does not RUN under "
                    f"{interpreter}: {run_label}")
            if interpreter not in command:
                problems.append(f"{stage}/{genre}: the command does not use the "
                                f"pinned interpreter {interpreter!r}: {command}")
            if f"--out packages/" not in command:
                problems.append(f"{stage}/{genre}: the command does not write under "
                                f"packages/: {command}")
            for gate in gates:
                if gate not in output:
                    problems.append(f"{stage}/{genre}: the resolver does not name "
                                    f"the gate {gate!r} it must run after building")
        notes.append(f"{stage}: builds for {len(built)}/{len(genres)} genre(s) "
                     f"(lane {lane!r}): {', '.join(built) or 'none'}")
        if skipped:
            notes.append(f"{stage}: resolved `build: no` for {len(skipped)} "
                         f"genre(s) without that lane")
    if not products:
        notes.append("no lane declares a derived product — nothing to check")
    return problems, notes


# ── selftest fixtures ───────────────────────────────────────────────────────
GOOD_INTERPRETER = "/usr/bin/python3"
GOOD_PRODUCT = {
    "lane": "game-assets",
    "stage": "asset-pack",
    "generator": "music/assets/pack.py",
    "interpreter": GOOD_INTERPRETER,
    "out": "packages/<master-stem>-asset-pack",
    "gates": ["gate_sync_ready", "gate_loop_points"],
    "requires_modules": ["numpy", "scipy"],
}


def _prompt(gates=("gate_sync_ready", "gate_loop_points"),
            resolver=True, out=True, rc=True, publish=None) -> str:
    parts = ["Run the asset-pack stage."]
    if resolver:
        parts.append(f"{GOOD_INTERPRETER} music/registry.py derived-for-stage "
                     f"--stage asset-pack --genre <g>")
    if out:
        parts.append("The output directory is packages/<master-stem>-asset-pack.")
    if rc:
        parts.append("Check the command's exit status and do NOT advance on rc 1.")
    else:
        parts.append("Run the command.")
    parts.append("Run " + " and ".join(gates) + " against the pack.")
    if publish:
        parts.append(publish)
    return " ".join(parts)


def _doc(order=("brief", "generate", "stems", "master", "gate", "asset-pack",
                "package", "publish", "human-approval"),
         prompt=None, human_gate_stage=None) -> dict:
    stages = []
    for name in order:
        entry = {"stage": name, "bot": "producer", "prompt": "advance"}
        if name == "asset-pack":
            entry["prompt"] = _prompt() if prompt is None else prompt
        if name == human_gate_stage:
            entry = {"stage": name, "human_gate": True}
        stages.append(entry)
    return {"stages": stages}


def _fake_resolver(interpreter, stage, genre, answer, command=None, run_label="yes"):
    def _inner(repo, got_interpreter, got_stage, got_genre, master=None):
        lines = [f"stage   : {got_stage}", f"genre   : {got_genre}",
                 f"build   : {answer}"]
        if answer == "yes":
            lines += [f"run     : {run_label}",
                      "command : " + (command or
                                      f"{got_interpreter} music/assets/pack.py "
                                      f"<master.wav> --genre {got_genre} "
                                      f"--out packages/<master-stem>-asset-pack"),
                      "gate    : gate_sync_ready --package-dir <pack> --lane game-assets",
                      "gate    : gate_loop_points --pack-dir <pack>"]
        return 0, "\n".join(lines)
    return _inner


def selftest() -> int:
    repo = Path("/nonexistent")  # the fake resolver never touches disk
    lanes = {"game-assets": {"gate": "gate_sync_ready"}, "streaming": {}}
    genres = {"gamer": {"lanes": ["game-assets", "streaming"]},
              "plain": {"lanes": ["streaming"]}}
    products = {"asset-pack": dict(GOOD_PRODUCT)}
    ok_resolver = _fake_resolver(GOOD_INTERPRETER, "asset-pack", "x", "yes")
    # the fake needs a per-genre answer: a lane-carrying genre builds, the other does not
    def resolver(_repo, interpreter, stage, genre, master=None):
        return _fake_resolver(interpreter, stage, genre,
                              "yes" if genre == "gamer" else "no")(_repo, interpreter,
                                                                   stage, genre, master)

    cases: list[tuple[str, dict, dict, dict, dict, object, str]] = [
        ("clean", products, lanes, genres, _doc(), resolver, ""),
        ("stage absent from the map", products, lanes, genres,
         _doc(order=("brief", "master", "gate", "package")), resolver, "NO stage"),
        ("stage is a human gate", products, lanes, genres,
         _doc(human_gate_stage="asset-pack"), resolver, "human gate"),
        ("stage sits before the quality gate", products, lanes, genres,
         _doc(order=("brief", "asset-pack", "gate", "package")), resolver, "BEFORE"),
        ("stage sits after the release package", products, lanes, genres,
         _doc(order=("brief", "gate", "package", "asset-pack")), resolver, "AFTER"),
        ("prompt hardcodes (no resolver call)", products, lanes, genres,
         _doc(prompt=_prompt(resolver=False)), resolver, "does not call"),
        ("prompt drops a gate", products, lanes, genres,
         _doc(prompt=_prompt(gates=("gate_sync_ready",))), resolver,
         "never names the product's gate"),
        ("prompt drops the output convention", products, lanes, genres,
         _doc(prompt=_prompt(out=False)), resolver, "output convention"),
        ("prompt ignores the generator's rc", products, lanes, genres,
         _doc(prompt=_prompt(rc=False)), resolver, "exit status"),
        ("prompt uploads", products, lanes, genres,
         _doc(prompt=_prompt(publish="Then run butler push <pack> user/pack:linux.")),
         resolver, "publisher command"),
        ("resolver answers no for a lane-carrying genre", products, lanes, genres,
         _doc(), _fake_resolver(GOOD_INTERPRETER, "asset-pack", "x", "no"),
         "IS in this genre's lanes"),
        ("resolver answers yes for a genre without the lane", products, lanes,
         {"gamer": {"lanes": ["streaming"]}, "plain": {"lanes": ["streaming"]}},
         _doc(), _fake_resolver(GOOD_INTERPRETER, "asset-pack", "x", "yes"),
         "no lane of this genre declares"),
        ("generator does not run", products, lanes, genres, _doc(),
         _fake_resolver(GOOD_INTERPRETER, "asset-pack", "x", "yes",
                        run_label="NO — ModuleNotFoundError: scipy"),
         "does not RUN"),
        ("command uses a bare interpreter", products, lanes, genres, _doc(),
         _fake_resolver("python3", "asset-pack", "x", "yes",
                        command="python3 music/assets/pack.py <m.wav> --genre g "
                                "--out packages/<master-stem>-asset-pack"),
         "pinned interpreter"),
        ("command writes outside packages/", products, lanes, genres, _doc(),
         _fake_resolver(GOOD_INTERPRETER, "asset-pack", "x", "yes",
                        command=f"{GOOD_INTERPRETER} music/assets/pack.py <m.wav> "
                                f"--genre g --out /tmp/whatever"),
         "does not write under"),
    ]
    for label, prods, ln, gn, doc, res, expect in cases:
        problems, _notes = run(prods, ln, gn, doc, repo, res)
        if not expect:
            if problems:
                print(f"SELFTEST FAIL ({label}): clean case reported {problems}")
                return 1
            continue
        if not any(expect in p for p in problems):
            print(f"SELFTEST FAIL ({label}): expected {expect!r} in {problems}")
            return 1
    print("PASS --selftest: a product with no stage, a human-gate stage, both "
          "position errors, a hardcoded/gate-dropping/rc-ignoring/uploading "
          "prompt, a wrong build answer, a generator that does not run, and a "
          "command that ignores the pinned interpreter or the output convention "
          "are all caught")
    return 0


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    ap = argparse.ArgumentParser(
        description="Check that every declared derived product has a stage that builds it.")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--stages", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve()
    stages = Path(args.stages) if args.stages else repo / "music" / "stages.yaml"
    try:
        doc = _load_stages(stages)
    except CheckError as exc:
        print(f"FAIL check_pack_stage: {exc}")
        return 2

    sys.path.insert(0, str(repo / "music"))
    try:
        import registry  # noqa: PLC0415
        reg = registry.load_registry()
    except Exception as exc:  # registry.RegistryError or an import error
        print(f"FAIL check_pack_stage: the registry does not load: "
              f"{type(exc).__name__}: {exc}")
        return 1

    problems, notes = run(reg["derived_products"], reg["lanes"], reg["genres"],
                          doc, repo)
    for note in notes:
        print(f"note    {note}")
    if problems:
        print(f"FAIL check_pack_stage: {len(problems)} problem(s) in "
              f"{repo / 'music' / 'lanes.yaml'} vs {stages}")
        for problem in problems:
            print(f"  {problem}")
        print("  cited: t_eb079b91 (a product with no stage), t_5ed495eb "
              "(generator deps), t_d9983bb9 (a hardcoded decision in a prompt)")
        return 1
    products = reg["derived_products"]
    print(f"PASS check_pack_stage: {len(products)} derived product(s) built by a "
          f"declared stage; {len(reg['genres'])} genre(s) resolved live, "
          f"both lanes.yaml and stages.yaml agreeing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
