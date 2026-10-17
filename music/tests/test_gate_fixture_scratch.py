#!/usr/bin/env python3
"""The gate suite's fixture builders write only where they are told to.

Run: python3 music/tests/test_gate_fixture_scratch.py

REGRESSION (2026-10-16, card t_7ab98781). `music/gates/_visual_fixtures.py`
wrote the ffmpeg concat demuxer's list to the BARE RELATIVE name
`concat_list.txt`. `check_gate_suite.sh` cd's to the repo root before it builds
fixtures, and `concat_list.txt` is a TRACKED file there, so EVERY matrix run
overwrote it with that run's own fixture paths and left the shared checkout
dirty - which is how a fixture byproduct gets swept into somebody's commit by
`git add -A`. Measured on nexus: `git diff concat_list.txt` after one run held
three `file '<that run's scratch>/pscene_N.mp4'` lines.

The builder now derives the list from its OUTPUT path - so the list can only
land beside the output - and refuses a relative path outright. These checks
hold that down, and they need no ffmpeg: the list step is exercised on its own.
"""

import importlib.util
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
BUILDER = REPO / "music" / "gates" / "_visual_fixtures.py"

spec = importlib.util.spec_from_file_location("_visual_fixtures", BUILDER)
vf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vf)

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


# ---------------------------------------------------------------------------
print("1. the concat list is derived from the output path, never a fixed name")

out = "/scratch-dir/good_visual.mp4"
lst = vf.list_path(out)
check(f"list_path({out!r}) sits next to its output",
      lst == f"{out}.concat_list.txt", repr(lst))
check("...and is an absolute path", os.path.isabs(lst), repr(lst))
check("...and is not the bare name the builder used to write",
      os.path.basename(lst) != "concat_list.txt", repr(lst))

# ---------------------------------------------------------------------------
print()
print("2. the list step, run from the REPO ROOT, touches no repo file")

# The incident needs the WRITE, not only the path: run the list step with the
# CWD set to the repo root - where `check_gate_suite.sh` runs - and watch the
# tracked file that used to be overwritten there. The comparison is before/after
# within this run, so a sibling run's dirt at the same path cannot make it flaky.
tracked = REPO / "concat_list.txt"
before = tracked.read_bytes() if tracked.is_file() else None
scratch = pathlib.Path(tempfile.mkdtemp(prefix="_tgf-"))
out2 = str(scratch / "prior_visual.mp4")
written = None
cwd = os.getcwd()
try:
    os.chdir(REPO)
    written = vf.write_list(["/scratch-dir/pscene_0.mp4"], out2)
finally:
    os.chdir(cwd)

check("the list was written next to the output it was given",
      written == f"{out2}.concat_list.txt" and pathlib.Path(written).is_file(),
      repr(written))
check("...carrying the file paths verbatim",
      pathlib.Path(written).read_text() == "file '/scratch-dir/pscene_0.mp4'\n",
      repr(pathlib.Path(written).read_text()))
after = tracked.read_bytes() if tracked.is_file() else None
check("the tracked repo file is untouched by a build run from the repo root",
      before == after, f"{tracked}: {before!r} -> {after!r}")
check("the repo root gained no fixture list beside an output",
      not sorted(p.name for p in REPO.glob("*.mp4.concat_list.txt")),
      "a *.mp4.concat_list.txt appeared at the repo root")

# ---------------------------------------------------------------------------
print()
print("3. a relative output is refused, not written into the caller's CWD")

# The incident's exact shape: a relative name would land in the CWD, which here
# is the repo root. A refusal is what keeps the matrix from dirtying the tree in
# silence (`build_fixtures` turns the failure into FATAL, so it cannot pass).
probe_cwd = pathlib.Path(tempfile.mkdtemp(prefix="_tgf-cwd-"))
refused = False
detail = "write_list accepted a relative output"
left: list[str] = []
cwd = os.getcwd()
try:
    os.chdir(probe_cwd)
    try:
        vf.write_list(["/scratch-dir/pscene_0.mp4"], "relative_visual.mp4")
    except SystemExit as e:
        refused = "absolute path" in str(e)
        detail = str(e)
    left = sorted(p.name for p in probe_cwd.iterdir())
finally:
    os.chdir(cwd)
check("a relative output is refused instead of landing in the CWD", refused, detail)
check("...and that CWD was left empty", left == [], str(left))

# The probe scratch is this suite's own; remove it so nothing is left behind.
for d in (scratch, probe_cwd):
    for p in d.iterdir():
        p.unlink()
    d.rmdir()

# ---------------------------------------------------------------------------
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
