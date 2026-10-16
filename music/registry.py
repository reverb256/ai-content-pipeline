#!/usr/bin/env python3
"""music/registry.py — genre + lane registry loader and validator.

The music pipeline is genre-generic: genres are DATA (genres.yaml),
never code. This module is the single read path for that data and the
guard that keeps the registry internally consistent.

Pattern basis (established implementations, researched 2026-10-08):
  - PyYAML docs / yaml/pyyaml#576: use yaml.safe_load (yaml.load
    without a Loader is deprecated and unsafe).
  - autowarefoundation/autoware-index scripts/registry_load.py: one
    load module every reader goes through; RegistryError raised on
    parse errors, non-mapping documents, missing keys, and dangling
    references (a reference to an id that is not live is a HARD
    failure — silent empty output is exactly the failure mode this
    loader exists to kill).

Validation rules (fail loudly, exit non-zero on any violation):
  1. Both YAMLs parse (via safe_load).
  2. Every genre block carries the required keys: family,
     prompt_template, visual_style, lanes, cadence, video_shape.
  3. Every `lanes:` entry in every genre exists as a lane in
     lanes.yaml (dangling lane reference = failure).
  4. Every `prompt_template` and `visual_style` path resolves to a
     real file relative to music/ (dangling path = failure).
  5. Every lane block carries the required keys: surface, bot, gate.
  6. Every lane's `derived_product:` block names a stage that EXISTS in
     music/stages.yaml, a generator that resolves, an absolute interpreter that
     is a file, an output convention carrying <master-stem>, gate scripts that
     exist, and importable module names. A declared product nothing runs is the
     same class of defect as a dangling lane reference (card t_eb079b91).

Usage:
    python3 music/registry.py validate    # exit 0 on a clean registry
    python3 music/registry.py show        # dump the resolved registries
    python3 music/registry.py gate-for-stage --stage S --genre G
    python3 music/registry.py derived-for-stage --stage S --genre G \
        [--master PATH] [--bpm N] [--key K]

Exit codes: 0 = valid, 2 = registry error (dangling reference or
malformed file). On success, prints the resolved genre + lane counts.
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

# music/ is the anchor for every template/visual path in genres.yaml.
MUSIC_DIR = Path(__file__).resolve().parent
GENRES_YAML = MUSIC_DIR / "genres.yaml"
LANES_YAML = MUSIC_DIR / "lanes.yaml"
QUOTA_LEDGER = MUSIC_DIR / "quota-ledger.json"
GATES_DIR = MUSIC_DIR / "gates"
STAGES_YAML = MUSIC_DIR / "stages.yaml"

GENRE_REQUIRED_KEYS = (
    "family",
    "prompt_template",
    "visual_style",
    "lanes",
    "cadence",
    "video_shape",
)
LANE_REQUIRED_KEYS = ("surface", "bot", "gate")

# Stage gates (card t_d9983bb9). A gate named in a stage prompt cannot see that
# the gate and the genre's lane set disagree — the `visual` stage ran the YouTube
# inauthentic-content gate for a genre with no YouTube lane. So a stage's gate is
# declared here and resolved from the GENRE'S lanes.
STAGE_GATE_SELECTORS = ("lane_gate",)
WHEN_ABSENT_NONE = "none"

# Derived products (card t_eb079b91). A lane whose surface sells an artifact
# DERIVED from a master (the game-assets pack) declares it on the lane. `stage`
# names the stage in stages.yaml that runs the generator; `out` is the output
# convention and must carry the master's stem, so two tracks cannot share one
# pack directory.
DERIVED_REQUIRED_KEYS = ("stage", "generator", "interpreter", "out")
MASTER_STEM_PLACEHOLDER = "<master-stem>"


class RegistryError(Exception):
    """A registry invariant is violated. Printed, exit code 2."""


def repo_path(rel: str) -> Path:
    """Resolve a repo-relative path from a registry file (paths are repo-relative
    in stages.yaml and lanes.yaml, e.g. `music/assets/pack.py`)."""
    return MUSIC_DIR.parent / rel


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise RegistryError(f"missing registry file: {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryError(f"{path}: cannot parse: {exc}") from exc
    if not isinstance(doc, dict):
        raise RegistryError(
            f"{path}: expected a YAML mapping, got {type(doc).__name__}"
        )
    return doc


def load_lanes() -> dict:
    doc = load_yaml(LANES_YAML)
    lanes = doc.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise RegistryError(
            f"{LANES_YAML}: 'lanes:' must be a non-empty mapping of lane id -> spec"
        )
    problems = []
    for name, spec in lanes.items():
        if not isinstance(spec, dict):
            problems.append(f"{LANES_YAML}::{name}: lane spec must be a mapping")
            continue
        for key in LANE_REQUIRED_KEYS:
            value = spec.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(
                    f"{LANES_YAML}::{name}: '{key}' must be a non-empty string"
                )
    if problems:
        raise RegistryError("lane registry errors:\n  " + "\n  ".join(problems))
    return lanes


def load_genres(lanes: dict) -> dict:
    doc = load_yaml(GENRES_YAML)
    genres = doc.get("genres")
    if not isinstance(genres, dict) or not genres:
        raise RegistryError(
            f"{GENRES_YAML}: 'genres:' must be a non-empty mapping of genre id -> spec"
        )

    problems = []
    for name, spec in genres.items():
        if not isinstance(spec, dict):
            problems.append(f"{GENRES_YAML}::{name}: genre spec must be a mapping")
            continue

        for key in GENRE_REQUIRED_KEYS:
            if key not in spec or spec[key] in (None, ""):
                problems.append(
                    f"{GENRES_YAML}::{name}: missing required key '{key}'"
                )

        # Lane references must exist in lanes.yaml (the crossover check).
        declared = spec.get("lanes")
        if isinstance(declared, str):
            declared = [declared]
        if isinstance(declared, list):
            for lane in declared:
                if not isinstance(lane, str) or lane not in lanes:
                    problems.append(
                        f"{GENRES_YAML}::{name}: lane {lane!r} has no entry in "
                        f"{LANES_YAML.name}"
                    )

        # Template + visual paths must resolve to real files. Enforce
        # string type: YAML types `1.2` as float, which would silently
        # mangle the path (autoware registry_load.py float trap).
        for key in ("prompt_template", "visual_style"):
            rel = spec.get(key)
            if not isinstance(rel, str) or not rel:
                continue
            target = MUSIC_DIR / rel
            if not target.is_file():
                problems.append(
                    f"{GENRES_YAML}::{name}: {key} '{rel}' does not resolve "
                    f"(expected {target})"
                )

    if problems:
        raise RegistryError("genre registry errors:\n  " + "\n  ".join(problems))
    return genres


def load_stage_gates(lanes: dict) -> dict:
    """Load + validate the `stage_gates:` block of lanes.yaml (card t_d9983bb9).

    A stage's gate is DECLARED here and resolved from the genre's lanes, so a
    gate cannot be run for a genre that has no lane publishing to the surface it
    guards. Validation is deliberately loud: a declared gate with no script, or
    one no lane declares, would be a silent no-op.
    """
    doc = load_yaml(LANES_YAML)
    block = doc.get("stage_gates")
    if not isinstance(block, dict) or not block:
        raise RegistryError(
            f"{LANES_YAML}: 'stage_gates:' must be a non-empty mapping of "
            "stage -> {selector, gate, when_absent} — a gate hardcoded in a stage "
            "prompt cannot see that the gate and genre's lanes disagree"
        )

    stage_names: set[str] | None = None
    if STAGES_YAML.is_file():
        try:
            stages_doc = load_yaml(STAGES_YAML)
            stage_names = {
                str(entry.get("stage"))
                for entry in (stages_doc.get("stages") or [])
                if isinstance(entry, dict) and entry.get("stage")
            }
        except RegistryError:
            stage_names = None

    problems = []
    for stage, spec in block.items():
        where = f"{LANES_YAML.name}::stage_gates::{stage}"
        if not isinstance(spec, dict):
            problems.append(f"{where}: must be a mapping")
            continue
        if stage_names is not None and stage not in stage_names:
            problems.append(
                f"{where}: no such stage in {STAGES_YAML.name} — the rule can "
                f"never fire (stages: {', '.join(sorted(stage_names))})"
            )
        if spec.get("selector") not in STAGE_GATE_SELECTORS:
            problems.append(
                f"{where}: 'selector' must be one of "
                f"{', '.join(STAGE_GATE_SELECTORS)}"
            )
        gate = spec.get("gate")
        if not isinstance(gate, str) or not gate.strip():
            problems.append(f"{where}: 'gate' must be a non-empty gate name")
        elif not (GATES_DIR / f"{gate}.py").is_file():
            problems.append(
                f"{where}: gate '{gate}' has no script "
                f"music/gates/{gate}.py"
            )
        elif not any(lane.get("gate") == gate for lane in lanes.values()):
            problems.append(
                f"{where}: no lane in {LANES_YAML.name} declares "
                f"gate: {gate} — the stage gate could never be selected"
            )
        absent = spec.get("when_absent")
        if absent != WHEN_ABSENT_NONE and not (
            isinstance(absent, str) and (GATES_DIR / f"{absent}.py").is_file()
        ):
            problems.append(
                f"{where}: 'when_absent' must be {WHEN_ABSENT_NONE!r} or a gate "
                "whose script exists (what runs when no lane selects 'gate')"
            )
    if problems:
        raise RegistryError("stage gate errors:\n  " + "\n  ".join(problems))
    return block


def load_derived_products(lanes: dict) -> dict:
    """Load + validate every lane's `derived_product:` block (card t_eb079b91).

    A lane whose surface sells a DERIVED artifact — a pack built from a finished
    master, not the master itself — declares the product on the lane: the
    generator, the interpreter, the output convention, the gates. The `stage`
    key names the stage in music/stages.yaml that RUNS the generator.

    Before this block the `game-assets` lane had a generator and two gates and
    NO stage: `music/stages.yaml` declared 14 stages and not one of them ran
    `music/assets/pack.py`, so the primary lane of all six gamer genres had a
    manual step. That is what validation here makes impossible — a declared
    product whose stage does not exist is a HARD failure, exactly like a
    dangling lane reference (autoware registry_load.py: a reference to an id
    that is not live is a hard failure, because silent empty output is the
    failure mode this loader exists to kill).

    Returns {stage: {**block, "lane": <lane id>}}. Raises RegistryError.
    """
    stage_names: set[str] | None = None
    human_gates: set[str] = set()
    if STAGES_YAML.is_file():
        try:
            stages_doc = load_yaml(STAGES_YAML)
            entries = [e for e in (stages_doc.get("stages") or []) if isinstance(e, dict)]
            stage_names = {str(e["stage"]) for e in entries if e.get("stage")}
            human_gates = {
                str(e["stage"]) for e in entries if e.get("stage") and e.get("human_gate")
            }
        except RegistryError:
            stage_names = None

    problems: list[str] = []
    products: dict[str, dict] = {}
    for lane_name, spec in lanes.items():
        if not isinstance(spec, dict) or "derived_product" not in spec:
            continue
        where = f"{LANES_YAML.name}::{lane_name}::derived_product"
        block = spec.get("derived_product")
        if not isinstance(block, dict):
            problems.append(f"{where}: must be a mapping")
            continue

        for key in ("stage", "generator", "interpreter", "out"):
            value = block.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{where}: '{key}' must be a non-empty string")

        stage = block.get("stage")
        if isinstance(stage, str) and stage.strip():
            if stage_names is not None and stage not in stage_names:
                problems.append(
                    f"{where}: stage {stage!r} is not declared in {STAGES_YAML.name} — "
                    f"nothing in the pipeline runs {block.get('generator')!r} "
                    f"(stages: {', '.join(sorted(stage_names))})"
                )
            elif stage in human_gates:
                problems.append(
                    f"{where}: stage {stage!r} is a human gate — a human gate is "
                    f"never auto-dispatched, so the product would never build"
                )
            if stage in products:
                problems.append(
                    f"{where}: stage {stage!r} is already declared by lane "
                    f"{products[stage]['lane']!r} — one stage per product, or the "
                    f"resolver cannot tell which lane selected it"
                )
            else:
                products[stage] = {**block, "lane": lane_name}

        generator = block.get("generator")
        if isinstance(generator, str) and generator.strip():
            if not repo_path(generator).is_file():
                problems.append(
                    f"{where}: generator {generator!r} does not resolve "
                    f"(expected {repo_path(generator)})"
                )

        interpreter = block.get("interpreter")
        if isinstance(interpreter, str) and interpreter.strip():
            if not interpreter.startswith("/"):
                problems.append(
                    f"{where}: 'interpreter' must be an absolute path (got "
                    f"{interpreter!r}) — a bare name resolves differently in a "
                    f"worker shell (card t_d3b9e218)"
                )
            elif not Path(interpreter).is_file():
                problems.append(
                    f"{where}: interpreter {interpreter!r} is not a file on this host"
                )

        out = block.get("out")
        if isinstance(out, str) and out.strip() and MASTER_STEM_PLACEHOLDER not in out:
            problems.append(
                f"{where}: 'out' must carry {MASTER_STEM_PLACEHOLDER} — a pack "
                f"directory keyed to a fixed name would collide across tracks"
            )

        gates = block.get("gates")
        if not isinstance(gates, list) or not gates:
            problems.append(f"{where}: 'gates' must be a non-empty list of gate names")
        else:
            for gate in gates:
                if not isinstance(gate, str) or not (GATES_DIR / f"{gate}.py").is_file():
                    problems.append(
                        f"{where}: gate {gate!r} has no script music/gates/{gate}.py"
                    )

        modules = block.get("requires_modules")
        if modules is not None and (
            not isinstance(modules, list)
            or not all(isinstance(m, str) and m.strip() for m in modules)
        ):
            problems.append(
                f"{where}: 'requires_modules' must be a list of importable module "
                f"names (the interpreter's dependency declaration)"
            )

    if problems:
        raise RegistryError("derived product errors:\n  " + "\n  ".join(problems))
    return products


def derived_for_stage(stage: str, genre: str) -> dict:
    """The derived product that `stage` builds for `genre`, from the GENRE's lanes.

    Returns stage, genre, the genre's lanes, the lane whose `derived_product`
    selects this stage (None when no lane of this genre declares one), the
    product block, and a reason a human can audit. Raises RegistryError for a
    stage no lane declares (a resolver that guessed here would run a generator
    nothing selected) or an unknown genre.
    """
    registry = load_registry()
    products = registry["derived_products"]
    if stage not in products:
        raise RegistryError(
            f"no lane declares a derived product for stage {stage!r} in "
            f"{LANES_YAML.name} (declared: {', '.join(sorted(products)) or 'none'})"
        )
    genres = registry["genres"]
    if genre not in genres:
        raise RegistryError(f"no genre {genre!r} in {GENRES_YAML.name}")
    product = products[stage]
    lanes_spec = registry["lanes"]
    declared = genres[genre].get("lanes") or []
    if isinstance(declared, str):
        declared = [declared]

    base = {"stage": stage, "genre": genre, "lanes": list(declared),
            "product": product, "lane": product["lane"],
            "out": product["out"]}
    if product["lane"] in declared:
        return {**base,
                "reason": f"lane {product['lane']!r} declares the derived product "
                          f"{stage!r} (surface: {lanes_spec[product['lane']].get('surface')})"}
    return {**base, "lane": None, "product": None, "out": None,
            "reason": f"no lane of this genre declares a derived product for stage "
                      f"{stage!r} (lanes: {', '.join(declared) or 'none'})"}


def derived_command(product: dict, genre: str, master: str | None = None,
                    bpm=None, key=None) -> list[str]:
    """The generator command for a resolved product. `<master-stem>` in `out`
    becomes the master file's own stem, which is the generator's own default —
    the pack cannot drift from the master that produced it."""
    stem = Path(master).stem if master else MASTER_STEM_PLACEHOLDER
    out = str(product["out"]).replace(MASTER_STEM_PLACEHOLDER, stem)
    cmd = [product["interpreter"], product["generator"], master or "<master.wav>",
           "--genre", genre, "--out", out]
    if bpm is not None:
        cmd += ["--bpm", str(bpm)]
    if key is not None:
        cmd += ["--key", str(key)]
    return cmd


def gate_for_stage(stage: str, genre: str) -> dict:
    """The gate that guards `stage` for `genre`, resolved from the genre's LANES.

    Returns stage, genre, the genre's lanes, the resolved gate (None when the
    genre has no lane guarded by the declared gate), the lane that selected it,
    the script to run, and a reason a human can audit. Raises RegistryError for
    an unknown stage or genre.
    """
    registry = load_registry()
    rules = registry["stage_gates"]
    if stage not in rules:
        raise RegistryError(
            f"no stage_gates rule for stage {stage!r} in {LANES_YAML.name} "
            f"(declared: {', '.join(sorted(rules))})"
        )
    spec = rules[stage]
    genres = registry["genres"]
    if genre not in genres:
        raise RegistryError(f"no genre {genre!r} in {GENRES_YAML.name}")
    lanes_spec = registry["lanes"]
    declared = genres[genre].get("lanes") or []
    if isinstance(declared, str):
        declared = [declared]
    declaring = spec["gate"]

    selector_lane = next(
        (lane for lane in declared
         if isinstance(lane, str) and lanes_spec.get(lane, {}).get("gate") == declaring),
        None,
    )
    base = {"stage": stage, "genre": genre, "lanes": list(declared),
            "declared_gate": declaring}
    if selector_lane is not None:
        return {**base, "gate": declaring, "lane": selector_lane,
                "script": GATES_DIR / f"{declaring}.py",
                "reason": f"lane {selector_lane!r} is guarded by {declaring} "
                          f"(surface: {lanes_spec[selector_lane].get('surface')})"}
    absent = spec.get("when_absent")
    if absent == WHEN_ABSENT_NONE:
        return {**base, "gate": None, "lane": None, "script": None,
                "reason": f"no lane in this genre declares gate: {declaring} "
                          f"(lanes: {', '.join(declared)}) — when_absent: none, "
                          f"so the {stage} stage runs no gate for it"}
    return {**base, "gate": absent, "lane": None,
            "script": GATES_DIR / f"{absent}.py",
            "reason": f"no lane in this genre declares gate: {declaring}; "
                      f"when_absent: {absent}"}


def load_quota_ledger() -> dict:
    if not QUOTA_LEDGER.is_file():
        raise RegistryError(f"missing quota ledger: {QUOTA_LEDGER}")
    try:
        data = json.loads(QUOTA_LEDGER.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RegistryError(f"{QUOTA_LEDGER}: cannot parse: {exc}") from exc
    for key in ("standard_downloads_limit", "warn_at", "hard_stop_at"):
        if key not in data:
            raise RegistryError(f"{QUOTA_LEDGER}: missing '{key}'")
    if data["warn_at"] >= data["hard_stop_at"]:
        raise RegistryError(
            f"{QUOTA_LEDGER}: warn_at ({data['warn_at']}) must be < hard_stop_at "
            f"({data['hard_stop_at']})"
        )
    return data


def load_registry() -> dict:
    """Full registry: genres, lanes, stage gates, derived products, defaults, quota."""
    lanes = load_lanes()
    genres_doc = load_yaml(GENRES_YAML)
    genres = load_genres(lanes)
    return {
        "genres": genres,
        "lanes": lanes,
        "stage_gates": load_stage_gates(lanes),
        "derived_products": load_derived_products(lanes),
        "defaults": genres_doc.get("defaults", {}),
        "quota": load_quota_ledger(),
    }


def cmd_validate() -> int:
    registry = load_registry()
    genre_count = len(registry["genres"])
    lane_count = len(registry["lanes"])
    quota = registry["quota"]
    print(f"registry OK: {genre_count} genres, {lane_count} lanes, "
          f"{len(registry['stage_gates'])} stage gate rule(s), "
          f"{len(registry['derived_products'])} derived product(s)")
    print("genres: " + ", ".join(sorted(registry["genres"])))
    print("lanes: " + ", ".join(sorted(registry["lanes"])))
    for stage, spec in registry["stage_gates"].items():
        print(f"stage gate {stage}: {spec['selector']} -> {spec['gate']} "
              f"(when_absent: {spec['when_absent']})")
    for stage, product in registry["derived_products"].items():
        print(f"derived product {stage}: lane {product['lane']} -> "
              f"{product['generator']} under {product['interpreter']} "
              f"(out: {product['out']}, gates: {', '.join(product['gates'])})")
    print(
        "quota ledger: period {period}, standard {standard_downloads_used}/"
        "{standard_downloads_limit} "
        "(warn_at {warn_at}, hard_stop_at {hard_stop_at})".format(**quota)
    )
    return 0


def cmd_gate_for_stage(argv: list[str]) -> int:
    """`gate-for-stage --stage <stage> --genre <genre>` — the resolved gate.

    A stage prompt calls this instead of naming a gate, so the gate follows the
    genre's lanes (card t_d9983bb9). Exit 0 whether or not a gate applies:
    `gate: none` is a resolved answer, not an error.
    """
    stage = genre = None
    index = 2
    while index < len(argv):
        if argv[index] == "--stage" and index + 1 < len(argv):
            stage = argv[index + 1]
            index += 2
        elif argv[index] == "--genre" and index + 1 < len(argv):
            genre = argv[index + 1]
            index += 2
        else:
            print(f"usage: {Path(argv[0]).name} gate-for-stage "
                  "--stage <stage> --genre <genre>", file=sys.stderr)
            return 2
    if not stage or not genre:
        print(f"usage: {Path(argv[0]).name} gate-for-stage "
              "--stage <stage> --genre <genre>", file=sys.stderr)
        return 2

    resolved = gate_for_stage(stage, genre)
    print(f"stage   : {resolved['stage']}")
    print(f"genre   : {resolved['genre']}")
    print(f"lanes   : {', '.join(resolved['lanes'])}")
    if resolved["gate"] is None:
        print("gate    : none")
        print(f"reason  : {resolved['reason']}")
        print("action  : run NO gate for this stage, and state that on the card "
              "explicitly — a gate for a surface this genre never publishes to "
              "is a false check")
    else:
        print(f"gate    : {resolved['gate']}")
        print(f"script  : "
              f"{resolved['script'].relative_to(MUSIC_DIR.parent).as_posix()}")
        print(f"reason  : {resolved['reason']}")
        print("action  : run that script against this stage's artifact")
    return 0


def _run_label(product: dict) -> tuple[bool, str]:
    """Does the product's generator actually RUN under its pinned interpreter?

    Executes the generator's entrypoint (`--help`) instead of grepping for an
    import: before card t_5ed495eb the pack generator could not run at all on the
    lane host (/usr/bin/python3 had numpy but no scipy) and nothing noticed until
    a gate fixture failed. A dependency that is DECLARED but not importable is
    the failure this measures.
    """
    cmd = [product["interpreter"], product["generator"], "--help"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                              cwd=str(MUSIC_DIR.parent))
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"{product['generator']} did not start: {exc}"
    if proc.returncode == 0:
        return True, (f"{product['generator']} runs under {product['interpreter']} "
                      f"(modules: {', '.join(product.get('requires_modules') or [])})")
    first = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, (f"{product['generator']} does NOT run under "
                   f"{product['interpreter']} (rc {proc.returncode}): "
                   f"{first[-1] if first else 'no output'}")


def cmd_derived_for_stage(argv: list[str]) -> int:
    """`derived-for-stage --stage <stage> --genre <genre> [--master PATH] [--bpm N] [--key K]`

    A stage prompt calls this instead of hardcoding the generator, the interpreter
    and the output directory, so the product follows the GENRE's lanes (the same
    rule as `gate-for-stage`, card t_d9983bb9). Exit 0 whether or not the genre
    builds a product: `build: no` is a resolved answer, not an error.
    """
    stage = genre = master = None
    bpm = key = None
    index = 2
    wants = {"--stage": "stage", "--genre": "genre", "--master": "master",
             "--bpm": "bpm", "--key": "key"}
    while index < len(argv):
        flag = argv[index]
        if flag in wants and index + 1 < len(argv):
            value = argv[index + 1]
            if wants[flag] == "stage":
                stage = value
            elif wants[flag] == "genre":
                genre = value
            elif wants[flag] == "master":
                master = value
            elif wants[flag] == "bpm":
                bpm = value
            else:
                key = value
            index += 2
        else:
            print(f"usage: {Path(argv[0]).name} derived-for-stage --stage S --genre G "
                  "[--master PATH] [--bpm N] [--key K]", file=sys.stderr)
            return 2
    if not stage or not genre:
        print(f"usage: {Path(argv[0]).name} derived-for-stage --stage S --genre G "
              "[--master PATH] [--bpm N] [--key K]", file=sys.stderr)
        return 2

    resolved = derived_for_stage(stage, genre)
    print(f"stage   : {resolved['stage']}")
    print(f"genre   : {resolved['genre']}")
    print(f"lanes   : {', '.join(resolved['lanes'])}")
    if resolved["product"] is None:
        print("build   : no")
        print(f"reason  : {resolved['reason']}")
        print("action  : run NO generator for this genre, state that on the card "
              "explicitly, and advance to the next stage — a pack for a lane this "
              "genre does not declare is work nobody sells")
        return 0

    product = resolved["product"]
    out = str(resolved["out"])
    if master:
        out = out.replace(MASTER_STEM_PLACEHOLDER, Path(master).stem)
    print("build   : yes")
    print(f"lane    : {resolved['lane']}")
    print(f"out     : {out}")
    print(f"compute : {product['interpreter']}")
    ok, label = _run_label(product)
    print(f"run     : {'yes' if ok else 'NO'} — {label}")
    print("tempo   : state the tempo and key the render was made at (the plan JSON "
          "at /var/lib/music-plans/<plan-stem>.json carries bpm + key); the "
          "generator only ESTIMATES them when they are not stated (card t_4906bc6e)")
    print("command : " + " ".join(derived_command(product, genre, master, bpm, key)))
    print("accept  : rc 0 = the generator ACCEPTED the pack (it prints its own "
          "acceptance block); rc 1 = REJECTED — read the block, comment it, and do "
          "NOT advance (a master too short for the generator's loop count cannot "
          "make a shippable pack)")
    for gate in product["gates"]:
        if gate == "gate_loop_points":
            print(f"gate    : {gate} --pack-dir {out}")
        else:
            print(f"gate    : {gate} --package-dir {out} --lane {resolved['lane']}")
    print(f"reason  : {resolved['reason']}")
    print("action  : run the command, then BOTH gates against the pack; a gate FAIL "
          "means the pack is reworked, never advanced")
    print("publish : NOT here — an upload stays behind the human gate (j_kro)")
    return 0


def cmd_show() -> int:
    registry = load_registry()
    print(yaml.safe_dump({"genres": registry["genres"], "lanes": registry["lanes"]}, sort_keys=False))
    return 0


def main(argv: list) -> int:
    command = argv[1] if len(argv) > 1 else "validate"
    try:
        if command == "validate":
            return cmd_validate()
        if command == "show":
            return cmd_show()
        if command == "gate-for-stage":
            return cmd_gate_for_stage(argv)
        if command == "derived-for-stage":
            return cmd_derived_for_stage(argv)
        print(f"usage: {Path(argv[0]).name} "
              "[validate|show|gate-for-stage --stage S --genre G"
              "|derived-for-stage --stage S --genre G [--master PATH] "
              "[--bpm N] [--key K]]",
              file=sys.stderr)
        return 2
    except RegistryError as exc:
        print(f"REGISTRY ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
