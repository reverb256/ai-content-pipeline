#!/usr/bin/env python3
"""render_state — the render rail's marker state machine (card t_69cab80b).

WHY THIS FILE EXISTS (board music, measured 2026-10-16)
--------------------------------------------------------
The render rail (`music-pipeline-render`, ns mining) decided whether to render a
plan from ONE thing: `if <stem>.rendered exists: skip "already rendered"`. It
then wrote BOTH of its outcomes to that same path:

    if r.returncode == 0:
        marker.write_text("")           # rendered
    elif r.returncode == 1:
        marker.write_text("refused\\n")  # refused: a human must edit the sheet

So a refusal was stored as "finished", and nothing in either repo ever removed
the file. Measured live at 14:5x on 2026-10-16:

    $ for f in /var/lib/music-plans/*.rendered; do echo "$f -> $(cat $f)"; done
    anime-ending-reflections.rendered            -> refused
    epic-orchestral-boss-the-last-gate.rendered  -> refused
    smoke-chill-lounge.rendered                  -> refused
    testplan.rendered                            -> refused
    trance-signal-before-dawn.rendered           -> refused
    final-round.rendered                         -> (empty)

The rail's own log says what that costs (job music-pipeline-render-29869781,
2026-10-16 16:41): `skip epic-orchestral-boss-the-last-gate (already rendered)`.
Four of the eight live queue entries are `lyricsMode: draft`, so the last mile
of each of those genres was blocked by a MARKER, not by the music.

THE RULE THIS FILE IMPLEMENTS (decided on card t_69cab80b)
----------------------------------------------------------
Two outcomes need two states, and the state must be readable:

    <stem>.rendered     empty                       = rendered (the pre-card form)
                        `rendered <sha> <utc>`      = rendered, and the plan it
                                                      was rendered from
    <stem>.refused      `refused <sha> <utc>`       = refused, and the plan it
                        + the refusal reason          was refused from
    <stem>.looprefused  reasons                     = sticky (t_b21aeb51)
    <stem>.noartifact   check dump                  = sticky (t_320bae4c)

A REFUSAL IS RE-ATTEMPTED WHEN THE PLAN CHANGES, and ONLY then. The refusal is
a local parse (`acestep_plan.py` refuses a scaffold before any network call), so
re-attempting every run would also be cheap — but it would re-print the same
refusal six times a day for every draft in the queue, and a state that is
re-decided on every run cannot carry the answer to "has the human written the
sheet yet?". The recorded plan fingerprint answers exactly that question: the
same bytes cannot produce a different verdict, different bytes must be tried.

THE STICKY STATES DO NOT CHANGE. `.looprefused` and `.noartifact` cost GPU time
or need a human to look at a path, so they are never re-attempted automatically
(t_b21aeb51, t_320bae4c). Only a refusal — which costs nothing — is re-entered.

A MARKER THAT CANNOT BE READ IS NOT A FINISHED RENDER. An empty `.rendered` and
a `rendered …` record mean finished; anything else (the legacy `refused` text, a
truncated write, a state this file does not know) means "attempt it once and
rewrite the state". The failure direction matters: an unreadable marker must
never be able to hold a plan below the render rail forever, which is the defect
this card exists to remove.

MODES
  --decide --plan FILE [--plans DIR] [--json]
      exit 0  ATTEMPT this plan; prints `attempt <stem> (<why>)`
      exit 1  SKIP it; prints `skip   <stem> (<why>)` — the rail prints this line
      exit 2  usage error
  --record --plan FILE [--plans DIR] --state {rendered,refused,looprefused,noartifact}
           [--detail TEXT | --detail-file FILE]
      Write that state and REMOVE every other state marker for the stem, so a
      stem has exactly one state. `rendered`/`refused` record the plan's sha256.
  --fingerprint --plan FILE
      Print the plan's sha256 (the value the markers carry).
  --check [--plans DIR] [--json]
      The live invariant. exit 0 = every marker agrees with what the rail reads;
      exit 1 = at least one marker is a state the rail must not honour (a
      refusal stored as `.rendered` is the one this card is about).
  --selftest
      Prove every behaviour on real files in a scratch directory.

THE RAIL RUNS THIS FILE, NOT A COPY OF THE RULE. The render CronJob calls
--decide for each plan and --record after each outcome, so the rule has ONE
definition and `music/tests/test_render_state.py` exercises the same bytes.

Usage:
  python3 music/scripts/render_state.py --decide --plan /var/lib/music-plans/x.json
  python3 music/scripts/render_state.py --record --plan /var/lib/music-plans/x.json \\
      --state refused --detail "7 section(s) have no lyrics"
  python3 music/scripts/render_state.py --check --plans /var/lib/music-plans
  python3 music/scripts/render_state.py --selftest
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
import tempfile
from pathlib import Path

# ── the state, in ONE place ─────────────────────────────────────────────────
RENDERED, REFUSED = "rendered", "refused"
LOOPREFUSED, NOARTIFACT = "looprefused", "noartifact"
STATE_SUFFIX = {
    RENDERED: ".rendered",
    REFUSED: ".refused",
    LOOPREFUSED: ".looprefused",
    NOARTIFACT: ".noartifact",
}
# The two states a refusal may be re-entered from. `.looprefused` and
# `.noartifact` are deliberately NOT here: they cost GPU time or a human's eyes
# (t_b21aeb51, t_320bae4c).
RE_ATTEMPTABLE = (REFUSED,)

OK, SKIP, USAGE = 0, 1, 2
# The record the success marker carries. The pre-card form of a success marker
# was an EMPTY file, and 8 of the live markers are empty, so empty stays a
# finished render — a check cannot be allowed to turn 8 finished plans back into
# work because the format grew a field.
RENDERED_PREFIX = "rendered "
REFUSED_PREFIX = "refused "
# The exact bytes the old rail wrote into `.rendered` when it refused a plan.
LEGACY_REFUSAL_TOKENS = ("refused", "refused\n")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan_fingerprint(plan: Path) -> str:
    """The plan's own bytes. Same bytes -> same verdict, so the same bytes must
    not buy a second refusal; different bytes must buy an attempt."""
    return hashlib.sha256(plan.read_bytes()).hexdigest()


def marker(plans: Path, stem: str, state: str) -> Path:
    return plans / f"{stem}{STATE_SUFFIX[state]}"


class Decision:
    def __init__(self, attempt: bool, state: str, reason: str, markers: dict | None = None):
        self.attempt = attempt
        self.state = state
        self.reason = reason
        self.markers = markers or {}

    def line(self, stem: str) -> str:
        verb = "attempt" if self.attempt else "skip   "
        return f"{verb} {stem} ({self.reason})"

    def as_dict(self, stem: str) -> dict:
        return {
            "stem": stem,
            "attempt": self.attempt,
            "state": self.state,
            "reason": self.reason,
            "markers": self.markers,
        }


def read_marker(path: Path) -> tuple[str, str]:
    """(kind, payload) for a `.rendered` file.

    kind is one of: "absent", "finished", "refusal", "unknown". `finished` and
    `unknown` are separated because they fail in opposite directions: finished
    means do not render again, unknown means render once and say why.
    """
    if not path.exists():
        return "absent", ""
    text = path.read_text(errors="replace")
    stripped = text.strip()
    if not stripped:
        return "finished", ""
    if stripped.startswith(RENDERED_PREFIX):
        return "finished", stripped
    first = stripped.split()[0] if stripped.split() else ""
    if stripped in LEGACY_REFUSAL_TOKENS or first == REFUSED.rstrip() \
            or stripped.startswith(REFUSED_PREFIX):
        return "refusal", stripped
    return "unknown", stripped


def read_refusal(path: Path) -> tuple[str | None, str]:
    """(recorded plan sha or None, reason) for a `.refused` file.

    None means the marker carries no fingerprint (the pre-card form, e.g. the
    live `/var/lib/music-plans/jungle-dnb-two-speeds.refused`, 0 bytes). The
    rail cannot tell whether the plan changed since such a marker was written,
    so it re-attempts once and records a fingerprint.
    """
    if not path.exists():
        return None, ""
    lines = path.read_text(errors="replace").splitlines()
    head = lines[0].strip() if lines else ""
    reason = "\n".join(lines[1:]).strip()
    if head.startswith(REFUSED_PREFIX):
        parts = head.split()
        if len(parts) >= 2 and len(parts[1]) == 64:
            return parts[1], reason
        return None, reason
    # A bare marker, or one written by a hand: no fingerprint.
    return None, "\n".join(lines).strip()


def decide(plan: Path, plans: Path | None = None) -> Decision:
    """The rail's whole rule, in one function."""
    plans = plans or plan.parent
    stem = plan.stem
    try:
        sha = plan_fingerprint(plan)
    except OSError as exc:
        # Cannot read the plan: attempting is the honest answer (the wrapper
        # will fail on the same file), and skipping forever is the bug.
        return Decision(True, "unreadable-plan",
                        f"the plan could not be read ({exc.__class__.__name__}) - attempting")

    tracked = {s: str(marker(plans, stem, s)) for s in STATE_SUFFIX}

    # 1. `.rendered` is the state that used to swallow refusals. Read what it SAYS.
    rendered = marker(plans, stem, RENDERED)
    kind, payload = read_marker(rendered)
    if kind == "refusal":
        return Decision(
            True, "legacy-refusal-in-rendered",
            f"the old rail wrote a REFUSAL into {rendered.name} (it says "
            f"{payload[:40]!r}); that is not a finished render, so this plan is "
            f"attempted once and the state is rewritten (card t_69cab80b)",
            tracked)
    if kind == "unknown":
        return Decision(
            True, "unreadable-rendered",
            f"{rendered.name} carries a state this rail does not know "
            f"({payload[:40]!r}); an unreadable marker is never read as a finished "
            f"render - attempting once and rewriting it",
            tracked)
    if kind == "finished":
        if payload:
            parts = payload.split()
            sha_of_render = parts[1] if len(parts) > 1 else "?"
            when = parts[2] if len(parts) > 2 else "?"
            return Decision(False, RENDERED,
                            f"already rendered (marker records plan sha "
                            f"{sha_of_render[:12]}... written {when})", tracked)
        return Decision(False, RENDERED,
                        "already rendered (empty marker - a render from the rail "
                        "before the marker recorded its state)", tracked)

    # 2. The sticky states. A human clears these; a re-render costs GPU and
    #    cannot repair either one (t_b21aeb51, t_320bae4c).
    if marker(plans, stem, LOOPREFUSED).exists():
        return Decision(False, LOOPREFUSED,
                        f"loop refused earlier - see {marker(plans, stem, LOOPREFUSED).name}",
                        tracked)
    if marker(plans, stem, NOARTIFACT).exists():
        return Decision(False, NOARTIFACT,
                        f"no deliverable at the documented render path - see "
                        f"{marker(plans, stem, NOARTIFACT).name}; a human clears it",
                        tracked)

    # 3. A refusal: skip only while the plan is the plan that was refused.
    refused = marker(plans, stem, REFUSED)
    if refused.exists():
        recorded, _reason = read_refusal(refused)
        if recorded is None:
            return Decision(
                True, f"{REFUSED}-unfingerprinted",
                f"{refused.name} carries no recorded plan fingerprint, so this rail "
                f"cannot tell whether the plan changed since the refusal - attempting "
                f"once and recording one (card t_69cab80b)", tracked)
        if recorded != sha:
            return Decision(
                True, f"{REFUSED}-changed",
                f"the plan CHANGED since it was refused (sha {recorded[:12]}... -> "
                f"{sha[:12]}...) - a human may have written the sheet: attempting",
                tracked)
        when = ""
        lines = refused.read_text(errors="replace").splitlines()
        if lines and len(lines[0].split()) > 2:
            when = f" at {lines[0].split()[2]}"
        return Decision(False, REFUSED,
                        f"refused{when} and the plan has NOT changed since (sha "
                        f"{sha[:12]}...) - waiting for a human to write the sheet", tracked)

    return Decision(True, "fresh", "no marker yet - never attempted", tracked)


