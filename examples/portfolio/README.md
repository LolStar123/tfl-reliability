# Tube reliability dashboard

Serve this directory with `python -m http.server 8000 --directory examples/portfolio` from the repository root, then open http://localhost:8000.

The ranking, history, source switch, candles, events and CSV use real collected observations. The browser checks the durable observation feed every five minutes while visible; the bundled event snapshot is the fallback. Current service status comes separately from TfL.

See the [repository guide](../../README.md) for scoring, collector setup, checks and the code map, and [provenance](../../PROVENANCE.md) for the archive boundary.
