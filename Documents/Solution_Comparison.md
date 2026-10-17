# Original vs Current Solution — Comparison

## Overview

| Aspect | Original (Claude + Web Search) | Current (Interlinked + Gemini) |
|---|---|---|
| LLM | Claude Sonnet via Anthropic API | Gemini 2.5 Flash via Interlinked |
| Web Search | Live — Claude's built-in web search with domain restriction | None — relies on LLM training knowledge |
| API Calls per Lookup | 2-6+ (discovery + lookup + pause loops) | 1 |
| Data Source | Official CAD websites (verified, real-time) | LLM memory (static, unverified) |
| Output | JSON via CLI | JSON + Markdown + Streamlit UI |

## Where Original Wins(Paid LLM Call)

- **Live data** from official county appraisal district websites.
- **Domain restriction** (`allowed_domains`) guarantees data comes only from official CAD sources.
- **Iterative search** — Claude searches multiple times, follows links, and reads full pages.
- **Diagnostic metadata** — reports exactly what was searched, what matched, and what failed.
- **Honesty** — clearly distinguishes verified data from unavailable fields.

## Where Current Wins (Free Tier)

- **Single LLM call** — faster, cheaper, simpler.
- **Web UI** — Streamlit interface with preview, download buttons.
- **Dual export** — auto-saves JSON and Markdown to outputs folder.
- **Zero API cost** — runs through Interlinked floodgate, no billing.
- **Simpler codebase** — ~130 lines vs ~400 lines.

## Current System — Limitations (Free Tier)

1. **No live web search.** Data comes from Gemini's training knowledge, not real-time lookups. Property records may be outdated or inaccurate.
2. **Source URLs are generated, not visited.** The `sources` field contains plausible URLs, but Gemini never actually accessed them.
3. **No domain restriction.** Cannot guarantee data originates from official government sources.
4. **Low field coverage.** ~17 out of 87 fields populated in testing. Construction details, utilities, flood data, and valuation fields are mostly null.
5. **No verification mechanism.** No way to confirm if owner name, year built, or zoning data is current and correct.
6. **Interlinked floodgate blocks Google Search grounding.** The `Tool('google_search')` serializes correctly but is rejected server-side with a 403.
7. **Network restrictions block external web access.** Direct HTTP calls to public websites are blocked by the local proxy.

## Future Path — Enabling Live Search

The current Interlinked-based solution is **static and incapable of dynamic web search**. However, two proven approaches exist for production:

- **Claude Sonnet with Web Search** — supports `allowed_domains` to lock searches to official CAD sites. Best accuracy, iterative deep search, but higher cost (~$0.05-0.15 per lookup).
- **Gemini with Google Search Grounding** — native search via `google_search` tool. Cheaper (~$0.002-0.05 per lookup), but searches Google snippets rather than reading full pages.

Either can be integrated into the current tool's architecture by replacing the LLM client module — the prompt, formatter, exporter, and Streamlit UI remain unchanged.

## Recommendation

Use the current solution as a **working POC** to validate the workflow and UI. For production, switch the LLM backend to Claude Sonnet (if official-source-only data is required) or Gemini with grounding (if general web sources are acceptable).
