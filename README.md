# TfL Reliability — Live Elo Ratings for the London Underground

A real-time data pipeline that polls Transport for London's open API, persists every
line- and train-level status snapshot to SQLite, and turns that history into an
**Elo-style reliability rating** for each Tube line — the same rating maths used to rank
chess players, applied to which lines actually run on time.

> Built end-to-end: API ingestion → event detection → rating model → persistence →
> dashboard. No external services; runs from a single `python` command.

---

## What it does

- **Ingests** live line-status and per-train arrival predictions from the
  [TfL Unified API](https://api.tfl.gov.uk) (rate-limit aware, optional app credentials).
- **Detects events** from successive snapshots — status changes, delays, suspensions,
  cancellations — rather than trusting a single instantaneous reading.
- **Rates** each line with an event-driven Elo update: a line "wins" when it holds Good
  Service and "loses" on disruptions, so a noisy line drifts down and a dependable one
  climbs. Tunable `--base-elo` and `--k-factor`.
- **Persists** every snapshot to indexed SQLite for reproducible re-ranking over any
  lookback window.
- **Visualises** disruption trends in a Streamlit dashboard.

## Two granularities

| Script | Granularity | Use |
|--------|-------------|-----|
| `tfl_line_elo.py` | Line-level status | Lightweight; one snapshot ≈ all lines |
| `tfl_train_event_elo.py` | Per-train stop-call events | Higher fidelity; continuous polling |

A third module, `tfl_fare_data.py`, encodes the full 2025/26 TfL fare ruleset
(peak/off-peak, zone caps, Railcard discounts) — used to reason about cost alongside
reliability.

## Quick start

```bash
pip install -r requirements.txt

# Collect one snapshot of every line
python tfl_line_elo.py collect --iterations 1

# Compute the reliability leaderboard over the last 24h
python tfl_line_elo.py rank --lookback-hours 24

# Or run a continuous collector (one snapshot per minute, forever)
python tfl_line_elo.py collect --interval 60 --iterations 0
```

Per-train event tracking + live dashboard:

```bash
python tfl_train_event_elo.py monitor --line-ids victoria,central,northern --interval 60 --iterations 0
python -m streamlit run tfl_train_event_dashboard.py
```

Optional TfL API credentials (higher rate limits):

```bash
set TFL_APP_ID=your_app_id
set TFL_APP_KEY=your_app_key
```

## Sample output

```
line_id        line_name         elo      good_ratio  latest_status
victoria       Victoria          1523.88  1.00        Good Service
piccadilly     Piccadilly        1517.69  0.00        Minor Delays
metropolitan   Metropolitan      1498.82  0.00        Part Closure
northern       Northern          1489.39  0.00        Part Suspended
circle         Circle            1487.81  0.00        Severe Delays
```

Full leaderboard is written to `tfl_line_elo_leaderboard.csv` on each `rank`.

## Design notes

- **Event-driven, not poll-driven scoring.** Elo updates fire on *transitions* between
  snapshots, so a line sitting in "Minor Delays" for an hour isn't penalised sixty times.
- **Reproducible.** Ratings are derived from the snapshot table, so changing the model
  (K-factor, priors) and re-running `rank` recomputes the whole history — no lossy state.
- **Honest about what it measures.** This is an Elo-style *reliability* signal from public
  status feeds, not official TfL punctuality statistics.

## Stack

Python 3 · SQLite · TfL Unified API · pandas / numpy · Streamlit · matplotlib

## Layout

```
tfl_line_elo.py              line-level collector + Elo ranking CLI
tfl_train_event_elo.py       per-train event collector + monitor + ranking CLI
tfl_train_event_dashboard.py Streamlit dashboard
tfl_fare_data.py             2025/26 TfL fare ruleset (zones, caps, Railcards)
*_leaderboard.csv            sample ranking output
```

> Databases (`*.db`) are generated locally on first run and are gitignored.
