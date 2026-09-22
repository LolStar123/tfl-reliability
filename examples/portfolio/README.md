# Live Tube reliability

Open the repository root in a terminal:

```sh
python tools/collect_public.py
python -m http.server 8000 --directory examples/portfolio
python -m unittest discover -s tools -p test_public.py
node --test examples/portfolio/model.test.mjs
```

The page fetches real TfL line status on load and every minute while visible. Select a line
and station to inspect live arrival predictions. Download the calculated leaderboard as CSV.
The scheduled workflow stores history on the observations branch and publishes a new feed
four times per hour. All calculations use real observations; no generated records are used.

`live.mjs` owns observation replacement, timeframe selection and rating reconstruction.
`model.mjs` ports the existing Python scoring function. `app.mjs` displays the live network.
