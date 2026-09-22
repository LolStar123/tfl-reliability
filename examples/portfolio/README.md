# tube reliability: working example

Replay line-status events and introduce a disruption to see the ratings change.

**[Open the demo](https://lolstar123.github.io/tfl-reliability/)** · [Calculation / workflow code](model.mjs) · [Checks](model.test.mjs)

![Example output](preview.png)

## Run it

From the repository root, with Python 3 and Node.js 22:

```sh
python -m http.server 8000 --directory examples/portfolio
```

Open http://localhost:8000. Change an input, or edit the JSON fixture, then export the computed result as JSON or CSV.

```sh
node --test examples/portfolio/model.test.mjs
```

## What it does

Poll TfL status feeds, save timestamped snapshots in SQLite and replay the history into line ratings. Delays, cancellations, service changes and recovery all contribute to the ranking.

## Scope and source

Sample service events. Ratings are this project's reliability measure, not official TfL punctuality statistics.

tfl_line_elo.py: quality_from_severity and calculate_elo_for_line. Browser scoring ports those functions.

`model.mjs` is the small public implementation. `app.mjs` connects its inputs and outputs to the browser. No package install or network key is needed to run the example. GitHub Pages runs the same files after the checks pass.
