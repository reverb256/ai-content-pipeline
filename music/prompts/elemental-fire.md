# elemental-fire — prompt template

> Registry: family `gamer`, lanes: game-assets, youtube-gaming, streaming.
> Boss/battle theme for the fire element. Target: indie devs + gaming music channels.
> Video shape: loop-10min — the track must survive repetition and loop seamlessly.

## Style field (paste into Suno "Styles", 583/1000 chars)

```text
fire elemental boss battle theme, 150 BPM, driving taiko and frame-drum percussion with galloping triplets, aggressive staccato string ostinato in the low register, low brass swells and braams answering the strings, cracking rhythmic fire-crackle texture layer, shredding modal melody on horns or erhu, minor key with flat-2 Phrygian color, phrased as a fight: tension intro, burning theme, molten peak, brief smoldering breakdown, full blaze reprise, loop-safe ending that resolves back to the opening tension, seamless game loop, high energy throughout, cinematic hybrid orchestral
```

## Lyrics guidance

Instrumental. Leave the **lyrics box empty** — that is Suno's instrumental path.
(Battle themes with sung lyrics have narrow
sync utility; a wordless low choir "ahh" is acceptable as texture if it appears.)
The tag sheet below is OPTIONAL structure control: section tags and parenthetical
direction, never singable words.

```text
[Intro]
(tension bed: low strings tremolo, fire crackle, single taiko pulse)

[Instrumental]
(burning theme stated on horns over the full percussion kit)

[Instrumental]
(theme develops, strings ostinato doubles, brass answers)

[Break]
(the molten peak: melody up an octave, all layers in)

[Instrumental Break]
(smoldering breakdown: percussion thins, strings sustain,
fire-crackle and low drone — tension rebuilds)

[Instrumental]
(full blaze reprise: theme returns at maximum intensity)

[Outro]
(energy resolves back to the intro tension bed — LOOP POINT:
the last bar must lead seamlessly into the first)
```

Rules:
- This is loop-shaped music for `loop-10min` videos and game integration. The outro
  must resolve INTO the intro, not into silence.
- Mark the intended loop point in the metatag structure; downstream `gate_loop_points`
  will verify the seam.
- Multi-phase feel (escalating layers) mirrors boss-fight phases — new instrument
  layers mark each escalation.

## More Options

- **Weirdness:** 40%. Battle music tolerates aggression and surprise; keep it under
  the level where the theme itself dissolves.
- **Style Influence:** 80%. "Percussion-forward + ostinato + Phrygian" must hold.
- **Exclude Styles:** ` pop vocals, EDM drop, trap, happy major key, ambient drone, lo-fi`
- The "happy major key" exclusion matters: fire reads as danger and drive, not
  picnic.

## Craft notes — what makes it read as a FIRE battle theme

1. **Percussion is the protagonist.** Boss/battle convention: taiko, orchestral bass
   drum, toms at 130–200 BPM (this template: 150). Galloping and triplet figures
   create the "act now" urgency the fight demands.
2. **Low-register string ostinato = the engine.** The genre's "nervous system": fast
   repeated figures in cellos/basses that drive under everything and cut through
   the percussion weight.
3. **Phrygian flat-2 is fire's scale color.** The semitone-above-root has been
   "danger/exotic/flame" since the classical era; it is the modal signature that
   separates a fire theme from generic epic minor.
4. **Braams and brass swells** are the hybrid-trailer vocabulary for scale and threat;
   keep them as ANSWWERS to the string ostinato, not constant wallpaper.
5. **Texture layer:** literal fire-crackle rhythm gives elemental identity beyond
   generic battle. Percussive noise-as-instrument is a McCreary-grade move
   (gamelan/percussion-as-terror in SOCOM 4).
6. **Loop discipline is a lane requirement.** game-assets requires stems, loop_point,
  seamless_loop. A track that only works once is unusable in-engine.

A generation that is slow ambient, major-key heroic, or built on a sung pop chorus
is OUT of genre — reject it.
