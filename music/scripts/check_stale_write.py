#!/usr/bin/env python3
"""check_stale_write — REFUSE a change whose content is older than the bytes the
branch already carries: a stale write, i.e. a would-be revert of a committed hunk.

WHY THIS EXISTS
---------------
INCIDENT (2026-10-16, cards t_96dfc521 / t_3497b627 / t_69cab80b / t_42bc85ba,
follow-up card t_8dadd6cb). `/home/j_kro/ai-content-pipeline` is ONE git working
tree that every concurrently running music card writes to. A card that writes a
WHOLE FILE from a snapshot it read earlier puts back content that another card
has already committed. Nothing fails; the check that the lost bytes implemented
just stops running.

Measured on this repo, from real commits (not from a description):

    $ git show 9082ce3:music/gates/check_gate_suite.sh | grep -c 'planner regression suite'
    1
    $ git show edeef61:music/gates/check_gate_suite.sh | grep -c 'planner regression suite'
    0

9082ce3 (card t_96dfc521) added section 13 to the gate suite, wiring the planner
regression suite into the daily acceptance matrix. edeef61 (card t_69cab80b)
rewrote that file from a stale copy and the section was gone. It was re-landed as
a31deb2. Same mechanism, second instance: 5cb2e3d (card t_7a528617) committed
from the shared tree while it still held pre-change copies of card t_450e7f39's
files and REVERTED that card's landing 6eb5a23 seven seconds after it landed.

The sibling guard `music/scripts/git_commit_fence.sh` (card t_6d0b7dd7, doc
`music/docs/SHARED-TREE.md`) fences the SCOPE of a commit: the shared index
carries a sibling's staged files. It cannot see content, so it ALLOWS the commit
that dropped section 13 — that commit named its paths and used a private index.
This check is the other half: the CONTENT.

THE RULE (measured, not invented)
---------------------------------
For a path P with base content A (the bytes the branch carries) and candidate
content S (the bytes being committed):

    dropped   = the substantive lines of A that the diff to S removes or replaces
    kept      = the substantive lines of A that S retains
    age(c)    = `git rev-list --count c..<base>`   (0 = base itself, larger = older)

    REFUSE when dropped is non-empty, kept is non-empty, and
    min age(dropped) < min age(kept): the change drops a line YOUNGER than every
    line it kept, so the writer's snapshot predates that line.

That is a fact about provenance, not a guess about intent: blame (positional, at
the base revision) names the commit that introduced each line.

Blame MUST be positional. A content-keyed origin is meaningless here: this repo's
gate suite alone has ~150 blank lines and a repeated separator comment, so
"origin of the text '#'" spans dozens of commits and every comparison collapses.
Measured: with content-keyed origins edeef61 is NOT flagged (the dropped lines
and the kept separator lines share the youngest origin); with positional blame it
is, naming 9082ce3.

The SUBSTANTIVE filter (blank lines and pure separator / comment-punctuation
lines are ignored) is what keeps the rule quiet. Measured over the last 150
commits of this repo:

    rule variant                                      flags
    dropped is a SUBSET of the newest change            133   (useless)
    dropped INTERSECTS the newest change                172   (useless)
    dropped intersects ANY of the last 5 changes        248   (useless)
    provenance, content-keyed blame                     n/a   (misses edeef61)
    provenance, POSITIONAL blame + substantive filter     11   <- this one

and it catches both recorded incidents (edeef61, 5cb2e3d) with one false
positive class: a card that deliberately removes bytes another card just added
(the re-land 176b575 of 6eb5a23). That case is real work and must not be
blocked — it must be DECLARED. See the override below.

MODES
-----
    --staged            the paths THIS commit carries (index vs HEAD). The
                        pre-commit hook slot runs it; git sets $GIT_INDEX_FILE to
                        the commit's own index, so a named-paths commit is
                        measured on exactly the paths it names and a sibling's
                        staged work is not touched.
    --rev REV           audit one commit against its parent
    --range A..B        audit every non-merge commit in the range
    --since REF         audit the commits reachable from HEAD and not from REF
                        (the daily leg: what landed in the last day)
    --push              pre-push: refs on stdin (local_ref local_sha remote_ref
                        remote_sha); audits the commits about to be PUBLISHED
    --armed             assert the guard is armed here and run its suite

EXIT CODES
----------
    0 allow | 1 refuse (a stale write; in audit mode: a regression landed)
    2 usage | 3 cannot measure (no repo, no such rev). 3 is reported, never
    returned as 0 — a check that cannot measure must not read as a pass.

ESCAPES (each names the reason; each belongs in the card)
---------------------------------------------------------
    KANBAN_STALE_WRITE=off                 emergency, for a tree only you are in
    KANBAN_STALE_WRITE=<sha>[,<sha>...]    DECLARE the origin commit(s) whose
                                           bytes you intend to drop. The shas
                                           must be the ones this check named, so
                                           an override cannot mute it silently.
                                           Add the same declaration to the
                                           commit message, on its own line:

        Stale-write-dropped: <sha>[,<sha>]

    The env var clears the commit that is in flight. The TRAILER is what the
    audit reads (--rev / --range / --since / --push), because the audit sees
    history and not an environment: a commit whose message names the origin
    bytes it drops is reported as "declared" and is not refused, so a legitimate
    rollback does not make the daily leg red. Nothing else silences it.

Regression suite: music/scripts/test_check_stale_write.py (planted defects; each
case drives a real `git commit` / `git push` through the armed hook).
Reference: kanban t_8dadd6cb. Doc: music/docs/STALE-WRITE.md.
"""

