# Plan — How the NTSB Investigates a Plane Crash

## Narrative Arc

The video corrects a common misconception: the NTSB is not a crash investigation agency — it is a safety recommendation engine that uses crashes as input. The viewer goes from thinking "planes crash, NTSB writes reports" to understanding the full recommendation pipeline: crash → Go Team → Party System → investigation → public record → recommendations → adoption → safer next generation.

## Color Palette

- Background: `#1C1C1C` (Classic 3B1B)
- Primary: `#58C4DD` (blue — crash sites, NTSB, core elements)
- Secondary: `#83C167` (green — safety, adoption, positive outcomes)
- Accent: `#FFFF00` (yellow — emphasis, urgent, key numbers)
- Warning: `#FF6B6B` (red — litigation barred, crash icon)
- Neutral: `#888888` (axes, grids, supportive elements)

## Font

Mono: Menlo (all text mobjects)

## Scene Breakdown

| Scene | Script Section | Duration (TTS) | Visual Concept | Dominant Color |
|-------|---------------|----------------|----------------|----------------|
| Scene1_Hook | 0:00–0:08 | ~15s | Title card + crash site icon with radiating "Go Team" label | Primary (blue) |
| Scene2_Stakes | 0:08–0:45 | ~35s | Animated counters: 154,000 → 15,700 → 82%. Quote card with @wangtangkiki | Accent (yellow) for counters, Neutral for text |
| Scene3_GoTeam | 0:45–2:30 | ~105s | Radial diagram: Go Team icon at center, spokes to specialist roles. Site documentation animation | Primary (blue) |
| Scene4_PartySystem | 2:30–4:15 | ~105s | Central NTSB node, surrounding party nodes with arrows. Red X over litigation icon. Fact card for FAA automatic party | Secondary (green) for parties, Warning (red) for barred |
| Scene5_Timeline | 4:15–5:45 | ~90s | Timeline graphic with Class 1–4. Two concrete timeline strips (Alaska 1282, DCA collision) | Neutral (gray) for timeline, Accent for dates |
| Scene6_PublicRecord | 5:45–7:00 | ~75s | NTSB Aviation Investigation Search mockup with searchable fields | Primary (blue) |
| Scene7_InvisibleSystem | 7:00–8:30 | ~90s | One red dot among green dots. Flow diagram: Investigation → Findings → Recommendations → Adoption. Line chart: GA fatal rate decline | Secondary (green) for data, Warning (red) for the crash |
| Scene8_PayoffCTA | 8:30–9:30 | ~45s | Zoom-out from crash site to full safety cycle. End screen with subscribe button | Primary (blue) → Secondary (green) gradient |

## Animation Notes

- Each scene sets `self.camera.background_color = "#1C1C1C"`
- All scenes use `Menlo` font for Text mobjects
- Add subtitles via `self.add_subcaption()` or `subcaption=` on `self.play()`
- Every scene ends with `self.play(FadeOut(Group(*self.mobjects)))` for clean exit
- Vary entry animations: Scene1 Write, Scene2 FadeIn, Scene3 Create, etc.
- Add `self.wait()` after key reveals (2s for "aha moments", 1s for supporting, 0.5s for cleanup)
- Numbers animate with `AnimatedCounter` or `Transform` from 0 to target
