import test from "node:test";
import assert from "node:assert/strict";
import * as m from "./model.mjs";
test("workflow invariants and boundary cases", () => {
    assert.ok(Math.abs(m.rate([{ severity: 10 }]).elo - 1516.1) < 1e-8);
    assert.ok(
        Math.abs(m.rate([{ severity: 0, reason: "cancelled" }]).elo - 1475.4) <
            1e-8,
    );
    assert.ok(
        m.rate([{ severity: 10 }, { severity: 10 }]).elo >
            m.rate([{ severity: 10 }, { severity: 6 }]).elo,
    );
});

test("long disruption and good-service sequences stay inside bands and recover", () => {
    const bad = Array.from({ length: 100000 }, () => ({
            severity: 0,
            reason: "cancelled",
        })),
        good = Array.from({ length: 100000 }, () => ({ severity: 10 }));
    for (const events of [
        bad,
        good,
        bad.concat(good.slice(0, 100)),
        good.concat(bad.slice(0, 100)),
    ]) {
        const r = m.rate(events);
        assert.ok(
            r.history.every((x) => Number.isFinite(x) && x >= 100 && x <= 3500),
        );
    }
    assert.ok(m.rate(bad).elo > 100);
    assert.ok(m.rate(good).elo < 3500);
    assert.ok(
        m.rate(bad.concat(good.slice(0, 100))).elo > m.rate(bad).elo + 100,
    );
});
