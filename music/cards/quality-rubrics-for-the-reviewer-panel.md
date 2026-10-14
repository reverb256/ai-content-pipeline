The reviewer panel (reviewer-deepseek / reviewer-longcat / reviewer-minimax /
reviewer-nemotron) needs MUSIC rubrics. Research basis: knowledge-grounded rubrics
beat generic ones (Evaluation-Illusion); small diverse judges beat one big judge
(PoLL); geometric-median aggregation is robust to a contaminated judge (RoPoLL).

Deliverables:
1. `music/rubrics/<genre-family>.json` — per family (ambient, edm, acoustic,
   utility, vocal, gamer). Criteria must be CORPUS-ANCHORED: cite real production
   conventions and numbers, not "is it good".
2. Genre-authenticity criteria: e.g. trance = 128-140 BPM, 32-bar structure,
   breakdown/build; jungle = 160-175 BPM, amen breaks, ragga vocal; chiptune =
   authentic chip timbres not "chiptune-ish synth".
3. Aggregation: geometric median across the panel; disagreement -> human triage.
4. `gate_quality.py` integration (owned by the gate card — coordinate).
5. Rulings: any j_kro music-quality correction goes into brain/RULINGS.md under a
   new "Music" section (the file is currently EMPTY — that is a health red flag).

Acceptance: panel scores one real track across 3+ distinct model families with
the aggregation shown, and one deliberately bad track scoring lower.


## Context (read before starting)

Repo: /home/j_kro/Projects/ai-content-pipeline
Architecture: brain/playbooks/music-lane-architecture.md  ← READ THIS FIRST
Platform research: brain/research/music-monetization-2026.md

## Hard constraints
- Suno Premier: 60 STANDARD downloads/month. Suno STUDIO downloads are UNLIMITED.
  Every export path must go through Studio. Never the standard download button.
- Suno has NO official API. Generation = CDP browser automation on the logged-in
  Premier session (see the suno-studio pattern). No paid reseller proxies.
- The pipeline is GENRE-GENERIC. Genres are DATA (music/genres.yaml), never code.
  Adding a genre must require zero script edits.
- Banned platforms — do NOT build for these: Pond5, AudioJungle/Envato, Artlist,
  Epidemic Sound, Soundstripe, PremiumBeat, Musicbed, Bandcamp (Jan 2026),
  Beatport (Aug 2026), CD Baby.
- Gates must EXECUTE the artifact (parse/measure/render). A gate that greps a file
  for a feature name is a defect — it passes while the artifact is broken.
- No stubs. No TODOs. Complete code, verified by real execution.

## Report back
Evidence in the report: exact commands run, real output, file paths.
A claim without tool output is not done.
