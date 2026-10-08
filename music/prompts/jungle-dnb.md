# jungle-dnb — prompt template

> Registry: family `edm`, lanes: streaming, youtube-mix, direct-license.
> Same Beatport ban as trance. Amen-break / ragga vocal direction is the genre's spine.

## Style field (paste into Suno "Styles", 653/1000 chars)

```text
ragga jungle, 168 BPM, chopped and resequenced Amen break with ghost notes and pitch-shifted snare edits, tight punchy kick and snare layered under the break, deep rolling sine sub-bass in the 40-60 Hz region following a slow reggae bassline at half the drum tempo, long sliding bass notes with space where the drums are busiest, ragga toasting vocal hook chopped to the fast grid, dub delays, spring reverb splashes, airhorns and siren FX, 12-bit sampler crunch and vinyl crackle texture, soundsystem pressure, UK 1994 pirate radio energy, rough and raw not clinical, call-and-response vocal chops, forward-rolling breakbeat that rarely repeats exactly
```

## Lyrics guidance

Ragga vocals: short, chantable, dancehall phrasing. The voice sits on the SLOW grid
(half tempo, ~84 BPM feel) against the bass, never chopped to the fast drum grid.

```text
[Intro]
(dub siren, airhorn, vocal chant: "rewind, come again")

[Break]
(break states once, sub-bass slides in underneath)

[Hook]
(ragga toast, 2-4 short lines, crowd-addressing: "all massive inside!")

[Break]
(break re-chops, ghost snares, bass answers the kick)

[Hook]
(call-and-response: lead vocal line, then a chopped vocal answer)

[Break]
(filtered break and bass for tension, then full pressure returns)

[Outro]
(break subtracts, dub delay trails, siren fades)
```

Rules:
- Short chants, not verses. Call-and-response and crowd address ("massive!", "rewind!")
  carry the soundsystem vibe.
- Time-stretched/chopped vocal chops are stylistically authentic — keep intelligibility
  during the drops.
- If Suno cannot deliver a convincing ragga toast, generate the instrumental and treat
  the vocal hook as a stem-layer edit downstream.

## More Options

- **Weirdness:** 55%. Jungle's breaks are chaotic by convention — slightly-above-normal
  weirdness helps the re-chop variation. If output gets sloppy, drop to 45%.
- **Style Influence:** 80%. "Amen + 168 + ragga + sub-bass at half tempo" must survive.
  This genre drifts to generic DnB fast.
- **Exclude Styles:** ` liquid DnB rollers, pop EDM, half-time dubstep, autotune R&B, stadium house`
- Watch for drift to clinical modern DnB: if the break sounds like a one-shot sample
  pack instead of a chopped break, regenerate.

## Craft notes — what makes it read as jungle (not DnB, not breakcore)

1. **168 BPM drums, ~84 BPM bass — the two-speed relationship is the genre.** Drums
   160–175 (sweet 165–170); the bassline is written at half that, reggae/dancehall
   territory. A bassline that fights the break at 170 kills the jungle feel instantly.
2. **Chopped breaks, not loops.** Amen (The Winstons "Amen, Brother"), Think (Lyn
   Collins), Apache (Incredible Bongo Band), Hot Pants (James Brown). Slice into
   1/8–1/32 fragments, ghost notes, pitch variances, reverse hits, edits every few
   bars. A flat looped break reads as lazy DnB.
3. **12-bit sampler crunch is authentic.** Akai S950/SP-1200 heritage: bitcrush the
   breaks, add vinyl crackle, let time-stretch artifacts live in the sound. Clean
   24-bit breaks are wrong for this genre.
4. **Sub-bass: sine/triangle, 40–60 Hz, mono.** Long sliding notes drawn from reggae —
   answering the kick, not doubling it. E-to-G region for soundsystem weight.
5. **Ragga vocal = the toasting, on the slow grid.** Phrases against the bass. Dub
   techniques: delays, tape echo, spring reverb, airhorns, sirens, rewinds.
6. **Jungle vs DnB:** jungle came first — grittier, sample-based, ragga-fused. DnB is
   the cleaner, more clinical descendant. If a generation sounds polished and
   synth-bassed, it has crossed into DnB — reject it.

A generation with a reese-bass-led clinical groove, a straight 4/4, or no chopped
break energy is OUT of genre — reject it.
