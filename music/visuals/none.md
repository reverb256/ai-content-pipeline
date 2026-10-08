# visual: none (commentary-beds)

> Pairs with: `prompts/commentary-beds.md`. Video shape: none. Lane: direct-license,
> sync — audio-only product. THIS FILE EXISTS TO SAY "NO VISUAL".

## Rule

Commentary beds ship as audio + stems + licence, not as videos. Do not render a
visual for this genre. There is no YouTube lane, no thumbnail, no video task.

## Why the file exists

`genres.yaml` requires a `visual_style:` path per entry. Resolving this path must
read "no visual," not crash or fall through to a default. Bots reading this:
stop here. The deliverable is the audio kit.

## Package cover art

The ONLY visual artifact in this lane: flat 3000x3000 cover PNG for the kit —
podcast name, motif rendered as a simple mark, palette from the show's flavor
(warm lo-fi jazz = amber/teal; tech news = blue/white; true crime = red/black).
Cover art is metadata, not content. Do not build a video pipeline for it.
