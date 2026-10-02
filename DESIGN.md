# Tube reliability

The page is a departure board for comparing all eleven Underground lines. The primary action is to inspect a line's current rating and its recorded history.

## Direction and references

The original hackathon dashboard supplies line colours and ranking. A station departure board supplies the left-to-right scan: rank, line, service, rating. These are product references, not copied website identities. The existing public demo was inspected before editing: its full-width chart pushed ranking below the fold and its compressed type was difficult to read.

```
Product / observation timestamp
Source, refresh, CSV
Current ranking (11 lines) | History / timeframe / line selection
Sampling and scoring note
```

## Tokens

- Ground `#0d151d`, surface `#14212d`, rule `#2d4152`, text `#f1f4f6`, secondary `#a9bac7`, rating `#efcf79`.
- Official line colours identify lines; readable white names sit beside a coloured edge. The Northern trace uses light grey in the chart for visibility.
- Display: local Arial Narrow/Segoe UI, 36-44px. Body: local Segoe UI, 14-16px. Data: local Consolas/monospace. No font downloads or external font dependency.
- 8px spacing base, 24px column gap, 1180px content width. A ranking column sits beside the chart from 960px; below it, ranking precedes history.
- All actionable controls have visible focus and at least 40px height. The source switch stays visible. Service state has text in addition to colour.
- Chart dimensions follow the actual container so axis labels stay legible. Points remain real observations; lines and scoring are unchanged.

## Behaviour and acceptance

First load shows live collection and all eleven lines. Source switching labels the hackathon archive. Timeframes, single-line focus, show-all, refresh and CSV remain available. Ratings stay in 100..3500; collection and history continuity are untouched. No invented cancellation evidence.

Acceptance: 1280px and 390px renders, no overflow or JavaScript errors, all eleven ranking rows and polylines, monotonic timeframe coverage, focus/show-all, archive/live switch, CSV, API fallback, keyboard focus, reduced motion. Review in three bounded passes: function, system, craft. CSS/SVG only; animations stop with reduced motion.

## Copy audit

Named emotion and generic marketing claims: none. Rejected: "data-driven insights", "seamless experience", "powerful dashboard". The unresolved limitation is sampling: prediction sightings are not confirmed train movements. Narrative quotas, sensory anecdotes and personal costs do not fit a technical interface; none are invented.

## Completed review

Function, design-system and visual-craft passes completed at 1280px and 390px in isolated Chrome. Main controls, invalid inputs, visible focus and reduced motion were checked; screenshots were opened and inspected. The repository guide uses the actual implementation and names its data limits. Full audit records, state screenshots, copy audit and metadata proposals are kept in ignored `output/qa/`.
