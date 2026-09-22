import test from 'node:test';
import assert from 'node:assert/strict';
import * as m from './model.mjs';
test('workflow invariants and boundary cases',()=>{
assert.ok(Math.abs(m.rate([{severity:10}]).elo-1516.1)<1e-8);assert.ok(Math.abs(m.rate([{severity:0,reason:'cancelled'}]).elo-1475.4)<1e-8);assert.ok(m.rate([{severity:10},{severity:10}]).elo>m.rate([{severity:10},{severity:6}]).elo);
});
