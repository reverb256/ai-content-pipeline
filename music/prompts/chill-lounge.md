# chill-lounge — prompt template

> Registry: family `ambient`, lanes: youtube-longform, streaming, sync, direct-license.
> Primary lane: 30–60 min YouTube album videos. Watch time is the product.

## Style field (paste into Suno "Styles", 545/1000 chars)

```text
downtempo chill lounge, 75 BPM, 4/4, heavy swung hats, warm jazz chords on felt electric piano, maj7 min7 dom9 voicings, soft round bassline following chord roots, tape saturation and gentle wow-and-flutter pitch drift, vinyl crackle bed at the noise floor, slow low-pass filter movement across the loop, light sidechain pump on the chords, unhurried 8-bar loop that barely develops, kick and snare sitting behind the chords, muted guitar answering phrases, airy reverb, no bright modern top end, warm not loud, late-night room with rain outside
```

## Lyrics guidance

This lane is almost always instrumental. Leave the **lyrics box empty** — that is
Suno's instrumental path (the editor placeholder says "leave this empty for
instrumental"). Do not paste production notes as sung lyrics.
If a spoken/ambience layer is wanted, keep it to texture words only.
The tag sheet below is OPTIONAL structure control: it carries section tags and
parenthetical direction, never singable words.

```text
[Intro]
(rain and vinyl crackle, chords fade in)

[Instrumental]
(chord loop states twice, hats enter, bass enters)

[Instrumental Break]
(melody drops out, filtered chords and noise bed only)

[Instrumental]
(full loop returns, one new counter-line)

[Outro]
(elements subtract one by one, rain and crackle remain, slow fade to silence)
```

Rules:
- Mark every section with a metatag. Suno reads them as arrangement instructions.
- Never put production notes inside `[Verse]` sections as prose — the singer will sing them.
- For the album-video lane, generate one track per loop idea; the 30–60 min video is a
  compilation, not one long piece.

## More Options

- **Weirdness:** 40%. Low weirdness keeps the loop stable and loopable; chaos breaks the meditative spell this lane sells.
- **Style Influence:** 70%. Strong enough that "tape + swung hats + maj7" survive; leave room for fresh chord colors.
- **Exclude Styles:** ` EDM, big drops, autotuned pop vocals, trap hats, bright synth leads, loud drums`
- Keep the exclusion list short — six terms max. Exclusions steer; they do not forbid.

## Craft notes — what makes it read as chill-lounge

Cite-check against real production convention before changing this template:

1. **Tempo 70–90 BPM, sweet spot 75–85.** Above 90 it drifts to boom-bap; the lane's
   meditative feel lives in the mid-70s.
2. **Jazz harmony, not pop triads.** maj7/min7/dom9 with close voicings and gentle
   velocity (Dm7–G7–Cmaj7 is the canonical ii–V–I loop). Voice-lead: shared notes move
   least.
3. **Swing on the hats, straight backbone.** Nudge select 16th hats 12–18 ms late; keep
   kick/snare on the grid. Full-grid or full-loose both kill the pocket.
4. **Degradation is the sound.** Bit/sample-rate reduction, tape flutter 10–20%, a
   crackle bed at −18 to −22 dBFS. Subtle alone, together = "memory." Top end rolled
   off around 8–12 kHz, not deleted.
5. **The loop is the point.** 4–8 bars, minimal development, small per-pass variation
   (filter, crackle shift, one melody note). Arrangement is texture, not a song arc.
6. **YouTube lane survival:** visual identity + disclosure are what keep the
   inauthentic-content policy off this lane. The prompt only fixes the audio half.

A generation that has a vocal hook, a build-drop, or a bright modern top end is
OUT of genre — reject it.
