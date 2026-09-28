import { rate } from "./model.mjs";
export const colours = {
    bakerloo: "#ad713b",
    central: "#db3935",
    circle: "#e8bf30",
    district: "#32805a",
    "hammersmith-city": "#c98c9a",
    jubilee: "#879299",
    metropolitan: "#8e375d",
    northern: "#303237",
    piccadilly: "#4168aa",
    victoria: "#54a3c1",
    "waterloo-city": "#78b6a9",
};
export function flatten(payload) {
    if (!Array.isArray(payload) || payload.length !== 11)
        throw Error("TfL did not return all eleven lines.");
    return payload.map((l) => {
        if (!l.lineStatuses?.length)
            throw Error("TfL returned an incomplete line status.");
        const active = l.lineStatuses.filter((s) => s.statusSeverity !== 20),
            s = (active.length ? active : l.lineStatuses).reduce((a, b) =>
                a.statusSeverity < b.statusSeverity ? a : b,
            );
        return {
            id: l.id,
            name: l.name,
            severity: s.statusSeverity,
            status: s.statusSeverityDescription,
            reason: [...new Set(l.lineStatuses.map((s) => s.reason || ""))]
                .join(" ")
                .trim(),
        };
    });
}
export function mergeLive(feed, lines, at) {
    const bucket = Math.floor(Date.parse(at) / 600000);
    return {
        ...feed,
        updated: at,
        snapshots: [
            ...feed.snapshots.filter(
                (s) => Math.floor(Date.parse(s.at) / 600000) !== bucket,
            ),
            { at, lines },
        ].sort((a, b) => Date.parse(a.at) - Date.parse(b.at)),
    };
}
export function leaderboard(feed, hours = 24) {
    const cutoff = Date.parse(feed.updated) - hours * 3600000,
        snapshots = feed.snapshots.filter((s) => Date.parse(s.at) >= cutoff),
        latest = feed.snapshots.at(-1);
    return latest.lines
        .map((line) => {
            const obs = snapshots.flatMap((s) => {
                    const l = s.lines.find((l) => l.id === line.id);
                    return l && l.severity !== 20 ? [{ ...l, at: s.at }] : [];
                }),
                r = rate(
                    obs.map((l) => ({
                        severity: l.severity,
                        reason: l.reason,
                    })),
                );
            return {
                ...line,
                elo: r.elo,
                observations: obs.length,
                good: obs.length
                    ? obs.filter((o) => o.severity === 10).length / obs.length
                    : null,
                history: r.history.map((elo, i) => ({
                    at: obs[i].at,
                    elo,
                    status: obs[i].status,
                })),
            };
        })
        .sort((a, b) => b.elo - a.elo || a.name.localeCompare(b.name));
}

export function eventSeries(feed) {
    const ids = new Set(Object.keys(feed.lines || {})),
        ratings = Object.fromEntries([...ids].map((id) => [id, 1500])),
        history = [...(feed.history || [])]
            .filter((row) => Number.isFinite(Date.parse(row.at)))
            .sort((a, b) => Date.parse(a.at) - Date.parse(b.at)),
        events = [...(feed.events || [])]
            .filter(
                (event) =>
                    ids.has(event.line_id) &&
                    Number.isFinite(event.elo) &&
                    Number.isFinite(Date.parse(event.at)),
            )
            .sort((a, b) => Date.parse(a.at) - Date.parse(b.at));
    if (!events.length)
        return [
            { at: feed.started, ratings: { ...ratings }, observed: [] },
            ...history.map((row) => ({
                at: row.at,
                ratings: { ...row.ratings },
                observed: [...ids],
            })),
        ];

    const firstEvent = Date.parse(events[0].at),
        series = [];
    for (const row of history.filter((row) => Date.parse(row.at) < firstEvent)) {
        Object.assign(ratings, row.ratings);
        series.push({
            at: row.at,
            ratings: { ...ratings },
            observed: [...ids],
            eventCount: 0,
        });
    }
    if (!series.length)
        series.push({
            at: feed.started,
            ratings: { ...ratings },
            observed: [],
            eventCount: 0,
        });

    for (const event of events) {
        ratings[event.line_id] = event.elo;
        series.push({
            at: event.at,
            ratings: { ...ratings },
            observed: [event.line_id],
            eventCount: 1,
        });
    }
    return series;
}