def record(plan: Path, plans: Path | None, state: str, detail: str = "") -> Path:
    """Write `state` for this stem and remove every other state marker.

    Exactly one state per stem: a stem that is rendered is not refused, and a
    stem whose loop was refused is not rendered. Without this a corrected plan
    would carry its old `.refused` into its next render, and the two could
    disagree in the directory a human reads.
    """
    if state not in STATE_SUFFIX:
        raise ValueError(f"unknown state {state!r}")
    plans = plans or plan.parent
    stem = plan.stem
    target = marker(plans, stem, state)
    sha = plan_fingerprint(plan)
    if state in (RENDERED, REFUSED):
        body = f"{state} {sha} {utc_now()}\n"
        if state == REFUSED and detail:
            body += detail.strip() + "\n"
    else:
        body = (detail.strip() + "\n") if detail.strip() else f"{state}\n"
    for other in STATE_SUFFIX:
        if other != state:
            marker(plans, stem, other).unlink(missing_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def check(plans: Path) -> list[tuple[str, str]]:
    """The live invariant: every marker says a state the rail must honour.

    RED is a marker the rail is NOT allowed to honour, and the one this card is
    about is a refusal stored in `.rendered`: the old rail read ANY `.rendered`
    as `already rendered`, so a plan waiting for a human was reported finished
    forever. The card's suggested wording adds "while its plan is newer than the
    marker" — measured, that qualifier was true for 1 of the 5 live files
    (epic-orchestral-boss was re-planned by t_78bd4754), and the state itself is
    wrong in all 5, so every unreadable-state `.rendered` is RED here and the
    plan/marker mtimes are reported in the detail.
    """
    findings: list[tuple[str, str]] = []
    if not plans.is_dir():
        return [("RED", f"{plans} is not a directory - nothing can be checked")]
    plans_seen = {p.stem for p in plans.glob("*.json")}
    for rendered in sorted(plans.glob("*.rendered")):
        stem = rendered.name[: -len(".rendered")]
        kind, payload = read_marker(rendered)
        if kind in ("absent", "finished"):
            if kind == "finished" and payload:
                parts = payload.split()
                if len(parts) > 1 and len(parts[1]) == 64 and stem in plans_seen:
                    now = plan_fingerprint(plans / f"{stem}.json")
                    if now != parts[1]:
                        findings.append((
                            "NOTE",
                            f"{rendered.name}: records plan sha {parts[1][:12]}... but "
                            f"{stem}.json is now {now[:12]}... - a rendered plan is NOT "
                            f"re-rendered because the plan changed (that costs GPU); the "
                            f"record is for the reader"))
            continue
        plan = plans / f"{stem}.json"
        rel = ""
        if plan.exists():
            newer = plan.stat().st_mtime > rendered.stat().st_mtime
            rel = ("the plan is NEWER than the marker" if newer
                   else "the plan is not newer than the marker")
        findings.append((
            "RED",
            f"{rendered.name} holds {payload[:40]!r}, not a finished render "
            f"({rel}) - the old rail reads any .rendered as 'already rendered' "
            f"forever; the state belongs in {stem}.refused (card t_69cab80b)"))
    for refused in sorted(plans.glob("*.refused")):
        stem = refused.name[: -len(".refused")]
        recorded, _reason = read_refusal(refused)
        if recorded is None:
            findings.append((
                "NOTE",
                f"{refused.name} carries no recorded plan fingerprint - the rail "
                f"re-attempts it once and records one (card t_69cab80b)"))
            continue
        plan = plans / f"{stem}.json"
        if not plan.exists():
            findings.append((
                "NOTE", f"{refused.name} has no {stem}.json - an orphan marker "
                        f"the rail never reads"))
            continue
        now = plan_fingerprint(plan)
        if now != recorded:
            findings.append((
                "NOTE",
                f"{refused.name}: the plan CHANGED since the refusal "
                f"({recorded[:12]}... -> {now[:12]}...) - the next render run "
                f"re-attempts it (self-healing, not a defect)"))
    return findings


# ── selftest: the reds and the greens, on real files ────────────────────────
def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def expect(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    with tempfile.TemporaryDirectory() as td:
        plans = Path(td)
        stem = "selftest-stem"
        plan = plans / f"{stem}.json"

        def write_plan(body: str) -> None:
            plan.write_text(body, encoding="utf-8")

        def clean() -> None:
            for s in STATE_SUFFIX.values():
                (plans / f"{stem}{s}").unlink(missing_ok=True)

        # 1. fresh
        clean()
        write_plan('{"lyrics": "draft"}')
        d = decide(plan, plans)
        expect("a plan with no marker is attempted", d.attempt and d.state == "fresh",
               d.state)

        # 2. the pre-card success marker: empty = rendered, and 8 live markers are
        clean()
        (plans / f"{stem}.rendered").write_text("")
        d = decide(plan, plans)
        expect("an EMPTY .rendered is a finished render (the 8 live markers stay "
               "finished)", not d.attempt and d.state == RENDERED, d.state)

        # 3. THE DEFECT: the old rail's refusal written into .rendered
        clean()
        (plans / f"{stem}.rendered").write_text("refused\n")
        d = decide(plan, plans)
        expect("a refusal stored in .rendered is RE-ATTEMPTED (not 'already rendered')",
               d.attempt, d.state)
        expect("its message does NOT say 'already rendered'",
               "already rendered" not in d.reason, d.reason)
        expect("its message names the conflation and the card",
               "REFUSAL" in d.reason and "t_69cab80b" in d.reason, d.reason)

        # 4. a proper refusal marker: same plan -> skip; changed plan -> attempt
        clean()
        record(plan, plans, REFUSED, detail="7 section(s) have no lyrics")
        d = decide(plan, plans)
        expect("a fingerprinted refusal of the SAME plan is skipped",
               not d.attempt and d.state == REFUSED, d.state)
        write_plan('{"lyrics": "[Intro]\\nreal words a human wrote\\n"}')
        d = decide(plan, plans)
        expect("THE CARD'S TEST: the plan changes -> REFUSED plan is attempted again",
               d.attempt and d.state == f"{REFUSED}-changed", d.state)
        expect("the changed-plan message says the plan changed",
               "CHANGED" in d.reason, d.reason)

        # 5. the live legacy `.refused` (0 bytes, jungle-dnb-two-speeds)
        clean()
        (plans / f"{stem}.refused").write_text("")
        d = decide(plan, plans)
        expect("a .refused marker with NO fingerprint is attempted once",
               d.attempt and d.state == f"{REFUSED}-unfingerprinted", d.state)

        # 6. record replaces the state: a legacy .rendered refusal must not survive
        clean()
        write_plan('{"lyrics": "draft"}')
        (plans / f"{stem}.rendered").write_text("refused\n")
        record(plan, plans, REFUSED, detail="still a draft")
        expect("recording a refusal REMOVES the misleading .rendered",
               not (plans / f"{stem}.rendered").exists())
        expect("recording a refusal writes .refused with the plan's sha",
               read_refusal(plans / f"{stem}.refused")[0] == plan_fingerprint(plan))
        d = decide(plan, plans)
        expect("the migrated stem now skips (same plan, same refusal)",
               not d.attempt and d.state == REFUSED, d.state)

        # 7. and the human's edit opens it again, end to end
        write_plan('{"lyrics": "[Intro]\\nwritten at last\\n"}')
        d = decide(plan, plans)
        expect("the migration path is self-healing: edit -> attempt",
               d.attempt and d.state == f"{REFUSED}-changed", d.state)
        record(plan, plans, RENDERED)
        d = decide(plan, plans)
        expect("a rendered plan is skipped and no .refused remains",
               not d.attempt and d.state == RENDERED
               and not (plans / f"{stem}.refused").exists(), d.state)

        # 8. sticky states are NOT re-attempted, even when the plan changed
        for sticky, suffix in ((LOOPREFUSED, ".looprefused"), (NOARTIFACT, ".noartifact")):
            clean()
            (plans / f"{stem}{suffix}").write_text("the seam is 33.6 dB down\n")
            d = decide(plan, plans)
            expect(f".{sticky} is sticky (a re-render costs GPU)", not d.attempt, d.state)
            write_plan('{"lyrics": "changed anyway"}')
            d = decide(plan, plans)
            expect(f".{sticky} stays sticky after a plan change", not d.attempt, d.state)

        # 9. an unreadable marker must not be a finished render
        clean()
        (plans / f"{stem}.rendered").write_text("??truncated")
        d = decide(plan, plans)
        expect("an unreadable .rendered is attempted, not trusted",
               d.attempt and d.state == "unreadable-rendered", d.state)

        # 10. --check: RED on the conflation, green on a consistent directory
        clean()
        (plans / f"{stem}.rendered").write_text("refused\n")
        findings = check(plans)
        expect("--check is RED on a refusal stored as .rendered",
               any(k == "RED" and ".rendered" in m for k, m in findings), str(findings))
        (plans / f"{stem}.rendered").unlink()
        record(plan, plans, REFUSED, detail="draft")
        findings = check(plans)
        expect("--check is green on a fingerprinted refusal",
               not [f for f in findings if f[0] == "RED"], str(findings))

    bad = 0
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  [{detail}]"))
        bad += 0 if ok else 1
    if bad:
        print(f"\n{len(checks) - bad}/{len(checks)} behaviours")
        print(f"BROKEN: {bad} behaviour(s) misbehaved")
        return 1
    print(f"\nOK: {len(checks)} behaviours "
          f"(a refused plan is re-attempted once its plan changes, and a refusal "
          f"can never be read as 'already rendered')")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="the render rail's marker state machine (card t_69cab80b)")
    ap.add_argument("--decide", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--fingerprint", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--plan", default=None, help="the plan JSON (its stem names the markers)")
    ap.add_argument("--plans", default=None, help="the plans dir (default: the plan's own dir)")
    ap.add_argument("--state", default=None, choices=sorted(STATE_SUFFIX))
    ap.add_argument("--detail", default="",
                    help="the reason to store in the marker (looprefused/noartifact "
                         "and the refusal's first line)")
    ap.add_argument("--detail-file", default=None,
                    help="read the reason from this file instead (the check's dump)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    modes = [args.decide, args.record, args.fingerprint, args.check, args.selftest]
    if sum(1 for m in modes if m) != 1:
        print("usage: pick exactly one of --decide, --record, --fingerprint, "
              "--check, --selftest", file=sys.stderr)
        return USAGE

    if args.selftest:
        return selftest()

    if args.check:
        plans = Path(args.plans or "/var/lib/music-plans")
        findings = check(plans)
        red = [f for f in findings if f[0] == "RED"]
        if args.json:
            print(json.dumps({"plans": str(plans),
                              "findings": [{"level": k, "detail": m} for k, m in findings],
                              "red": len(red)}, indent=2))
        else:
            for level, message in findings:
                print(f"{level:5s} {message}")
            print(f"{plans}: {len(red)} marker(s) the rail must not honour, "
                  f"{len(findings) - len(red)} note(s)")
        return 1 if red else OK

    if not args.plan:
        print(f"usage: this mode needs --plan", file=sys.stderr)
        return USAGE
    plan = Path(args.plan)
    plans = Path(args.plans) if args.plans else plan.parent

    if args.fingerprint:
        print(plan_fingerprint(plan))
        return OK

    if args.decide:
        d = decide(plan, plans)
        if args.json:
            print(json.dumps(d.as_dict(plan.stem), indent=2))
        else:
            print(d.line(plan.stem))
        return OK if d.attempt else SKIP

    # --record
    if not args.state:
        print("usage: --record needs --state", file=sys.stderr)
        return USAGE
    detail = args.detail
    if args.detail_file:
        detail = Path(args.detail_file).read_text(errors="replace")
    target = record(plan, plans, args.state, detail=detail)
    print(f"state  {plan.stem} -> {target.name}")
    return OK


if __name__ == "__main__":
    sys.exit(main())
