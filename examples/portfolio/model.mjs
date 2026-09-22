// Browser port of tfl_line_elo.calculate_elo_for_line; closed periods are excluded by live.mjs.
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
