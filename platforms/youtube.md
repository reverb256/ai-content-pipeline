# YouTube Platform Playbook

> YouTube is the authority + visual surface. Long-form documentaries and
> deep-dives from the build logs, with Shorts for discovery.

## Platform Rules

- 2-4 long-form/week max (diminishing returns beyond that)
- Shorts as often as quality allows (~5/month pulls long-form up 46%)
- First 30 seconds decide retention; hook in first 2 seconds for Shorts
- Title + thumbnail earn the click; retention keeps it
- One niche, tight cluster — no wandering topics
- Playlists stretch sessions (autoplay chains)
- Cards/end-screens are retention nudges, not growth engines
- Enable auto-dubbing (global reach by default)

## Content Types That Compound

1. System design posts ("how we architected X, the tradeoffs, what we'd
   change")
2. Performance deep-dives ("cut p95 from 800ms to 120ms — what was actually
   slow")
3. Bug post-mortems ("the incident report")
4. Tool/library selection essays ("picked A over B, 6 months later: would we
   again")
5. Migration documentary (the Omarchy story, multi-episode)

## Production Reality (faceless, AI-assisted)

- Script from the flagship piece (writer → video script)
- Voiceover: TTS (ElevenLabs-class) or our own recording
- Visuals: screen captures of real builds, system diagrams, Mermaid graphs
- Thumbnails: consistent brand, curiosity + specificity
- Editing: cut dead air, vary shots, captions on

## Interaction Mode

YouTube interacts via the CDP browser (real reverb256 session) — Studio
uploads, analytics reads. API endpoints captured when we start uploading.

### MCP Integration (2026-08-29)

| Server | Status | What it gives |
|--------|--------|---------------|
| `social-video` (social-video-mcp) | ✅ wired in `/data/agents/mcp-bridges/social-video-mcp.sh` | Sub feed, watch history, liked, watch later, channel uploads, Shorts — via browser cookies (yt-dlp `--cookies-from-browser`), NO OAuth. Needs Hermes restart to load. |
| `youtube-mcp-server` (pauling-ai, 40 tools) | ⏳ deferred — needs Google Cloud OAuth | Full Data/Analytics/Reporting API: channel analytics, video upload, comments, SEO, transcripts. Setup requires a Google Cloud project + OAuth consent (one-time, ~20 min in console). Do when we start publishing. |

**Watch history note:** the YouTube Data API no longer exposes watch history.
The only API path is Google Takeout (export history JSON once, import via
`romanstrazanec/youtube-mcp` or search the JSON). The browser session shows
history via the web UI (CDP) today.

## Metrics That Matter

- CTR (target 5%+)
- Average view duration (target 40%+)
- Subscriber conversion
- Month-on-month view growth
- Traffic sources (Shorts vs search vs suggested)
