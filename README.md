# TfL train-event Elo

**[Open the live leaderboard](https://lolstar123.github.io/tfl-reliability/)**

All eleven Underground lines on the landing time-series chart, with the ranked table directly below. Coloured line badges, podium positions, arrival
counts, line history and five-minute candles restore the original hackathon dashboard.

![Live train-event leaderboard](examples/portfolio/preview.png)

## What is live

A GitHub collector samples each line's arrival predictions three times, twenty seconds apart,
every ten minutes. Two sightings and an ETA within thirty seconds produce a sampled arrival
estimate. An ETA slipping more than sixty seconds produces a late estimate. These are not
confirmed train movements or network-wide punctuality totals. A disappearing prediction is
**not** treated as a cancellation. The cancellation column is retained for the original layout,
but stays zero in the new live collection without confirmed cancellation evidence.

Every accepted event updates the line's rating using the original event reward/penalty function,
peak weighting, cubic restoring pressure toward 1500, and hard bounds of **100 to 3500**.
The live service dot comes directly from TfL's current status API. Missing data is shown as
unavailable, never replaced by generated observations.

## Original project and recovered history

Built with Benjamin Toze at QuantiHack 2026, after the five-day qualifying trading competition. [Benjamin's event post](https://www.linkedin.com/feed/update/urn:li:activity:7444669989090902016/) records the collaboration. [Devpost](https://devpost.com/software/tfl-elo-tracker)
contains the original screenshots and project account.
[Original team repository](https://github.com/bento-boxing/Quantihack2026project/tree/tfl-live-elo).

Choose **original hackathon archive** to inspect 539 rating observations recovered from the
public SQLite database, recorded on 28 March 2026. The archive preserves its historical scoring
and inferred cancellation counts. It is clearly labelled and never mixed into current counts.
The former tfl-elo.uk endpoint was unavailable when this restoration was made.

## Run and inspect

```sh
python -m http.server 8000 --directory examples/portfolio
python -m unittest discover -s tools -p 'test_*.py'
node --test examples/portfolio/model.test.mjs
pip install playwright
python -m playwright install chromium
python tools/browser_audit.py
```

| File | Purpose |
| --- | --- |
| `tools/collect_events.py` | Live prediction reconciliation and bounded event updates |
| `tfl_train_event_elo.py` | Original event model and SQLite collector |
| `tfl_train_event_dashboard.py` | Original Streamlit dashboard |
| `examples/portfolio/app.mjs` | Restored browser leaderboard, history, candles and event log |
| `examples/portfolio/data/archive.json` | Recovered original rating observations |
| `tools/audit_public.py` | Freshness, limits, eleven-line coverage and score agreement |
| `tools/browser_audit.py` | Public controls, charts, export, mobile and failure-state checks |
| `.github/workflows/example-pages.yml` | Collection, durable history, audit and publication |

The separate status-based model remains in `tfl_line_elo.py` for comparison; it no longer
supplies the landing page's event ratings. Collected state lives on the `observations` branch,
not in source commits. Every ten-minute run audits the data before publishing and verifies the
public feed afterwards. Browser checks run after deployment and every four hours. GitHub's
scheduler is best effort, so data timestamps remain visible.

Tests include 100,000 consecutive adverse or favourable observations, recovery, duplicate
sightings, missing predictions and exact agreement between status-model implementations.

Transport data: [TfL Unified API](https://tfl.gov.uk/info-for/open-data-users/).
