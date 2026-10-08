# visual: pixel-scene (chiptune-8bit)

> Pairs with: `prompts/chiptune-8bit.md`. Video shape: loop-10min.

## Palette & scene

- True NES palette (the ~54-color NES set, not modern HD palettes): sky blue
  #3cbcfc, brick #b53120, ground green #005800, sprite white #fcfcfc.
- Scene: side-scrolling level diorama (castle approach / cavern dash / sky
  bridge) with parallax at exactly 2 or 3 planes.

## Motion grammar

- Side-scroll parallax at constant velocity, tile-locked (8 or 16 px tiles).
  Background plane 0.5x, foreground 2x scroll speed.
- Sprite animation 2–4 frames per action, 8 fps, NO subpixel interpolation ever.
  The 8-bit constraint is the aesthetic; do not soften it.

## Texture

- Zero anti-aliasing. Zero gradients. Hard pixel edges only, integer scaling
  (e.g. 1080p = 240p x4.5 → use 1440p = 240p x6 for exact integers).
- Optional light CRT arc + scanlines overlay ≤ 15% — OFF for the "clean" variant.

## Loop & variation (gate_youtube_authentic)

- Rotate level themes (castle/cavern/sky/ice) per upload. Sprites and tilesets
  change; palette rules stay.

## Audio-visual sync

- Pulse-lead melody = the hero sprite's action cycle. Noise-channel hats = star
  sparkle tiles blinking. Breakdown = scroll pauses on a "checkpoint" screen
  while the music thins.
