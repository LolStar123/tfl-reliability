import test from "node:test";
import assert from "node:assert/strict";
import { eventSeries } from "./live.mjs";

test("event series expands run snapshots into real train observations", () => {
    const feed = {
        started: "2026-09-28T00:00:00Z",
        lines: {
            central: { id: "central" },
            victoria: { id: "victoria" },
        },
        history: [
            {
                at: "2026-09-28T00:10:00Z",
                ratings: { central: 1510, victoria: 1520 },
            },
            {
                at: "2026-09-28T00:30:00Z",
                ratings: { central: 1550, victoria: 1540 },
            },
        ],
        events: [
            {
                at: "2026-09-28T00:20:00Z",
                line_id: "central",
                elo: 1514,
            },
            {
                at: "2026-09-28T00:20:00Z",
                line_id: "central",
                elo: 1518,
            },
            {
                at: "2026-09-28T00:20:20Z",
                line_id: "victoria",
                elo: 1526,
            },
        ],
    };
    const series = eventSeries(feed);
    assert.equal(series.length, 4);
    assert.deepEqual(series[0].ratings, { central: 1510, victoria: 1520 });
    assert.deepEqual(series[1].observed, ["central"]);
    assert.equal(series[1].eventCount, 1);
    assert.deepEqual(series[1].ratings, { central: 1514, victoria: 1520 });
    assert.deepEqual(series[2].observed, ["central"]);
    assert.deepEqual(series[2].ratings, { central: 1518, victoria: 1520 });
    assert.deepEqual(series[3].observed, ["victoria"]);
    assert.equal(series[3].eventCount, 1);
    assert.deepEqual(series[3].ratings, { central: 1518, victoria: 1526 });
    assert.ok(series.every((point, index) => !index || Date.parse(point.at) >= Date.parse(series[index - 1].at)));
});

test("event series retains the coarse fallback when raw events are unavailable", () => {
    const series = eventSeries({
        started: "2026-09-28T00:00:00Z",
        lines: { central: { id: "central" } },
        history: [
            {
                at: "2026-09-28T00:10:00Z",
                ratings: { central: 1510 },
            },
        ],
    });
    assert.equal(series.length, 2);
    assert.equal(series.at(-1).ratings.central, 1510);
});