from __future__ import annotations

import argparse
import collections
import difflib
import json
import os
import re
import subprocess
import sys

# A line that carries no committed content: blank, or nothing but comment
# punctuation / separators. Such a line's blame origin is an artifact of where a
# hunk was inserted, so it must never decide the verdict.
TRIVIAL = re.compile(rb"^[#/;*<>\-=_. ]*$")

# How many commits that touched a path to search for the exact-rollback case.
ROLLBACK_WINDOW = 30

CARD_RE = re.compile(rb"\(t_[0-9a-f]{8}\)")


def git(*args: str, repo=None) -> bytes | None:
    """Run git. Returns stdout as BYTES, or None when git failed.

    Bytes, always: this check compares blobs, and a media repo holds non-UTF-8
    files (measured: `git show <rev>:<png>` raises UnicodeDecodeError when read
    as text).
    """
    cmd = ["git"]
    if repo:
        cmd += ["-C", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def git_text(*args: str, repo=None) -> str:
    out = git(*args, repo=repo)
    return out.decode("utf-8", "replace") if out is not None else ""


def rev_parse(rev, repo=None):
    out = git("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}", repo=repo)
    return out.decode().strip() if out else None


def blob(rev, path, repo=None):
    """File content at rev:path, or None when absent. None also for a symlink
    target that git stores as a blob with a weird mode - content is content."""
    out = git("show", f"{rev}:{path}", repo=repo)
    return out


def index_blob(path, repo=None):
    return git("show", f":{path}", repo=repo)


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:8000]


