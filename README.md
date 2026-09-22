# the tube, ranked

**[Open the live network](https://lolstar123.github.io/tfl-reliability/)** ? [Collector](tools/collect_public.py) ? [Frontend](examples/portfolio/app.mjs)

All eleven lines, current TfL service messages, observed-history Elo and live station arrivals.
Opening the page requests current service; the cloud collector retains observations every
15 minutes so the ratings keep building when nobody has the page open. The page displays
collection start, observation counts and freshness. Missing data stays missing.

<img src="examples/portfolio/preview.png" alt="Live Tube reliability leaderboard and line detail" width="900">



<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="TfL reliability: live service data ranked as an event stream" src="assets/banner-light.svg" width="100%">
</picture>

# TfL reliability

Which Tube line is actually running best? This project polls Transport for London's live
status and arrival feeds, preserves the observations in SQLite, and converts them into
Elo-style reliability rankings.

The difficult part is temporal: successive predictions must be reconciled into arrivals,
late trains, and cancellations without scoring the same disruption on every poll. The
repository includes both a lightweight line-status model and a stop-call event model,
plus a Streamlit dashboard for inspecting the signal.

## The published data

The public feed starts with real observations collected on 22 September 2026. Its history
is deliberately labelled short during warm-up. Current service comes directly from TfL;
ratings use the stored observations and the same scoring function as the Python collector.

- [Collected feed](https://lolstar123.github.io/tfl-reliability/data/network.json)
- [Durable observation history](https://github.com/LolStar123/tfl-reliability/tree/observations)
- [Collection and deployment runs](https://github.com/LolStar123/tfl-reliability/actions/workflows/example-pages.yml)

Scheduled Actions can be delayed. The page keeps the last successful observation visible
with its timestamp when a request fails. It never substitutes generated service events.
Repeated refreshes replace the current quarter-hour record, avoiding duplicate score updates.
Service-closed periods do not count as running-service failures.

## Signal path

```mermaid
flowchart LR
    API["TfL Unified API"] --> COLLECT["Status and arrival collectors"]
    COLLECT --> DB[("Indexed SQLite history")]
    DB --> LINE["Line-status Elo model"]
    DB --> EVENT["Stop-call event model"]
    LINE --> CSV["Reproducible CSV ranking"]
    EVENT --> CSV
    EVENT --> UI["Streamlit investigation dashboard"]
```

The two scoring paths answer different questions:

| Path | Observation | Best for |
|---|---|---|
| `tfl_line_elo.py` | One status for each line per poll | A fast network-wide readout |
| `tfl_train_event_elo.py` | Predictions sampled at individual stops | Arrival, lateness, and cancellation evidence |

Line-status Elo uses TfL severity as the outcome, rewards sustained Good Service, and
penalises adverse transitions and cancellation mentions. The train-event model resolves
successive stop predictions, gives peak-hour failures more weight, and applies slower
movement near the score boundaries. Both models rebuild rankings from stored evidence.

## Run it

Python 3.9 or newer is required because the train-event path uses `zoneinfo`.

```powershell
git clone https://github.com/LolStar123/tfl-reliability.git
cd tfl-reliability
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Capture two line-status snapshots, then rank the last 24 hours.
python tfl_line_elo.py collect --iterations 2 --interval 60
python tfl_line_elo.py rank --lookback-hours 24
```

The public TfL endpoints work without credentials. For higher API limits, set
`TFL_APP_ID` and `TFL_APP_KEY` in the environment; both CLIs also accept `--app-id` and
`--app-key` before the subcommand.

For the train-event view, keep the monitor running in one terminal:

```powershell
python tfl_train_event_elo.py monitor --max-stops-per-line 4 --interval 60 --iterations 0
```

Then open the dashboard from a second terminal:

```powershell
python -m streamlit run tfl_train_event_dashboard.py
```

![Dark TfL reliability dashboard showing the live train-event Elo table](assets/dashboard.png)

The screenshot uses a three-cycle live sample from 19 rotating stops on 30 July 2026. It
demonstrates the interface and collector, not a claim about whole-network performance.

## Repository map

| File | Responsibility |
|---|---|
| `tfl_line_elo.py` | Line-status ingestion, SQLite schema, ranking CLI |
| `tfl_train_event_elo.py` | Stop sampling, event reconciliation, train-event scoring |
| `tfl_train_event_dashboard.py` | Live status overlay, tables, event feed, charts |
| `tfl_fare_data.py` | Separate 2025/26 fare and capping reference module |
| `*_leaderboard.csv` | Captured model outputs for inspection |

Generated `*.db` files stay local and are ignored by Git. To contribute, keep ingestion,
event resolution, and scoring changes separate where possible; run
`python -m compileall -q .` and exercise the relevant CLI before opening a pull request.

This project is available under the [MIT License](LICENSE). TfL data remains subject to
Transport for London's own terms.
