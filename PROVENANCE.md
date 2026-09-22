# Data and model provenance

Original team source: https://github.com/bento-boxing/Quantihack2026project/tree/tfl-live-elo
Original screenshots and write-up: https://devpost.com/software/tfl-elo-tracker

`data/archive.json` contains only the original public SQLite `line_elo_snapshots` table:
539 rows between 2026-03-28 16:02 and 17:00 UTC. Historical ratings are 621 to 2415.
No historical records are presented as current service.

`data/events.json` is generated from fresh TfL Line Arrivals responses. See collector source
for the conservative sampling definition. Inferred stop calls are not official punctuality.
No user accounts, API keys or private journey records are included.

The original event gain/loss function is reused. Cubic gravity and 100?3500 limits are new
safeguards. This update deliberately avoids the original disappearing-prediction cancellation
heuristic. It does not claim to implement standard zero-sum pairwise Elo.

The event photograph was supplied by Atul from his clipboard for this page. Its rights remain with its owner; the code license does not license the photograph. The project account is sourced to Benjamin Toze's linked LinkedIn post.