class Repo:
    def __init__(self, path):
        self.path = path
        self._blame = {}
        self._age = {}
        self._name_status = {}

    # ---- git helpers -------------------------------------------------------
    def lines(self, rev, path):
        data = blob(rev, path, self.path)
        if data is None:
            return None
        if is_binary(data):
            return None
        return tuple(data.split(b"\n"))

    def blob_id(self, rev, path):
        out = git("rev-parse", "--verify", "--quiet", f"{rev}:{path}", repo=self.path)
        return out.decode().strip() if out else None

    def blame(self, rev, path):
        """line number (1-based at `rev`) -> origin commit."""
        key = (rev, path)
        if key in self._blame:
            return self._blame[key]
        out = git("blame", "--porcelain", "-l", rev, "--", path, repo=self.path)
        idx = {}
        if out is not None:
            for raw in out.split(b"\n"):
                if not raw or raw[0:1] == b"\t":
                    continue
                parts = raw.split(b" ", 3)
                if len(parts) >= 3 and len(parts[0]) == 40:
                    try:
                        int(parts[0], 16)
                        int(parts[2])
                    except ValueError:
                        continue
                    idx[int(parts[2])] = parts[0].decode()
        self._blame[key] = idx
        return idx

    def age(self, commit, base):
        """Commits between `commit` and `base`. 0 = commit IS base."""
        key = (commit, base)
        if key not in self._age:
            if commit == base:
                self._age[key] = 0
            else:
                out = git("rev-list", "--count", f"{commit}..{base}", repo=self.path)
                self._age[key] = int(out) if out else None
        return self._age[key]

    def card_of(self, commit):
        """The card id a lane commit names, from its subject: '(t_xxxxxxxx)'."""
        if not commit:
            return None
        out = git("log", "-1", "--format=%s", commit, repo=self.path)
        if not out:
            return None
        m = CARD_RE.search(out)
        return m.group(0)[1:-1].decode() if m else None

    def changed_paths(self, rev, base):
        out = git("diff", "--name-only", "-z", base, rev, repo=self.path)
        if out is None:
            return []
        return [p.decode("utf-8", "replace") for p in out.split(b"\0") if p]

    # ---- the rule ----------------------------------------------------------
    def verdict(self, path, base_rev, candidate, candidate_is_index=False):
        """Verdict for one path. Returns (kind, detail, refusal_or_None)."""
        # Blob ids first: they are exact, they work on binary paths (a .png, a
        # .flac), and a rollback can be named from them alone. The line-based
        # rule below is text-only.
        if candidate_is_index:
            s_id = git("rev-parse", "--verify", "--quiet", f":{path}", repo=self.path)
            s_id = s_id.decode().strip() if s_id else None
        else:
            s_id = self.blob_id(candidate, path)
        a_id = self.blob_id(base_rev, path)

        if a_id is None:
            return "ADDED", {"path": path}, None          # new path: nothing to lose
        if s_id is None:
            return "DELETED", {"path": path}, None        # whole file gone: see doc
        if a_id == s_id:
            return "OK", {"path": path}, None

        det = {"path": path}
        # 1. exact rollback: the candidate IS an older revision of this path.
        roll = self.rollback_origin(path, base_rev, s_id)
        if roll:
            det.update(rollback=roll[0][:8], rollback_card=roll[1])
            return "ROLLBACK", det, det

        # 2. provenance: does the change drop a line younger than everything kept?
        A = self.lines(base_rev, path)
        if candidate_is_index:
            data = index_blob(path, self.path)
            S = None if data is None or is_binary(data) else tuple(data.split(b"\n"))
        else:
            S = self.lines(candidate, path)
        if A is None or S is None:
            det["note"] = "binary or unreadable content: only the rollback rule applies"
            return "NOTE", det, None
        sm = difflib.SequenceMatcher(None, A, S, autojunk=False)
        del_idx, keep_idx = [], []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("delete", "replace"):
                del_idx.extend(range(i1, i2))
            elif tag == "equal":
                keep_idx.extend(range(i1, i2))
        substantive = [not TRIVIAL.match(x) for x in A]
        del_idx = [i for i in del_idx if substantive[i]]
        keep_idx = [i for i in keep_idx if substantive[i]]
        det["dropped_lines"] = len(del_idx)
        if not del_idx:
            return "OK", det, None
        if not keep_idx:
            return "REWRITE", det, None                   # nothing in common: unsigned

        bl = self.blame(base_rev, path)
        if not bl:
            det["note"] = "no blame available"
            return "NOTE", det, None

        def ages(idx):
            out = []
            for i in idx:
                c = bl.get(i + 1)
                if not c:
                    continue
                a = self.age(c, base_rev)
                if a is not None:
                    out.append((a, c))
            return out

        da, ka = ages(del_idx), ages(keep_idx)
        if not da or not ka:
            det["note"] = "no origins resolved"
            return "NOTE", det, None
        md, mk = min(x[0] for x in da), min(x[0] for x in ka)
        det["youngest_dropped_age"] = md
        det["youngest_kept_age"] = mk
        if md >= mk:
            return "OK", det, None

        owners = sorted({c for a, c in da if a == md})
        det["owners"] = [{"commit": c, "card": self.card_of(c),
                          "subject": git_text("log", "-1", "--format=%s", c,
                                              repo=self.path).strip()}
                         for c in owners]
        det["dropped_sample"] = [A[i].decode("utf-8", "replace")
                                 for i in del_idx][:6]
        return "STALE", det, det

    def rollback_origin(self, path, base_rev, s_id):
        """If the candidate content for path == this path's content at some
        recent commit that touched it, return (commit, card)."""
        if not s_id:
            return None
        out = git("log", f"-{ROLLBACK_WINDOW}", "--format=%H", base_rev, "--", path,
                  repo=self.path)
        if not out:
            return None
        for rev in out.decode().split():
            if self.blob_id(rev, path) == s_id:
                return (rev, self.card_of(rev))
        return None


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------
DECL_RE = re.compile(rb"^[ \t]*Stale-write-dropped:[ \t]*(.*)$", re.M)


