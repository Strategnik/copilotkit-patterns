# Patterns — ad landing pages

One landing page per agent-native pattern, each the destination for the paid-social ad that
promises it, plus a gallery. A third landing-page type alongside the scorecard and the
what-are-you-building preference page: a pattern-specific page (with the gallery as its strip)
that matches the C1–C5 ad promises. It adds to the mix — the scorecard ads are not replaced.

| Key | Page | Ads it catches |
|---|---|---|
| c1 | `/patterns/shared-state` | "One surface. Agent and user, same state." · "Build agent-native, not chat-adjacent." |
| c2 | `/patterns/generative-ui` | "Generative UI: components, not paragraphs." · "Your design system, driven by the agent." |
| c3 | `/patterns/multi-agent` | "Multi-agent flows that stay coherent." · "Sub-agents, one conversation." |
| c4 | `/patterns/channels` | "One agent. Every channel." · "Ship your agent to Slack." |
| c5 | `/patterns/human-in-the-loop` | "Copilots that act — with approval." · "A copilot that acts inside your workflows." |
| c6 | `/scorecard` (unchanged) | "Score your agent's production readiness." · "Production readiness, scored." |
| — | `/patterns` | gallery of the five + the scorecard |

Each page: eyebrow + H1 (the ad headline, accent word marker-swept), the ad body expanded, two
CTAs (live Dojo demo / docs guide), a real code snippet lifted from the showcase demo source,
a copyable install command, three "how it works" steps, a scorecard + talk-to-an-engineer band,
and a strip of the other patterns. CopilotKit brand system (same tokens/treatment as the
scorecard and preference pages; scene animations reused from the preference tiles).

## Files
- `patterns.json` — the registry: copy, URLs, code, steps, metadata per pattern
- `template.html` — pattern page template · `index-template.html` — gallery template
- `build.py` — generator (`python3 build.py --out <dir> [--base /patterns] [--asset ../]`)
- `logo-*.svg`, `icons/` — brand assets (icons: Noun Project, see `icons/ATTRIBUTION.txt`)
- `_previews/` — screenshots (desktop full page, gallery, mobile)

Edit the JSON/templates, never the generated HTML.

## Where it ships
- **Site:** `CopilotKit/website` PR #567 (draft) — `public/campaign-pages/patterns/**` +
  `src/app/(default)/patterns/{page,[slug]/page}.tsx` iframing through `CampaignFrame`, exactly
  like `/scorecard`. Rebuild for the site with `--base /patterns --asset ../` into
  `public/campaign-pages/patterns/`.
- **Standalone preview:** https://cpk-patterns.vercel.app (Strategnik Vercel project
  `cpk-patterns`; built with `--base "" --asset ../`).

## Capture — the declare tile (added 2026-09-10)
Every pattern page carries one capture surface, "Building this? → This is what I'm building."
It writes `nurture_use_case` (t1…t5, the same keys as the what-are-you-building page) plus
`cpk_paid_platform` / `cpk_paid_concept` / `cpk_last_landing_page` to HubSpot form
`2bb9a249-b5c8-4243-8f1f-185eee140b72` ("Patterns · Declare", portal 45532593). A visitor the
HubSpot cookie knows is stitched on one click and then offered an optional email; an unknown
visitor gives one email ("where should we send the demo source and the guide?"). `?demo=1`
disables submission. Events: `patterns_declared {identified, with_email}`, `patterns_declare_failed`.
Setting `nurture_use_case` enrolls the existing Use-Case Nurture flow. The retargeting lists
and audiences that hang off this are in `../retargeting/README.md`.

## Measurement (the retargeting ladder)
The documents load no scripts. They post bridge events to the same-origin parent
(`CampaignFrame`), which captures them in PostHog and — when a Meta pixel is installed on the
parent page — mirrors them as `fbq("trackCustom", …)`:

| Rung | Events |
|---|---|
| 1 · viewed | `patterns_page_viewed` |
| 2 · engaged | `patterns_demo_clicked`, `patterns_guide_clicked`, `patterns_install_copied`, `patterns_pattern_switched` |
| 3 · intent | `patterns_scorecard_clicked`, `patterns_engineer_clicked` |

Every event carries `pattern` (slug or `index`). **There is no Meta pixel on copilotkit.ai
today** (ad account owns zero datasets; site loads GA4 only). Installing one is a CopilotKit
decision — EU consent applies since the ads run in GB/DE/FR/NL/SE. Until then the ladder
exists in PostHog only; Meta retargeting is limited to on-platform engagement audiences.

## Meta ads
**Additive, not a replacement.** The scorecard ads keep running exactly as they are. 20 paused
creatives + ads (C1–C5 × a/b × contacts/lookalike → the pattern URLs,
`utm_content=<key>_contacts|_lookalike`) exist as an optional parallel landing-page arm; they
only run if Nick chooses to test the pattern pages alongside the scorecard after PR #567
merges. Notes in `meta/meta_state.json → patterns_repoint_2026_09_10`.
