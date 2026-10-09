# anime-opening — prompt template

> Registry: family `anisong`, lanes: streaming, sync, direct-license, youtube-gaming.
> Source idiom: anison — anime music with its own production conventions,
> fan economy, and chart system (campaigns/virtual-reflections/CAMPAIGN.md).
> Required by the Virtual Reflections album: tracks 7–8 ("Opening Theme",
> "Becoming") — the explosive end of the intimate→explosive arc.
> Video shape: single-4min (this is a SHOWPIECE, like epic-orchestral-boss,
> not a loop — a TV opening is 90 seconds of maximum density).

## Style field (paste into Suno "Styles", 752/1000 chars)

```text
japanese anime opening (anison), 160 BPM, J-rock with orchestral and synth layers, busy driving drums with double-kick fills, melodic bass that moves in eighth-note runs, piano AND strings together over dense rhythm guitars, bright brass stabs, IV-V-iii-vi "royal road" progression (the anime progression), explosive verse into a soaring singable chorus, Japanese-language vocals with idol-rock energy, maximum information density for a 90-second TV edit, no wasted bars, layered synth pads under the orchestra, dramatic risers between sections, triumphant and urgent at once, FINAL CHORUS JUMPS UP ONE KEY — the defining anison gesture, big key-change lift with full band and strings doubled an octave higher, hard-hitting ending on a final unison hit
```

## Lyrics guidance

Vocals are Japanese — write lyrics in **Japanese script** for correct
pronunciation. Suno mispronounces romanized Japanese. Give the writer the
royal-road structure and the key-change moment as [metatags]:

```text
[Intro]
(Japanese: 2-4 lines. High energy from bar one.
A hook fragment — the chorus melody in embryo,
stated over drums and bass only. No buildup waste:
an opening must hook inside 15 seconds)

[Verse 1]
(Japanese: 4-8 lines. Dense, story-forward lyrics,
melodic bass eighth-notes under piano + strings.
The verse carries the scene-set: who is running,
toward what. Information per bar is the genre standard)

[Pre-Chorus]
(Japanese: 2-4 lines. Tension climb — short lines,
rising pitch, drums open up, riser into the chorus)

[Chorus]
(Japanese: 4-8 lines. The soaring singable hook.
Title phrase repeated. IV-V-iii-vi carries it.
Full band + strings + brass stabs together)

[Verse 2]
(Japanese: 4-8 lines. Same density, new imagery,
bass runs busier, one guitar counter-line)

[Pre-Chorus]
(Japanese: repeat, bigger)

[Chorus]
(Japanese: repeat, bigger)

[Bridge]
(Japanese: 2-4 lines. Strip to piano + strings + voice,
half-time feel for two bars — the breath before
the final chorus. This silence is load-bearing)

[Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE]
(Japanese: the same chorus words, now in the higher key.
Vocals reach for the top of the range, strings doubled
an octave higher, full band at maximum. THE SIGNATURE
MOVE — omit it and the track reads as generic rock)

[Outro]
(Japanese: 1-2 lines or a shouted title phrase,
then a hard unison final hit. No fade-out.
The ending must cut like a TV edit to black)
```

Rules:
- **Final chorus jumps up a key.** This is the single most important line in
  this template. It is the genre's defining gesture — a listener who knows
  anison hears the key change and stops hesitating. State it in the style
  field AND give it a dedicated [metatag] section.
- Japanese script only. Kana/kanji, not romaji, in the lyrics box.
- 90-second TV edit discipline: every section earns its bars. The intro is
  15 seconds of hook, not a long ambient build. The bridge is the only
  permitted breath.
- IV–V–iii–vi (the "royal road", 王道進行) under the chorus. Opens on the
  subdominant, lands on the minor vi — that bittersweet-triumphant color is
  the "anime progression" a 2023 Music Theory Spectrum study found across a
  large share of Japan's best-selling songs for decades.

## More Options

- **Weirdness:** 35%. Anison form is load-bearing (15s hook, pre-chorus
  climb, bridge breath, key-changed final chorus). Chaos dissolves the
  edit-survival structure.
- **Style Influence:** 85%. "160 BPM + royal road + key-change final chorus
  + Japanese vocals" must survive intact or the generation is not anison.
- **Exclude Styles:** ` acoustic folk, lo-fi, trap beats, EDM drop, rap verse, ballad, English lyrics`
- Do not exclude "rock" or "orchestral" — they ARE this idiom. Keep the
  exclusion list to terms that pull toward other genres.

## Craft notes — what makes it read as anison (not generic epic rock)

Cite-check against real anison convention before changing this template:

1. **THE KEY CHANGE IS THE GENRE.** The final chorus jumping up a key
   (usually one semitone or a whole tone) is the defining gesture of the
   anison form — the triumphant lift at 1:30 in a real TV opening. A track
   without it is a rock song with anime stickers. This is the single most
   important discriminator in the template.
2. **The royal road (王道進行, IV–V–iii–vi).** Nicknamed "the anime
   progression": it opens on the subdominant and lands on the minor vi, so
   even triumphant passages carry the bittersweet undertone the genre runs
   on. A 2023 *Music Theory Spectrum* study documented it across a large
   share of Japan's best-selling songs over decades. Put it under the
   chorus, not the verse.
3. **Tempo 130–180 BPM; J-rock pocket 160–170.** Below 130 drifts to
   pop-rock, above 180 to speed-metal. The busy double-kick drum pattern
   and melodic eighth-note bass are the engine — "busy drums, melodic bass,
   piano AND strings together" is the layer contract.
4. **Dense orchestral + synth, not one or the other.** Strings and piano
   over rhythm guitars with synth pads underneath is the modern anison
   (post-2010s) wall of sound. Brass stabs on the chorus hooks.
5. **90-second TV edit discipline.** Real openings front-load the hook in
   15 seconds and waste no bars. The full song may run 3–4 minutes, but
   it must survive being cut to 90 seconds with the arc intact: hook →
   verse → pre-chorus → chorus → bridge → final chorus.
6. **Japanese vocals in Japanese script.** Suno's pronunciation model reads
   kana/kanji correctly and mangles romanization. The writer supplies
   Japanese lyrics (human-authored — see the lyrics gate).
7. **Hard ending, never a fade.** The final unison hit cuts like the TV
   cut-to-black. Fade-outs are a defect in this genre.

A generation without a key-changed final chorus, or with English lyrics, or
a long ambient intro is OUT of genre — reject it.