def declaration_of(repo, rev):
    """The origin shas a commit DECLARES it drops.

    `Stale-write-dropped: <sha>[,<sha>]` in the commit message is the DURABLE
    form of the override: the env var only clears the commit that is in flight,
    while the trailer travels with the history, so the daily audit
    (run_gate_matrix.sh leg 2f) can tell a declared rollback from a stale write
    without asking anyone. Without it, a card that deliberately restores an
    older revision would make the audit red for a day.
    """
    if not rev:
        return set()
    body = git("log", "-1", "--format=%B", rev, repo=repo.path)
    if not body:
        return set()
    shas = set()
    for m in DECL_RE.finditer(body):
        for tok in re.split(rb"[,\s]+", m.group(1).strip()):
            tok = tok.strip()
            if tok and tok != b"-":
                shas.add(tok.decode())
    return shas


def declared(repo, rev, flagged):
    """True when this commit declares every origin sha it was flagged for."""
    if not rev:
        return False
    named = declaration_of(repo, rev)
    if not named:
        return False
    owners = {o["commit"] for _, _, _, d in flagged for o in d.get("owners", [])}
    for _, _, kind, d in flagged:
        if kind == "ROLLBACK":
            owners.add(d.get("rollback") or "")
    owners.discard("")
    if not owners:
        return False
    return all(any(o.startswith(n) or n.startswith(o[:len(n)]) for n in named)
               for o in owners)


class Report:
    def __init__(self, repo, mode):
        self.repo = repo
        self.mode = mode
        self.flagged = []
        self.checked = 0
        self.notes = []

    def add_change(self, label, path, kind, det):
        self.checked += 1
        if kind in ("STALE", "ROLLBACK"):
            self.flagged.append((label, path, kind, det))
        elif kind in ("REWRITE", "DELETED", "NOTE"):
            self.notes.append((label, path, kind))

    def refuses(self):
        return bool(self.flagged)

    def text(self, quiet=False):
        out = []
        for label, path, kind, det in self.flagged:
            if kind == "STALE":
                owners = ", ".join(
                    f"{o['commit'][:8]}" + (f" (card {o['card']})" if o["card"] else "")
                    for o in det.get("owners", []))
                out.append(f"REFUSE {label}: {path} drops content that landed in the "
                           f"branch later than the content it keeps")
                out.append(f"       {det['dropped_lines']} substantive line(s) removed; "
                           f"youngest removed origin age={det['youngest_dropped_age']}, "
                           f"youngest kept origin age={det['youngest_kept_age']}")
                out.append(f"       the bytes you are dropping were introduced by: {owners}")
                for o in det.get("owners", []):
                    if o.get("subject"):
                        out.append(f"         {o['commit'][:8]} {o['subject']}")
                for line in det.get("dropped_sample", [])[:4]:
                    out.append(f"         - {line[:100]}")
            else:
                out.append(f"REFUSE {label}: {path} is EXACTLY revision "
                           f"{det['rollback'][:8]}"
                           + (f" (card {det['rollback_card']})" if det.get('rollback_card') else "")
                           + " — a rollback to an older version of this path")
        if not quiet:
            for label, path, kind in self.notes:
                if kind == "DECLARED":
                    out.append(f"declared {label}: {path} — the commit message "
                               f"declares the origin bytes it drops")
                else:
                    out.append(f"note   {label}: {path} {kind.lower()} — not a stale "
                               f"write, not measured further")
        return out


