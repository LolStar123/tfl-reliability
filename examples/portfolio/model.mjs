export const defaults = {
  disruption: 6,
  line: "Central",
  k: 32,
  events: {
    Central: [10, 10, 6, 6, 10, 10, 10, 10],
    Victoria: [10, 10, 10, 10, 10, 10, 10, 10],
    Northern: [10, 9, 9, 10, 7, 7, 10, 10],
  },
};
export const controls = [
  {
    key: "line",
    label: "Line to disrupt",
    type: "select",
    options: ["Central", "Victoria", "Northern"],
  },
  {
    key: "disruption",
    label: "Next service severity (10 = good)",
    type: "number",
    min: 0,
    max: 10,
    step: 1,
  },
  {
    key: "k",
    label: "Rating sensitivity",
    type: "number",
    min: 1,
    max: 80,
    step: 1,
  },
];
export function rate(events, base = 1500, k = 32) {
  let elo = base,
    streak = 0,
    prev = null;
  const history = [];
  for (const event of events) {
    const s = event.severity,
      quality =
        s === null ? 0.4 : Math.max(0, Math.min(10, Math.trunc(s))) / 10;
    elo += k * (quality - 1 / (1 + 10 ** ((base - elo) / 400)));
    if (s !== null && s < 10) {
      streak = 0;
      elo -= 0.6;
    } else elo += Math.min(2, 0.1 * ++streak);
    if ((event.reason || "").toLowerCase().includes("cancel")) elo -= 8;
    if (prev !== null && s !== null && prev !== s) elo += s > prev ? 3 : -3;
    prev = s;
    history.push(elo);
  }
  return { elo, history };
}
export function run(i) {
  if (i.disruption < 0 || i.disruption > 10 || i.k <= 0)
    throw Error("Choose severity 0-10 and a positive sensitivity.");
  const rows = Object.entries(i.events)
    .map(([line, values]) => {
      const events = values.map((severity) => ({ severity, reason: "" }));
      if (line === i.line)
        events.push({
          severity: i.disruption,
          reason: i.disruption === 0 ? "service cancelled" : "",
        });
      return { line, events, ...rate(events, 1500, i.k) };
    })
    .sort((a, b) => b.elo - a.elo);
  const selected = rows.find((r) => r.line === i.line);
  return {
    summary: `${rows[0].line} leads this service-history replay`,
    metrics: {
      "snapshots replayed": rows.reduce((a, r) => a + r.events.length, 0),
      "selected line Elo": selected.elo.toFixed(1),
    },
    columns: ["rank", "line", "Elo", "snapshots", "good-service share"],
    rows: rows.map((r, n) => [
      n + 1,
      r.line,
      r.elo.toFixed(1),
      r.events.length,
      (
        (100 * r.events.filter((e) => e.severity === 10).length) /
        r.events.length
      ).toFixed(1) + "%",
    ]),
    series: selected.history,
    seriesLabel: i.line + " rating after each snapshot",
    steps: [
      "Collect timestamped line status",
      "Persist snapshots in SQLite in the full pipeline",
      "Replay severity, transitions and cancellation signals",
      "Rank the resulting reliability scores",
    ],
    artifact: rows,
  };
}
