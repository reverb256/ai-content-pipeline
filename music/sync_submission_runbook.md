# RUNBOOK: Sync & Direct-Licensing Submission (HUMAN-GATED)
# Target Platforms: Songtradr, AudioSparx, Own Site

## 1. Songtradr Submission (API-First)
The pipeline uses `music/lanes/sync.py` to prepare the package.
The API submission is handled by the distributor bot.

**Human Action Required:**
1. Log into Songtradr dashboard to verify the "AI-Generated" tag is correctly applied.
2. Review the "Clearance" section to ensure the one-stop clearance doc is attached.
3. If API fails, manually upload `full_mix.wav` and `instrumental.wav` from the package folder.

## 2. AudioSparx Submission (Manual/Hybrid)
1. Navigate to Contributor Portal.
2. Upload the `full_mix.wav`.
3. In the metadata field, paste the contents of `manifest.json` (Mood, Tempo, Key).
4. Check the box: "I own all rights / AI-Generated (Commercial License)".

## 3. Direct-Licensing Storefront (Own Site)
1. Create a new product entry for the track.
2. Set pricing per `music/lanes/direct-license.py`:
   - Personal: $25
   - Commercial: $150
   - Exclusive: $500+
3. Map the digital delivery files:
   - Personal Tier -> `full_mix.wav`
   - Commercial Tier -> `full_mix.wav`, `instrumental.wav`
   - Exclusive Tier -> `all_stems.zip` (from the stems folder)

## 4. Verification Checklist
- [ ] Full Mix present?
- [ ] Instrumental present?
- [ ] Stems present (12 files)?
- [ ] AI-Disclosure signed and attached?
- [ ] Metadata (BPM, Key) matches audio analysis?
