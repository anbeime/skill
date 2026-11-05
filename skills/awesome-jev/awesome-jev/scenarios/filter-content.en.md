<!-- Generated from data/scenarios.json + data/projects.json. -->
[← Back to discovery](../README.md#discovery)

# Filter news & content

Keep relevant information and skip unwanted content.

**Where JEV fits**

Collected content → JEV relevance or category judgment → application filters or forwards items

## Projects to learn from

### [NewsJack](https://github.com/elvisun/newsjack)

An open-source PR workflow that screens a live news feed for timely brand opportunities.

**What to reference:** Headline screening before an agent develops PR opportunities.

[Source](https://github.com/elvisun/newsjack/tree/092d882fc69912622f620c50eb493afe625f99dc/demos/news-desk-dealer)

### [Bluenoise](https://github.com/rokcso/bluenoise)

An X/Twitter filtering extension using local rules by default, with optional Jev checks for unmatched replies.

**What to reference:** Optional JEV checks after deterministic reply-filtering rules.

[Source](https://github.com/rokcso/bluenoise/blob/ef81ea7a7c3677501d6de8f9235a4d6a866b573a/entrypoints/background.ts)

### [Youtube Sponsor Detection](https://github.com/trungdq88/youtube-sponsor-detection)

YouTube extension detecting sponsored segments from live audio and transcripts using Jev, skipping promotional blocks automatically.

**What to reference:** Classifying transcript segments before player controls skip sponsorships.

[Source](https://github.com/trungdq88/youtube-sponsor-detection/blob/de01f0568d043035889a296a61ce21e0accc8b16/extension/lib/jev.js#L1-L541)

These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.

[Try the free JEV API](https://docs.beatapi.io/decisions#free-calls) · [Search with your agent](../docs/agent-search.en.md)
