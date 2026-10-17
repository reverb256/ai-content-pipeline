G1: Core modules import cleanly  |  CHECK: bash music/sunolocal/checks/g1_imports.sh  |  EXPECT: G1-OK
G2: Store roundtrip with negative controls  |  CHECK: bash music/sunolocal/checks/g2_store.sh  |  EXPECT: G2-OK
G3: Suno to engine mappings and defaults  |  CHECK: bash music/sunolocal/checks/g3_translate.sh  |  EXPECT: G3-OK
G4: Live HTTP API end-to-end with fixture engine  |  CHECK: bash music/sunolocal/checks/g4_api.sh  |  EXPECT: G4-OK
G5: Adapter contracts against stub renderer and mock HTTP  |  CHECK: bash music/sunolocal/checks/g5_adapters.sh  |  EXPECT: G5-OK
G6: Scope integrity and no shipped stubs  |  CHECK: bash music/sunolocal/checks/g6_scope.sh  |  EXPECT: G6-OK
G7: Pipeline-wrapper contract (top-level audio_url + live wrapper run)  |  CHECK: bash music/sunolocal/checks/g7_wrapper_contract.sh  |  EXPECT: PASS g7 (regression: t_36ca4e7c — t_a77c505b shipped a wrapper that never ran once before merge)
G8: Explicit tempo + key contract (bpm / keyscale on the wire body)  |  CHECK: bash music/sunolocal/checks/g8_tempo_key_contract.sh  |  EXPECT: G8-OK (regression: t_25a6499c D1/D2 — `bpm` was hardcoded 120 and `key` was the whole style caption; G3 could not catch either because it asserted only `60 <= bpm <= 240` and pinned the D2 defect)

Lane-only gates (in checks/, NOT ledger lines above)
----------------------------------------------------
Three gates in this directory are deliberately absent from the ledger above.
Each needs a live GPU window or this repo's own `music/` tree, so the unlazy
checker can never MET them from here, and a permanent red line in the ledger is
a ledger nobody reads. They are real gates — run them by hand from this repo
root; they fail loudly when their precondition is missing instead of skipping:

  checks/g7_ace_step_render.sh   ACE-Step live render through acestep_plan.py.
                                 Preconditions: ComfyUI reachable at
                                 http://localhost:32188, ACE-Step nodes and
                                 models provisioned, ffprobe on PATH.
                                 Run: bash music/sunolocal/checks/g7_ace_step_render.sh
                                 Pass line: G7-OK
  checks/g8_yue2_render.sh       YuE2-3B live render on the 3090.
                                 Preconditions: 3090 with >= 2048 MiB free,
                                 /home/j_kro/Work/YuE present, YuE venv Python.
                                 Run: bash music/sunolocal/checks/g8_yue2_render.sh
                                 Pass line: G8-OK
  checks/g9_instrumental.sh      Instrumental mode end to end: translate.py
                                 plus music/suno-gen.py (is_instrumental_template,
                                 load_track, --dry). Needs this repo's music/
                                 tree; no GPU.
                                 Run: bash music/sunolocal/checks/g9_instrumental.sh
                                 Pass line: G9-OK

Two files are named g7_/g8_ beside a ledger gate of the same number
(g7_wrapper_contract.sh, g8_tempo_key_contract.sh). The names are kept as they
are because briefs cite them by path; the ledger order, not the file prefix, is
what the checker numbers.

This file is one of the files card t_42bc85ba keeps byte-identical between this
tree and the deployed mirror (helm/charts/sunolocal/files/music/sunolocal). Edit
the lane repo first, then run helm/charts/sunolocal/check-sunolocal-sync.sh in
mining-k8s.
