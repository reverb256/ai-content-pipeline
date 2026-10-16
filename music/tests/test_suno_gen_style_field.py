#!/usr/bin/env python3
"""The CDP rail's style field is the one the CALLER names (card t_0525127c).

Run:  /usr/bin/python3 music/tests/test_suno_gen_style_field.py
      /usr/bin/python3 music/tests/test_suno_gen_style_field.py \
          --suno-gen /tmp/t0525127c-prefix/suno-gen.py     # the RED re-run

WHY THIS TEST EXISTS (card t_0525127c, 2026-10-16, nexus)
---------------------------------------------------------
`music/prompts/commentary-beds.md` sells a KIT and says so: "Two separate
generations - never one". It declares TWO style fields, `## Style field —
INTRO STING` (line 8, 420 chars) and `## Style field — LOOPABLE TALK BED`
(line 14, 422 chars). The planner took the first block and was fixed under card
t_3497b627 (`--style-field`, from the queue entry's `styleField:`). The CDP
rail — `music/suno-gen.py` — carried the SAME defect on the other reader of a
style field:

    m = re.search(r"## Style field.*?```text\\n(.*?)```", text, re.S)

Measured against the pre-fix revision (sha256
9698f3302730e2d9d7f2d11a4ebd0c44c6a6244152cb14f3fe5ed164ee61eced):

    load_style_prompt("commentary-beds")                      -> 420 chars, the
        STING, byte-identical to field #1 (field #2 is 422 chars)
    load_style_prompt("commentary-beds", "LOOPABLE TALK BED") -> TypeError:
        load_style_prompt() takes 1 positional argument but 2 were given

So the kit's bed was unreachable from the rail: a run could only ever generate
the sting, for a genre that sells two half-products, and the manifest could not
say which half had been generated.

THE DECISION (the card's option 1 signature, backed by option 2's shared parser)
    `load_style_prompt(genre, style_field=None)` mirrors the planner: exactly
    one declared field -> the selector is optional; two or more -> the selector
    is REQUIRED, an unknown name is fatal, and there is NO fallback to the first
    block. The parser is NOT re-implemented here: `suno-gen.py` calls the
    planner's own `parse_style_fields()` / `resolve_style_caption()` through
    `planner_module()`, so the rail and the planner cannot drift (this file
    pins that with a case that compares them over every template).

WHY THIS TEST IS STANDALONE: the planner suite is standalone for the same
reason - these must run wherever `python3` runs, including the gate matrix
(`music/gates/check_gate_suite.sh` section 20) and the daily
`music/scripts/run_gate_matrix.sh`, with no pytest.

Exit codes: 0 = every case holds, 1 = at least one failed, 2 = usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
SUNO_GEN = REPO / "music" / "suno-gen.py"
PLANNER = REPO / "music" / "planner" / "planner.py"
PROMPTS = REPO / "music" / "prompts"
KIT = "commentary-beds"

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Register it the way a real `import` does. `exec_module` alone does NOT put
    # the module in sys.modules, and suno-gen's `planner_module()` reuses an
    # already-loaded planner precisely so one process holds one parser - the
    # registration is what makes that reuse reachable (and observable) here.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def style_blocks(genre: str) -> list[str]:
    """Every `## Style field` section's fenced block, as the template states them."""
    raw = (PROMPTS / f"{genre}.md").read_text(encoding="utf-8")
    parts = re.split(r"^##[ \t]*Style field[^\n]*$", raw, flags=re.M)[1:]
    return [re.search(r"```(?:text)?\n(.*?)```", p, re.S).group(1).strip()
            for p in parts if re.search(r"```(?:text)?\n(.*?)```", p, re.S)]


def raises(fn, *a) -> tuple[bool, str]:
    """(did it exit loudly, its message). Anything else is a FAIL, not a pass."""
    try:
        fn(*a)
    except SystemExit as e:
        return True, str(e)
    except Exception as e:  # noqa: BLE001 - an unexpected exception is not the refusal
        return False, f"{type(e).__name__}: {e}"
    return False, "(returned without refusing)"


def resolved(genre: str, field=None) -> tuple[str, str]:
    """The rail's (name, caption), or an error marker when it cannot answer.

    On a revision that has no `load_style_field` at all (the pre-fix rail this
    test is RED against) every case below must report FAIL - not crash the
    suite - so a missing method is turned into a value that cannot equal the
    expected text.
    """
    try:
        return sg.load_style_field(genre, field)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        return "", f"<{type(e).__name__}: {e}>"


