# X Search Query Recipes

> The signal scout's core tool. X search is a real-time, underrated
> intelligence layer — near real-time indexing of billions of posts. These
> recipes find content ideas, niches, and audience questions that Google-style
> keyword tools miss entirely.

## How To Use

- Swap the `<pillar>` / `<keyword>` / `<niche>` placeholder for the pillar
  being searched (migration, agents, content pipeline, mining, omnigate, etc.)
- Set the engagement floor (`min_faves:`) according to the goal
- Run via the `x_search` tool, or the X search UI, or the captured
  `SearchTimeline` API endpoint (see `platforms/x.md`)
- Save recurring queries so the scout can check them weekly

## Core Recipes

### 1. Content Idea Mining (proven engagement)

```
("<pillar>" OR "<related term>") lang:en -filter:replies min_faves:100 since:<30 days ago>
```

Finds original, high-engagement posts on the topic. Strip reply noise. The
result is a list of proven angles — what the audience already rewards.

### 2. Questions Your Audience Is Asking (headline gold)

```
("how do I" OR "any tips for" OR "can someone explain") "<keyword>" ? -filter:links
```

Every question is a potential post. The people asking are the readers; the
question is the headline.

### 3. Pain Points / Gaps (positioning opportunities)

```
("frustrated with" OR "looking for alternative" OR "does anyone know") "<keyword>" min_faves:1
```

Set the floor at 1 to catch genuine human posts (filters out bots) and find
conversations before they crest.

### 4. Viral Pattern Study (reverse-engineer what works)

```
"<keyword>" min_faves:500 -filter:replies since:<90 days ago>
```

Study the formats, hooks, and angles that broke through. Look for patterns:
thread-style storytelling? data-backed? contrarian? List the 3-4 formats and
build the calendar around them.

### 5. Authority Clip Hunting (source material)

```
"<keyword>" filter:links min_faves:50 since:<90 days ago>
```

Finds posts with links — articles, demos, evidence. Source material for the
researcher.

### 6. Emerging Conversations (early signal)

```
"<keyword>" min_faves:3 min_retweets:2
```

Low floor + Latest sort. Catches momentum before it peaks. Publishing a strong
take on an emerging topic is how authority builds early.

### 7. Competitor / Peer Gap Audit (weekly)

```
from:<peer-account> since:<30 days ago>
"<peer-account>" -from:<peer-account> min_replies:5
```

First: what they say. Second: how the community responds. High-reply/low-like
= controversy or confusion (positioning opportunity). High-like/high-retweet =
what resonates with the shared audience.

## Combined Query (the workhorse)

```
("<pillar>" OR "<related>") lang:en -filter:replies min_faves:100 since:<30d> -buy -discount -sale -job -hiring
```

The negative keywords strip commercial spam. This is the scout's default.

## Notes

- X search index is near real-time (minutes, not days) — the "now" signal
- Advanced Search UI is desktop-only; operators work in the mobile bar too
- Save recurring searches (three-dot menu → Save search) for weekly checks
- The `x_search` Hermes tool is the agent-native path; the captured
  `SearchTimeline` API endpoint is the direct-call path
