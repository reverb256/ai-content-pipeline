# commentary-beds — prompt template

> Registry: family `utility`, lanes: direct-license, sync. No visual lane.
> Market: 82% of podcasts license stock themes. The product is a KIT: intro sting,
> loopable bed, stings, outro — all from one motif. Beds must be loopable + stemmed.

## Style field — INTRO STING (420/1000 chars)

```text
short podcast intro theme, 120 BPM, instrumental, warm lo-fi jazz palette, one memorable 4-6 note bell-pluck motif stated twice over electric piano chords, punchy but soft kick and rimshot, quick 8-bar build, tight modern podcast production, mono-compatible mix for phone speakers, ends with a clean decisive hit then one beat of silence, no fade-out, no long reverb tails, bright enough to read on earbuds at low volume
```

## Style field — LOOPABLE TALK BED (422/1000 chars)

```text
minimal instrumental podcast talk bed, 120 BPM, same warm lo-fi jazz palette, muted chords and soft bass on the loop's chord roots, NO melody, no lead instrument, sparse rimshot ticks on the 2 and 4, extremely repetitive on purpose, low dynamic range, seamless loop-friendly phrasing, sits quietly under a speaking voice, no drum fills, no builds, no surprises, midrange leaves the vocal frequencies clear, mono-compatible
```

**Two separate generations — never one.** The sting and the bed are opposite briefs
sharing one palette. A generation asked for both grows melodies into the bed.

## Lyrics guidance

No lyrics ever. Leave the **lyrics box empty** for both generations — an empty
lyrics box is Suno's instrumental path.
Structure via metatags only (the sheet below is optional structure control:
section tags and parenthetical direction, never singable words):

```text
[Intro]
(the motif, alone)

[Instrumental]
(full soft arrangement, motif repeats once)

[Outro]
(the motif clipped short, one hit, hard stop, one beat of silence)
```

For the bed:

```text
[Instrumental]
(chords + bass + ticks, 16 bars, ends on the chord that leads back to bar 1)

[Instrumental]
(identical pass — the point is sameness)
```

## More Options

- **Weirdness:** 25% (sting) / 20% (bed). Utility music must be boring-adjacent. A
  bed that surprises fights the host's voice for attention.
- **Style Influence:** 85% (sting) / 90% (bed). The kit's identity comes from the
  prompt; deviations break brand consistency across episodes.
- **Exclude Styles (bed):** ` lead melody, vocal samples, fills, drum solos, builds, EDM drops, big dynamics`
- **Exclude Styles (sting):** ` long reverb tails, fade-outs, vocals, EDM`
- The sting ends HARD — silence is the edit point where the host's voice comes in.

## Craft notes — what makes a commentary bed read as professional

1. **The motif is the show's audio brand.** 4–6 notes, stated twice — one statement
   isn't memorable, three is annoying. Everything in the kit derives from it: the bed
   keeps its chords, the outro plays its answering phrase.
2. **Bed = anti-melody.** The ear follows a tune over a voice; the bed must never
   have one. Every musical event in a bed fights the speaker for attention. "No
   fills, no builds, no surprises" is the job description.
3. **Mono compatibility is non-negotiable.** A large share of podcast listening is a
   single phone speaker; wide-stereo stings collapse into phase soup there.
4. **Timing at 120 BPM:** every bar = exactly 2 seconds. An 8-bar intro runs 16 s,
   a 16-bar bed 32 s. Editors cut on those marks — keep the math clean.
5. **Intro under 20 seconds.** Past that listeners skip and the signature goes
   unheard.
6. **Loop-safety:** end the bed's last bar on the chord that leads back to bar 1;
   verify the loop point downstream with `gate_loop_points` (crossfade-verified
   seamlessness), because game/podcast lanes require proven loops.
7. **Deliverables for the lane:** stems (mandatory), 15/30/60 s cutdowns of the sting,
  loopable bed WAV, all in one kit folder per client genre flavor. Flavor by show
  type: "warm lo-fi jazz" (interview), "bright indie electronic" (tech news),
  "tense pulsing minimal" (true crime).

A bed with a melody, a build, or a fade-out is OUT of spec — reject it.