def rail_planner():
    """The rail's planner module, or None when the revision has no such hook."""
    try:
        return sg.planner_module()
    except Exception:  # noqa: BLE001
        return None


def rail_prompt(genre: str, field=None) -> str:
    """The rail's `load_style_prompt`, or an error marker when it cannot answer."""
    try:
        return sg.load_style_prompt(genre, field)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        return f"<{type(e).__name__}: {e}>"


def main() -> int:
    global sg
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--suno-gen", default=str(SUNO_GEN),
                    help="the revision under test (default: this repo's)")
    args, _unknown = ap.parse_known_args()

    src = pathlib.Path(args.suno_gen).resolve()
    if not src.is_file():
        print(f"FAIL test_suno_gen_style_field: no such file: {src}")
        return 2
    sg = _load("suno_gen_under_test", src)
    # The RED run loads a copy of an older revision from OUTSIDE the repo, and
    # the module derives REPO from its own __file__ - point it at the real tree
    # so the template under test is the real template, not a fake one.
    sg.REPO = REPO
    sg.PROMPTS_DIR = PROMPTS
    sg.PLANNER_PATH = PLANNER
    pl = _load("planner_for_style_field_test", PLANNER)

    print(f"suno-gen under test: {src}")
    print(f"sha256             : {hashlib.sha256(src.read_bytes()).hexdigest()}")
    print()

    # -----------------------------------------------------------------------
    print("1. the template still sells TWO products (neither may be dropped)")
    blocks = style_blocks(KIT)
    heads = re.findall(r"^##[ \t]*Style field[^\n]*$", (PROMPTS / f"{KIT}.md").read_text(), re.M)
    check(f"{KIT} declares two style headings, named",
          [h.split("—")[-1].strip().split(" (")[0] for h in heads]
          == ["INTRO STING", "LOOPABLE TALK BED"],
          str(heads))
    check("both blocks are present, non-empty and different",
          len(blocks) == 2 and all(blocks) and blocks[0] != blocks[1],
          str([len(b) for b in blocks]))
    check("the sting and the bed measure 420 and 422 chars",
          [len(b) for b in blocks] == [420, 422], str([len(b) for b in blocks]))
    check("block #1 is the sting and block #2 is the bed",
          blocks[0].startswith("short podcast intro theme")
          and blocks[1].startswith("minimal instrumental podcast talk bed"))

    # -----------------------------------------------------------------------
    print()
    print("2. naming a field returns THAT field (RED against the pre-fix rail)")
    got_name, got_bed = resolved(KIT, "LOOPABLE TALK BED")
    check("naming 'LOOPABLE TALK BED' resolves it by name",
          got_name == "LOOPABLE TALK BED", repr(got_name))
    check("its caption IS field #2 and is NOT field #1",
          got_bed == blocks[1] and got_bed != blocks[0], repr(got_bed[:60]))
    check("load_style_prompt(genre, style_field) returns the same text",
          rail_prompt(KIT, "LOOPABLE TALK BED") == blocks[1],
          repr(rail_prompt(KIT, "LOOPABLE TALK BED")[:60]))
    _, got_sting = resolved(KIT, "INTRO STING")
    check("naming 'INTRO STING' resolves field #1",
          got_sting == blocks[0] and got_sting != blocks[1], repr(got_sting[:60]))
    _, got_lower = resolved(KIT, "loopable talk bed")
    check("the name match is case-insensitive, like the planner's",
          got_lower == blocks[1], repr(got_lower[:60]))

    # -----------------------------------------------------------------------
    print()
    print("3. no fallback: the refusals are the behaviour under test")
    ok, msg = raises(lambda: sg.load_style_field(KIT))
    check(f"omitting the selector on a two-field template REFUSES ({msg.splitlines()[0][:60]!r})",
          ok and "carries 2 style fields" in msg, msg[:160])
    # The refusal must not have leaked a caption: prove the FIRST block is not
    # what a caller gets for an omission.
    check("  and the refusal is not a silent fallback to field #1",
          not ok or blocks[0] not in msg, "the sting's text came back in the refusal")
    ok, msg = raises(lambda: sg.load_style_field(KIT, "LOOPABLE BED"))
    check(f"an unknown name REFUSES ({msg.splitlines()[0][:60]!r})",
          ok and "unknown styleField" in msg, msg[:160])
    _, trimmed = resolved(KIT, "INTRO STING ")
    check("a name that differs only by surrounding space still matches (planner rule)",
          trimmed == blocks[0], repr(trimmed[:50]))

    # -----------------------------------------------------------------------
    print()
    print("4. the 13 single-field templates are untouched, and still refuse a wrong name")
    for genre in sorted(p.stem for p in PROMPTS.glob("*.md") if p.stem != KIT):
        want = style_blocks(genre)
        if len(want) != 1:
            check(f"{genre}: exactly one style field", False, str(len(want)))
            continue
        _, got = resolved(genre)
        check(f"{genre}: no selector needed, and it is the template's block",
              got == want[0], f"{len(got)} vs {len(want[0])} chars")
    ok, msg = raises(lambda: sg.load_style_field("chiptune-8bit", "NOPE"))
    check("a name on a one-field template is a hard failure, not ignored",
          ok and "unknown styleField" in msg, msg[:160])

    # -----------------------------------------------------------------------
    print()
    print("5. genre-agnostic: a synthetic kit under a name that is not commentary-beds")
    # The card forbids special-casing commentary-beds by name: the resolver must
    # be driven by what the TEMPLATE declares and what the CALLER states. This
    # drives the rail's own loader against a made-up genre whose template has
    # two named fields.
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / "any-kit-genre.md").write_text(
            "# any-kit-genre — prompt template\n\n"
            "## Style field - ALPHA (11/1000 chars)\n\n```text\nalpha text\n```\n\n"
            "## Style field - BETA (10/1000 chars)\n\n```text\nbeta text\n```\n",
            encoding="utf-8")
        rail_pl = rail_planner()
        check("the rail exposes the parser it resolves through", rail_pl is not None,
              "no planner_module() on this revision")
        if rail_pl is not None:
            old_sg, old_pl = sg.PROMPTS_DIR, rail_pl.PROMPT_DIR
            sg.PROMPTS_DIR, rail_pl.PROMPT_DIR = tmp, tmp
            try:
                name, caption = resolved("any-kit-genre", "BETA")
                check("the SECOND field of an unrelated genre resolves by name",
                      (name, caption) == ("BETA", "beta text"), f"{name!r} {caption!r}")
                ok, msg = raises(lambda: sg.load_style_field("any-kit-genre"))
                check("and an omission there refuses as well",
                      ok and "carries 2 style fields" in msg, msg[:160])
                ok, msg = raises(lambda: sg.load_style_field("any-kit-genre", "GAMMA"))
                check("and an unknown name there refuses too",
                      ok and "unknown styleField" in msg, msg[:160])
            finally:
                sg.PROMPTS_DIR, rail_pl.PROMPT_DIR = old_sg, old_pl

    # -----------------------------------------------------------------------
    print()
    print("6. the rail and the planner share ONE parser (nothing to drift)")
    raw = (PROMPTS / f"{KIT}.md").read_text(encoding="utf-8")
    rail_pl = rail_planner()
    rail = ([(f["name"], f["caption"]) for f in rail_pl.parse_style_fields(raw)]
            if rail_pl is not None else [])
    plan = [(f["name"], f["caption"]) for f in pl.parse_style_fields(raw)]
    check("the rail's module IS the planner's parser (one instance, one source)",
          rail_pl is pl and pathlib.Path(pl.__file__).resolve() == PLANNER.resolve(),
          f"{getattr(rail_pl, '__file__', None)}")
    check("both readers enumerate the same two kit fields, in the same order",
          rail == plan == [("INTRO STING", blocks[0]), ("LOOPABLE TALK BED", blocks[1])],
          str([n for n, _ in rail]))
    names = sorted(p.stem for p in PROMPTS.glob("*.md"))
    disagree = []
    for g in names:
        r = (PROMPTS / f"{g}.md").read_text(encoding="utf-8")
        a = ([(f["name"], f["caption"]) for f in rail_pl.parse_style_fields(r)]
             if rail_pl is not None else [])
        b = [(f["name"], f["caption"]) for f in pl.parse_style_fields(r)]
        if a != b:
            disagree.append(g)
    check(f"all {len(names)} templates parse identically on both rails",
          not disagree, str(disagree))

    # -----------------------------------------------------------------------
    print()
    if fails:
        print(f"RESULT: FAIL ({len(fails)})")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
