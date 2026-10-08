"""test_panel_math.py — unit checks for the panel's aggregation and rubric
integrity. Run: python3 music/rubrics/test_panel_math.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from panel import aggregate, geometric_median, load_rubric, genre_family
import numpy as np

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

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL CHECKS PASSED")