# ---------------------------------------------------------------------------
# modes
# ---------------------------------------------------------------------------
def mode_staged(repo, base_ref, rep):
    base = rev_parse(base_ref, repo.path)
    if not base:
        # An unborn branch has no bytes to lose: the first commit of a fresh
        # repository cannot revert anything. Any OTHER unresolvable base is a
        # cannot-measure, never an allow.
        if base_ref == "HEAD" and not git("rev-parse", "--verify", "--quiet",
                                         "HEAD^{commit}", repo=repo.path):
            return 0, "no commits yet (unborn branch): nothing to compare against"
        return 3, f"cannot measure: no such revision {base_ref}"
    out = git("diff", "--name-only", "-z", "--cached", base, repo=repo.path)
    if out is None:
        return 3, "cannot measure: git diff --cached failed"
    paths = [p.decode("utf-8", "replace") for p in out.split(b"\0") if p]
    if not paths:
        return 0, "no staged paths"
    for path in paths:
        kind, det, _ = repo.verdict(path, base, None, candidate_is_index=True)
        rep.add_change("staged", path, kind, det)
    return (1 if rep.refuses() else 0), None


def audit_commit(repo, rev, rep):
    parent = git("rev-parse", "--verify", "--quiet", f"{rev}^", repo=repo.path)
    if parent is None:
        return
    parent = parent.decode().strip()
    added = []
    for path in repo.changed_paths(rev, parent):
        kind, det, _ = repo.verdict(path, parent, rev)
        rep.checked += 1
        if kind in ("STALE", "ROLLBACK"):
            added.append((rev[:8], path, kind, det))
        elif kind in ("REWRITE", "DELETED", "NOTE"):
            rep.notes.append((rev[:8], path, kind))
    if not added:
        return
    # A commit that declares the origin bytes it drops is not a stale write: it
    # is a rollback someone asked for, recorded in the history that travels.
    if declared(repo, rev, added):
        for label, path, _, _ in added:
            rep.notes.append((label, path, "DECLARED"))
        return
    rep.flagged.extend(added)


def mode_range(repo, spec, rep):
    rng = spec.split("..")
    if len(rng) != 2:
        return 2, "usage: --range A..B"
    out = git("rev-list", "--no-merges", spec, repo=repo.path)
    if out is None:
        return 3, f"cannot measure: no such range {spec}"
    for rev in out.decode().split():
        audit_commit(repo, rev, rep)
    return (1 if rep.refuses() else 0), None


def mode_since(repo, ref, rep):
    base = rev_parse(ref, repo.path)
    if not base:
        return 3, f"cannot measure: no such revision {ref}"
    out = git("rev-list", "--no-merges", f"{base}..HEAD", repo=repo.path)
    if out is None:
        return 3, "cannot measure: git rev-list failed"
    revs = out.decode().split()
    for rev in revs:
        audit_commit(repo, rev, rep)
    return (1 if rep.refuses() else 0), None


def mode_push(repo, stdin_text, rep):
    """pre-push stdin: <local ref> <local sha> <remote ref> <remote sha>."""
    zero = "0" * 40
    lines = [l.split() for l in stdin_text.splitlines() if l.strip()]
    if not lines:
        return 3, "cannot measure: no refs on stdin (not a pre-push invocation?)"
    ranged = False
    for parts in lines:
        if len(parts) < 4:
            continue
        local_sha, _remote_ref, remote_sha = parts[1], parts[2], parts[3]
        if set(local_sha) == {"0"}:
            continue                                  # a delete: nothing published
        if set(remote_sha) == {"0"}:
            # new remote branch: publish everything not already on any remote
            out = git("rev-list", "--no-merges", local_sha, "--not", "--remotes",
                      repo=repo.path)
        else:
            out = git("rev-list", "--no-merges", f"{remote_sha}..{local_sha}",
                      repo=repo.path)
        if out is None:
            return 3, f"cannot measure: rev-list for {local_sha[:8]} failed"
        ranged = True
        for rev in out.decode().split():
            audit_commit(repo, rev, rep)
    if not ranged:
        return 0, "nothing to publish"
    return (1 if rep.refuses() else 0), None


