#!/usr/bin/env python3
"""_lane_registry — read `music/lanes.yaml` with the standard library only.

WHY THIS EXISTS (music board, card t_d9983bb9, measured 2026-10-16)
------------------------------------------------------------------
`music/lanes.yaml` declares, per lane, the gate that must pass before that lane
publishes:

    sync-documentary:
      gate: gate_sync_ready
      requires: [stems, metadata, clearance_doc, instrumental_version]

A gate must accept EVERY lane the registry assigns to it. So the gate's lane list
must be DERIVED from the registry, never kept as a second copy inside the script:
the copy is how `sync-documentary` came to declare `gate: gate_sync_ready` in
lanes.yaml while `gate_sync_ready.py`'s argparse rejected the name and exited 2 —
an ARGUMENT error that a stage reads as a gate FAILURE.

The obvious read path is PyYAML (`music/registry.py`). That path is NOT safe
inside a gate. Measured on nexus, 2026-10-16:

    $ command -v python3
    /home/j_kro/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3
    $ python3 -c 'import yaml'
    ModuleNotFoundError: No module named 'yaml'
    $ /usr/bin/python3 -c 'import yaml; print(yaml.__version__)'
    6.0.3

Every stage prompt calls a gate as `python3 music/gates/<gate>.py`, so a hard
PyYAML import would turn a working gate into a `ModuleNotFoundError` in exactly
the shell a worker uses — the same defect class this module removes: a gate that
fails for a reason that is not the artifact.

So this module is a scanner for the file's DOCUMENTED block shape (see the
lanes.yaml header): a lane id at 2-space indent inside the top-level `lanes:`
section, scalar keys at 4-space indent. It is deliberately not a YAML
implementation — it reads `gate`, `requires` and `surface` and skips the rest.

DRIFT GUARD (the reason a scanner is acceptable at all):
`music/scripts/check_gate_lane_surface.py` parses the same file with PyYAML via
`music/registry.py` and fails when the two readings disagree. A reformat of
lanes.yaml that this scanner cannot follow is therefore caught by a standing
check, not discovered later by a gate.
"""

from __future__ import annotations

import re
from pathlib import Path

MUSIC_DIR = Path(__file__).resolve().parents[1]
LANES_YAML = MUSIC_DIR / "lanes.yaml"

# A top-level key (no indent) opens a section: `version: 1`, `lanes:`,
# `stage_gates:`. Only the `lanes:` section holds lane blocks.
_TOP_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*$")
# A lane id: 2-space indent, bare key, nothing after the colon.
_LANE_RE = re.compile(r"^  ([A-Za-z0-9][A-Za-z0-9_.-]*):\s*$")
# A key inside a lane block: 4-space indent.
_LANE_KEY_RE = re.compile(r"^    ([a-z_][a-z0-9_]*):\s*(.*?)\s*$")
# An inline flow list: `[a, b, c]`.
_LIST_RE = re.compile(r"^\[(.*)\]$")


class LaneRegistryError(Exception):
    """`music/lanes.yaml` could not be read as the documented shape."""


def _scalar(raw: str) -> str:
    """The scalar value of a `key: value` line (quotes kept off, comment off)."""
    text = raw.strip()
    if text[:1] in ("'", '"'):
        quote = text[0]
        end = text.find(quote, 1)
        return text[1:end] if end != -1 else text[1:]
    return text.split("#", 1)[0].strip()


def _flow_list(raw: str) -> tuple[str, ...]:
    """Parse `[a, b, c]` (or `[]`) into a tuple of bare scalars."""
    text = raw.split("#", 1)[0].strip()
    match = _LIST_RE.match(text)
    if not match:
        return ()
    return tuple(
        item.strip().strip("'\"")
        for item in match.group(1).split(",")
        if item.strip()
    )


def load_lanes(path: Path | str | None = None) -> dict[str, dict]:
    """`{lane: {"gate": str|None, "requires": tuple, "surface": str|None}}`.

    Raises LaneRegistryError when the file is absent or holds no lane block — a
    reader that silently returns {} would make a gate pass its contract check
    against nothing.
    """
    source = Path(path) if path is not None else LANES_YAML
    if not source.is_file():
        raise LaneRegistryError(f"no lane registry at {source}")
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:  # unreadable file is a hard failure, not an empty registry
        raise LaneRegistryError(f"{source}: cannot read: {exc}") from exc

    lanes: dict[str, dict] = {}
    section: str | None = None
    current: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] not in (" ", "\t"):                      # top-level key
            match = _TOP_KEY_RE.match(raw)
            section = match.group(1) if match else None
            current = None
            continue
        if section != "lanes":
            continue
        match = _LANE_RE.match(raw)
        if match:
            current = match.group(1)
            lanes[current] = {"gate": None, "requires": (), "surface": None}
            continue
        match = _LANE_KEY_RE.match(raw)
        name = current
        if match and name is not None:
            key, value = match.group(1), match.group(2)
            if key == "requires":
                lanes[name]["requires"] = _flow_list(value)
            elif key in ("gate", "surface"):
                lanes[name][key] = _scalar(value) or None

    if not lanes:
        raise LaneRegistryError(
            f"{source}: no lane block found — the file is not in the documented "
            "shape (lane id at 2-space indent inside `lanes:`)"
        )
    return lanes


def lanes_declaring(gate_name: str,
                    path: Path | str | None = None) -> tuple[str, ...]:
    """Every lane whose `gate:` is `gate_name`, in registry order.

    This is the authoritative lane list for a gate: argparse `choices` for a gate
    script come from here, so adding a lane to lanes.yaml is enough to make the
    gate accept it (card t_d9983bb9).
    """
    return tuple(
        lane for lane, spec in load_lanes(path).items()
        if spec.get("gate") == gate_name
    )


def requirements_for(lane: str,
                     path: Path | str | None = None) -> tuple[str, ...]:
    """The artifacts `lane` declares under `requires:` (empty tuple when none)."""
    lanes = load_lanes(path)
    if lane not in lanes:
        raise LaneRegistryError(f"{lane!r} is not a lane in {path or LANES_YAML}")
    return tuple(lanes[lane].get("requires") or ())


if __name__ == "__main__":  # a reader that cannot be looked at is not verifiable
    import json
    import sys
    print(json.dumps(load_lanes(), indent=2, default=list))
    sys.exit(0)
