# Live Tube reliability

Open the repository root in a terminal:

```sh
python tools/collect_public.py
python -m http.server 8000 --directory examples/portfolio
python -m unittest discover -s tools -p test_public.py
node --test examples/portfolio/*.test.mjs
```

The page fetches current TfL status and the durable train-event feed on load, then checks the
feed every five minutes while visible. Select a line to focus its history or download the
calculated leaderboard as CSV. Scheduled jobs store six audited ten-minute collection cycles
on the observations branch. All calculations use real observations; no generated records are
used.

`live.mjs` owns observation replacement, timeframe selection and rating reconstruction.
`model.mjs` ports the existing Python scoring function. `app.mjs` displays the live network.
