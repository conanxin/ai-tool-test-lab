import test from 'node:test';
import assert from 'node:assert/strict';
import { checkEvidence, EVIDENCE } from '../src/evidence.mjs';

test('all source-backed claims have resolvable source identifiers', () => {
  assert.deepEqual(checkEvidence(), { ok: true, claims: 4, sources: 2 });
  const ids = new Set(EVIDENCE.sources.map(s => s.id));
  for (const c of EVIDENCE.claims.filter(c => c.status === 'SOURCE_BACKED')) assert.ok(ids.has(c.sourceId));
});

test('rejects unsupported source assertions', () => {
  assert.throws(() => checkEvidence({ ...EVIDENCE, claims: [{ id: 'X', status: 'SOURCE_BACKED', sourceId: 'BAD' }] }), /unbacked source claim/);
});

test('assumptions do not silently become sourced facts', () => {
  const a = EVIDENCE.claims.find(c => c.id === 'BT-03');
  assert.equal(a.status, 'MODEL_ASSUMPTION');
  assert.equal(a.sourceId, null);
});
