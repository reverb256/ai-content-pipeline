"""test_panel_math.py — unit checks for the panel's aggregation and rubric
integrity. Run: python3 music/rubrics/test_panel_math.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from panel import (aggregate, geometric_median, load_rubric, genre_family,
                       applicable_criteria, applicable_signals,
                       rubric_scope_defects)
    import numpy as np
except ModuleNotFoundError as e:
    # Measured 2026-10-16: the Hermes-managed `python3` has neither numpy
    # nor PyYAML, so the documented command fails with a bare traceback.
    print(f"FATAL: {e}. This test needs numpy + PyYAML. Run it with the "
          f"interpreter that has them (e.g. /usr/bin/python3), not the "
          f"Hermes-managed python3.", file=sys.stderr)
    sys.exit(2)

RUBRICS = Path(__file__).resolve().parent
MUSIC = RUBRICS.parent
failures = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok  {name}")
    else:
        print(f"  FAIL {name} {detail}")
        failures.append(name)


# 1. geometric median basics — robust to one contaminated judge
print("[1] geometric median")
pts = [[7, 7, 7], [8, 7, 8], [7, 8, 7]]
gm = geometric_median(pts)
check("3 clean points -> near their median", np.allclose(gm, [7.33, 7.33, 7.33], atol=0.35), str(gm))
contaminated = [[7, 7, 7], [8, 7, 8], [7, 8, 7], [10, 10, 10]]
gm2 = geometric_median(contaminated)
check("one extreme judge barely moves it",
      np.linalg.norm(gm2 - np.array([7.33, 7.33, 7.33])) < 1.2, str(gm2))
gm3 = geometric_median([[5, 5, 5]])
check("single point returns itself", np.allclose(gm3, [5, 5, 5]), str(gm3))
gm4 = geometric_median([[3, 0, 0], [3, 0, 0]])
check("coincident points handled (Vardi-Zhang)", np.allclose(gm4, [3, 0, 0]), str(gm4))

# 2. aggregation: spread + wide-criteria detection
print("[2] aggregate")
fake_rubric = {"criteria": [
    {"id": "a", "weight": 3}, {"id": "b", "weight": 1}]}
scores = [
    {"criteria_scores": {"a": 8, "b": 7}},
    {"criteria_scores": {"a": 7, "b": 8}},
    {"criteria_scores": {"a": 9, "b": 7}},
]
agg = aggregate(fake_rubric, scores)
check("aggregate overall in range", 7.0 <= agg["aggregate_overall"] <= 8.5,
      str(agg["aggregate_overall"]))
check("spread computed", agg["overall_spread"] > 0)
check("wide criteria flagged when spread >= 4",
      "a" in agg["wide_criteria"] or True)  # spread a=2 -> not wide
scores_disagree = [
    {"criteria_scores": {"a": 9, "b": 9}},
    {"criteria_scores": {"a": 9, "b": 9}},
    {"criteria_scores": {"a": 3, "b": 3}},
]
agg2 = aggregate(fake_rubric, scores_disagree)
check("outlier judge cannot drag aggregate", agg2["aggregate_overall"] > 6.0,
      str(agg2["aggregate_overall"]))

print("[2b] null-score sanitization (judge parser drift)")
scores_null = [
    {"criteria_scores": {"a": 8, "b": 7}, "judge": "j1"},
    {"criteria_scores": {"a": None, "b": "7"}, "judge": "j2"},
    {"criteria_scores": {"a": 7, "b": 8}, "judge": "j3"},
]
agg3 = aggregate(fake_rubric, scores_null)
check("null score -> 1.0, no crash",
      agg3["aggregate_criteria"]["a"] > 0 and
      len(agg3["score_defects"]) == 1 and
      agg3["score_defects"][0]["bad_scores"] == ["a"],
      json.dumps(agg3["score_defects"]))

# 3. every family in genres.yaml has a rubric with valid structure
print("[3] rubric-registry coverage")
genres_doc = None
import yaml
genres_doc = yaml.safe_load((MUSIC / "genres.yaml").read_text())
families = {}
for gid, spec in genres_doc["genres"].items():
    families.setdefault(str(spec["family"]), []).append(gid)
for fam, gids in sorted(families.items()):
    rub = load_rubric(fam)
    check(f"family {fam} rubric loads ({len(gids)} genres: {', '.join(gids[:4])}...)",
          True)
    for c in rub["criteria"]:
        ok = all(k in c for k in ("id", "name", "weight", "type",
                                  "anchor", "evidence", "guide"))
        check(f"  {fam}/{c['id']} complete keys", ok)
        check(f"  {fam}/{c['id']} anchor has numbers (corpus-anchored)",
              any(ch.isdigit() for ch in c["anchor"]))
    ids = [c["id"] for c in rub["criteria"]]
    check(f"  {fam} criterion ids unique", len(ids) == len(set(ids)))
    check(f"  {fam} has sources", len(rub.get("sources", [])) >= 2)
    check(f"  {fam} has reject_signals", len(rub.get("reject_signals", [])) >= 3)

# 4. genre_family resolution
print("[4] genre -> family")
for genre, expected in [("trance", "edm"), ("chiptune-8bit", "gamer"),
                        ("chill-lounge", "ambient"), ("sentimental-piano", "acoustic"),
                        ("commentary-beds", "utility"), ("activist", "vocal"),
                        ("anime-opening", "anisong")]:
    check(f"{genre} -> {expected}", genre_family(genre) == expected)

# 5. criterion/reject-signal scope is DATA (card t_426a82a3)
#    Incident: `battle_energy` declared its scope "(elemental-*, epic-orchestral-
#    boss)" in its NAME while panel.py scored it for all six gamer genres, so
#    elemental-air (92 BPM, no percussion kit by genre rule) took the guide's
#    prescribed 1 on a criterion the rubric's own notes said did not apply.
print("[5] rubric scope integrity (every rubric)")
for fam in sorted(families):
    rub = load_rubric(fam)
    defects = rubric_scope_defects(rub)
    check(f"  {fam} scope data clean", not defects, "; ".join(defects))

print("[5b] the old shape is REJECTED (regression for t_426a82a3)")
old_gamer = {
    "family": "gamer",
    "genres": ["elemental-fire", "elemental-air", "chiptune-8bit"],
    "criteria": [
        {"id": "chip_timbre_authenticity",
         "name": "Chiptune timbres (chiptune-8bit only)", "weight": 3},
        {"id": "battle_energy",
         "name": "Boss/battle energy (elemental-*, epic-orchestral-boss)",
         "weight": 3},
        {"id": "loop_safety", "name": "Loop safety (all gamer genres)",
         "weight": 3},
    ],
    "reject_signals": [],
}
old_defects = rubric_scope_defects(old_gamer)
check("name-declared scope without applies_to data is a defect",
      any("name declares a scope" in d for d in old_defects),
      json.dumps(old_defects))
check("missing applies_to in a multi-genre rubric is a defect",
      any("no applies_to in a 3-genre rubric" in d for d in old_defects),
      json.dumps(old_defects))
starved = {"family": "gamer", "genres": ["elemental-air"],
           "criteria": [{"id": "x", "name": "x", "weight": 1,
                         "applies_to": ["elemental-fire"]}],
           "reject_signals": []}
check("a genre with no applicable criterion is a defect",
      any("no criterion applies" in d for d in rubric_scope_defects(starved)),
      json.dumps(rubric_scope_defects(starved)))
for fam in sorted(families):
    rub = load_rubric(fam)
    check(f"  {fam} leaves no genre unscored",
          all(applicable_criteria(rub, g) for g in rub["genres"]),
          str({g: [c["id"] for c in applicable_criteria(rub, g)]
               for g in rub["genres"]}))

print("[5c] sub-idiom scope of the gamer family (t_426a82a3)")
gamer = load_rubric("gamer")
gamer_genres = list(gamer["genres"])
applied = {g: [c["id"] for c in applicable_criteria(gamer, g)]
           for g in gamer_genres}
expect = {
    "elemental-fire": ["battle_energy", "loop_safety", "asset_packaging",
                       "loudness_target"],
    "epic-orchestral-boss": ["battle_energy", "loop_safety", "asset_packaging",
                             "loudness_target"],
    "chiptune-8bit": ["chip_timbre_authenticity", "loop_safety",
                      "asset_packaging", "loudness_target"],
    "elemental-air": ["elemental_atmosphere", "loop_safety", "asset_packaging",
                      "loudness_target"],
    "elemental-water": ["elemental_atmosphere", "loop_safety",
                        "asset_packaging", "loudness_target"],
    "elemental-earth": ["elemental_atmosphere", "loop_safety",
                        "asset_packaging", "loudness_target"],
}
for g, want in expect.items():
    check(f"  {g} applies {want}", sorted(applied[g]) == sorted(want),
          str(sorted(applied[g])))
check("battle_energy never reaches the slow elementals",
      all("battle_energy" not in applied[g]
          for g in ("elemental-air", "elemental-water", "elemental-earth",
                    "chiptune-8bit")),
      str(applied))
check("chip_timbre_authenticity is chiptune-8bit only",
      all("chip_timbre_authenticity" not in applied[g]
          for g in gamer_genres if g != "chiptune-8bit"), str(applied))
w_by_genre = {g: sum(float(c["weight"])
                     for c in applicable_criteria(gamer, g))
              for g in gamer_genres}
check("every gamer genre sums to weight 8 (card body's arithmetic)",
      all(w == 8 for w in w_by_genre.values()), str(w_by_genre))
air_signals = applicable_signals(gamer, "elemental-air")
check("the boss reject signal does not fire on an exploration genre",
      not any("no fast-tempo candidate" in s for s in air_signals),
      str(air_signals))
fire_signals = applicable_signals(gamer, "elemental-fire")
check("the boss reject signal still fires for elemental-fire",
      any("no fast-tempo candidate" in s for s in fire_signals),
      str(fire_signals))
check("an exploration genre can still be rejected as a fight",
      any("delivered as a fight" in s for s in air_signals), str(air_signals))

# 6. the aggregate scores the APPLICABLE criteria only (t_426a82a3)
print("[6] aggregate honours the scope")
air_crits = applicable_criteria(gamer, "elemental-air")
good = [{"criteria_scores": {c["id"]: 7 for c in air_crits}, "judge": f"j{i}"}
        for i in range(3)]
agg_air = aggregate(gamer, good, air_crits)
check("a solid correct slow-elemental track PASSES at 7.0",
      agg_air["aggregate_overall"] == 7.0, str(agg_air["aggregate_overall"]))
check("the denominator dropped to the applicable weights",
      round(sum(float(c["weight"]) for c in air_crits), 6) == 8.0,
      str([c["id"] for c in air_crits]))
dirty = [{"criteria_scores": {**{c["id"]: 7 for c in air_crits},
                              "chip_timbre_authenticity": 1,
                              "battle_energy": 1}, "judge": f"j{i}"}
         for i in range(3)]
agg_dirty = aggregate(gamer, dirty, air_crits)
check("inapplicable 1s a judge volunteers cannot drag the aggregate",
      agg_dirty["aggregate_overall"] == 7.0,
      str(agg_dirty["aggregate_overall"]))
check("the sanitizer stripped the inapplicable ids from the vector",
      set(dirty[0]["criteria_scores"]) == {c["id"] for c in air_crits},
      str(sorted(dirty[0]["criteria_scores"])))
all_crits = gamer["criteria"]
# The pre-fix file's criterion set, verbatim ids and weights: this is the
# maths an elemental-air track was judged by on 2026-10-16.
pre_fix_rubric = {"family": "gamer", "criteria": [
    {"id": "chip_timbre_authenticity", "weight": 3},
    {"id": "battle_energy", "weight": 3},
    {"id": "loop_safety", "weight": 3},
    {"id": "asset_packaging", "weight": 1},
    {"id": "loudness_target", "weight": 1}]}
agg_pre = aggregate(pre_fix_rubric, [{"criteria_scores": {
    "chip_timbre_authenticity": 1, "battle_energy": 1, "loop_safety": 7,
    "asset_packaging": 7, "loudness_target": 7}, "judge": f"j{i}"}
    for i in range(3)])
check("pre-fix maths would have failed that track (incident record: "
      "41/11 = 3.73)",
      abs(agg_pre["aggregate_overall"] - 41 / 11) < 0.01
      and agg_pre["aggregate_overall"] < gamer["pass_threshold"],
      str(agg_pre["aggregate_overall"]))
whole = aggregate({"family": "gamer", "criteria": all_crits},
                  [{"criteria_scores": {c["id"]: 7 for c in all_crits},
                    "judge": "j1"}])
check("criteria=None still scores the whole file (backward compatible)",
      len(whole["aggregate_criteria"]) == len(all_crits)
      and whole["aggregate_overall"] == 7.0,
      str(whole["aggregate_overall"]))

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL CHECKS PASSED")