REFUSAL_HELP = """
  The bytes you are about to commit remove content that landed in this branch
  AFTER the content you kept, so your copy of the file predates it. This lane is
  ONE working tree that every concurrent card writes to: reading a file, editing
  it, and writing it back WHOLE loses whatever a sibling committed in between.
  Nothing else notices — the check those bytes implemented just stops running.

  Fix it by re-applying your change on top of the current bytes:

      git show HEAD:<path> > <path>     # the current bytes, then edit them

  Then re-run your own check. If you REALLY mean to drop those bytes, declare the
  origin commit(s) this check named — in your card, and in the commit message on
  its own line:

      Stale-write-dropped: <sha>[,<sha>]

  For the commit in flight, KANBAN_STALE_WRITE=<sha>[,<sha>] does the same thing;
  the TRAILER is what the daily audit reads, because it travels with the history.
  KANBAN_STALE_WRITE=off is the emergency override — explain it in your card.

  Reference: kanban t_8dadd6cb. Doc: music/docs/STALE-WRITE.md.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="check_stale_write.py", add_help=True,
        description="Refuse a change whose content is older than the branch's own bytes.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true",
                   help="the paths THIS commit carries (index vs HEAD)")
    g.add_argument("--rev", metavar="REV", help="audit one commit against its parent")
    g.add_argument("--range", metavar="A..B", help="audit a commit range")
    g.add_argument("--since", metavar="REF", help="audit commits in REF..HEAD")
    g.add_argument("--push", action="store_true", help="pre-push mode (refs on stdin)")
    g.add_argument("--armed", action="store_true",
                   help="assert the hook is armed here, and run the suite")
    ap.add_argument("--repo", default=None, help="repo (default: toplevel of $PWD)")
    ap.add_argument("--base", default="HEAD", help="--staged base revision")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-selftest", action="store_true",
                   help="--armed: assert the arming only, do not run the suite")
    args = ap.parse_args(argv)

    repo_dir = args.repo
    if not repo_dir:
        out = git("rev-parse", "--show-toplevel")
        if not out:
            print("check_stale_write: cannot measure: not inside a git work tree",
                  file=sys.stderr)
            return 3
        repo_dir = out.decode().strip()

    if args.armed:
        return armed(repo_dir, args)

    repo = Repo(repo_dir)
    rep = Report(repo, "staged" if args.staged else "audit")

    if args.staged:
        rc, msg = mode_staged(repo, args.base, rep)
    elif args.rev:
        rev = rev_parse(args.rev, repo_dir)
        if not rev:
            print(f"check_stale_write: cannot measure: no such revision {args.rev}",
                  file=sys.stderr)
            return 3
        audit_commit(repo, rev, rep)
        rc = 1 if rep.refuses() else 0
        msg = None
    elif args.range:
        rc, msg = mode_range(repo, args.range, rep)
    elif args.since:
        rc, msg = mode_since(repo, args.since, rep)
    else:
        rc, msg = mode_push(repo, sys.stdin.read(), rep)

    if msg:
        if rc >= 2:
            print(f"check_stale_write: {msg}", file=sys.stderr)
        elif not args.quiet:
            print(f"check_stale_write: {msg}")
        return rc

    lines = rep.text(quiet=args.quiet)
    if args.json:
        print(json.dumps({"mode": rep.mode, "checked": rep.checked,
                          "refused": rep.refuses(),
                          "flagged": [{"label": l, "path": p, "kind": k, "detail": d}
                                      for l, p, k, d in rep.flagged],
                          "notes": [{"label": l, "path": p, "kind": k}
                                    for l, p, k in rep.notes]}, indent=1))
        return rc

    if rep.refuses():
        # The override is a DECLARATION: it must name an origin commit this run
        # flagged, so it can never be a silent mute.
        allow = stale_write_override(rep)
        if allow is True:
            print("check_stale_write: ALLOW — KANBAN_STALE_WRITE names every origin "
                  "commit this check flagged; the drop is declared.")
            for l in lines[:1]:
                print("  " + l)
            return 0
        if allow is False:
            print("check_stale_write: REFUSE — KANBAN_STALE_WRITE does not name the "
                  "origin commit(s) this check flagged. An override must declare what "
                  "it drops.", file=sys.stderr)
        for l in lines:
            print(l, file=sys.stderr)
        print(REFUSAL_HELP, file=sys.stderr)
        return 1

    if not args.quiet:
        for l in lines:
            print(l)
        print(f"check_stale_write: PASS — {rep.checked} path-change(s) measured, "
              f"no stale write")
    return 0


def stale_write_override(rep):
    """True = declared, False = refused override, None = no override set."""
    val = os.environ.get("KANBAN_STALE_WRITE", "").strip()
    if not val:
        return None
    if val == "off":
        return True
    named = {s.strip() for s in val.split(",") if s.strip()}
    owners = {o["commit"] for _, _, _, d in rep.flagged for o in d.get("owners", [])}
    ok = bool(owners) and all(
        any(o.startswith(n) or n.startswith(o[:len(n)]) for o in owners) for n in named)
    return True if ok else False


def armed(repo_dir, args):
    """The guard must be ARMED: a hook is file state plus one local config key,
    and neither travels with the tree."""
    problems = []
    root = git("rev-parse", "--show-toplevel", repo=repo_dir)
    repo_dir = root.decode().strip() if root else repo_dir
    hooks_path = git_text("config", "--get", "core.hooksPath", repo=repo_dir).strip()
    if hooks_path != ".githooks":
        problems.append(f"core.hooksPath is {hooks_path or '(unset)'}, not .githooks")
    guard_rel = os.path.join("music", "scripts", "check_stale_write.py")
    guard = os.path.join(repo_dir, guard_rel)
    if not os.path.exists(guard):
        problems.append(f"no guard at {guard_rel}")
    elif not os.access(guard, os.X_OK):
        problems.append(f"{guard_rel} is not executable")
    armed_by = []
    for hook in ("pre-push", "pre-commit"):
        h = os.path.join(repo_dir, hooks_path or ".githooks", hook)
        if not os.path.exists(h):
            continue
        with open(h, "rb") as fh:
            body = fh.read()
        if b"check_stale_write" not in body:
            continue
        if not os.access(h, os.X_OK):
            problems.append(f".githooks/{hook} is not executable")
            armed_by.append(f"{hook} (NOT EXECUTABLE)")
        else:
            armed_by.append(hook)
    if not armed_by:
        problems.append("no hook runs check_stale_write (expected .githooks/pre-push "
                        "and/or .githooks/pre-commit)")
    if problems:
        print("check_stale_write --armed: DISARMED", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("  re-arm:  git config core.hooksPath .githooks; "
              "chmod +x .githooks/pre-push", file=sys.stderr)
        return 3
    print(f"check_stale_write --armed: ARMED by {', '.join(armed_by)} "
          f"(core.hooksPath={hooks_path})")
    if args.skip_selftest:
        return 0
    suite = os.path.join(repo_dir, "music", "scripts", "test_check_stale_write.py")
    if not os.path.exists(suite):
        print(f"  note: no planted-defect suite at music/scripts/"
              f"test_check_stale_write.py", file=sys.stderr)
        return 0
    r = subprocess.run([sys.executable, suite], capture_output=True)
    tail = r.stdout.decode("utf-8", "replace").strip().splitlines()
    for line in tail[-3:]:
        print("  " + line)
    if r.returncode != 0:
        print("check_stale_write --armed: the planted-defect suite FAILED",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
