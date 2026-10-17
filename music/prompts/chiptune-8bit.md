# chiptune-8bit — prompt template

> Registry: family `gamer`, lanes: game-assets, youtube-gaming, streaming.
> NES/Game Boy-era sound. The genre is defined by hardware constraint: pulse waves,
> triangle bass, noise percussion, fast arpeggios, NO reverb. Loop-10min shape.

## Style field (paste into Suno "Styles", 567/1000 chars)

```text
authentic NES-style chiptune, 150 BPM, two pulse-wave channels trading lead melody and fast arpeggio, triangle-wave bass, noise-channel percussion, one-frame-speed arpeggios cycling chord tones for implied harmony, call-and-response between the two pulse leads, 25 percent and 50 percent duty-cycle contrast between channels, vibrato on held lead notes, simple key-triggered echo instead of reverb, bright energetic 4/4, melody-driven like 1980s action-game music, no chords stacked more than one note deep per channel, crunchy low-bitrate texture, seamless game loop
```

## Lyrics guidance

Instrumental. Leave the **lyrics box empty** — that is Suno's instrumental path.
(Vocal chiptune exists but kills the
game-asset lane utility.)
The tag sheet below is OPTIONAL structure control: section tags and parenthetical
direction, never singable words.

```text
[Intro]
(pulse 1 states the theme over triangle bass, noise hats)

[Instrumental]
(pulse 2 answers in the gaps — call and response)

[Instrumental]
(harmony phase: pulse 1 lead, pulse 2 fast arp implying
the chords underneath)

[Instrumental Break]
(drop to one pulse and triangle — space does the work)

[Instrumental]
(both pulses drive, noise percussion doubles, highest
energy)

[Outro]
(theme clipped to a single punchy phrase — LOOP POINT)
```

Rules:
- Four voices, four jobs: lead, harmony/arp, bass, percussion. Nothing else. The
  moment a fifth sustained layer appears, the illusion dies.
- Vibrato and pitch-bend on held notes = the "performed" feel of chip leads.
- Loop-safe: end on a punchy clipped phrase that leads back to bar 1.

## More Options

- **Weirdness:** 35%. The genre's charm is discipline inside constraint — chaos
  breaks the "single-chip" illusion.
- **Style Influence:** 85%. "Pulse + triangle + noise + fast arps" must hold or it
  becomes generic synth.
- **Exclude Styles:** ` reverb, lush pads, realistic instruments, drums with long tails, modern synths, detuned supersaws`
- The "reverb" exclusion is load-bearing: the 2A03 had none. A hall tail on a chip
  lead instantly reads as "synth pretending."

## Craft notes — what makes it read as chiptune (not generic synth)

1. **The sound is the chip, not a style.** NES Ricoh 2A03: exactly five voices — two
   pulse, one triangle, one noise, one DPCM. Game Boy: two pulse, one wave, one
   noise. Chiptune is defined by TIMBRE under constraint, not by "retro" mood.
2. **The fast arpeggio is the genre's single most recognisable move.** One voice
   cycles chord tones at frame rate (~60 Hz swaps — a note every 1/16 to 1/64) so
   the ear fuses them into implied harmony. This fakes chords from monophony;
   Martin Galway brought it into game music. A "chord" that actually rings as a
   stack is a mistake — the real chip could not do it.
3. **Duty cycle is the timbre control.** Pulse channels have 12.5% (thin/nasal),
   25% (reedy — the classic lead), 50% (hollow square) — three distinct voices.
   Contrast them between channels.
4. **Triangle = bass, noise = drums.** The standard division of labor. A modern sub
   bass or 909 kit under chip leads reads instantly wrong.
5. **Volume steps, not fades.** 16-step envelopes (4-bit volume) make the plucked
   staccato attacks; a smooth fade is not a thing the hardware did.
6. **Echo, not reverb.** The period-correct space is a single quiet re-triggered
   note as slap echo. Anything wetter breaks the chip illusion.
7. **Musical DNA: melody-first** with frantic arps and counterpoint — drawn from
   80s progressive rock/jazz fusion game scores. The tune must survive being
   whistled.

A generation with smooth analog pads, reverb tails, realistic instruments, or
>2-note-per-channel chords is OUT of genre — reject it.
