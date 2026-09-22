# Sources

Live line status and arrival predictions are fetched from the TfL Unified API.
Collection began 22 September 2026. Observation timestamps and sample counts travel with
the feed. The scoring model is tfl_line_elo.py; its browser port is model.mjs.
The public collector excludes timetable-closed periods and picks the worst active status
where TfL supplies multiple statuses. It keeps at most one observation per quarter-hour.

The old fixture demonstration has been replaced by the live network application.
See TfL data terms: https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service
