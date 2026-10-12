import test from 'node:test';
import assert from 'node:assert/strict';
import { BTree, makeExampleTree } from '../src/btree.mjs';

test('initial empty tree has valid root and misses safely', () => {
  const tree = new BTree();
  assert.equal(tree.validate().height, 0);
  assert.deepEqual(tree.values(), []);
  assert.equal(tree.search(42).found, false);
  assert.deepEqual(tree.search(42).steps.map(s => s.kind), ['visit', 'missing']);
});

test('supports insertion, root split, non-root splits, and sorted order', () => {
  for (const t of [2, 3, 4, 6]) {
    const tree = new BTree(t);
    const inputs = [70, 40, 80, 5, 30, 10, 20, 50, 60, 90, 15, 75, 65, 85, 55, 35, 45, 25];
    for (const value of inputs) {
      assert.equal(tree.insert(value), true);
      assert.equal(tree.validate().keys, tree.size);
    }
    assert.deepEqual(tree.values(), [...inputs].sort((a, b) => a-b));
    for (const value of inputs) assert.equal(tree.search(value).found, true);
    assert.ok(tree.validate().height >= 1);
    assert.equal(tree.insert(inputs[0]), false);
    assert.equal(tree.size, inputs.length);
  }
});

test('search trace is deterministic, accurate, and contiguous', () => {
  const tree = makeExampleTree();
  for (const value of [-100, -1, 0, 5, 19, 25, 40, 57, 90, 999]) {
    const trace = tree.search(value);
    assert.equal(trace.found, tree.values().includes(value));
    const visits = trace.steps.filter(step => step.kind === 'visit');
    assert.equal(visits.length, trace.steps.filter(s => s.kind === 'descend').length + 1);
    for (let i = 0; i < visits.length; i++) assert.equal(visits[i].depth, i);
    assert.ok(['found', 'missing'].includes(trace.steps.at(-1).kind));
    assert.equal(trace.steps.at(-1).nodeId, trace.nodeId);
    for (let i = 0; i < trace.steps.length - 1; i++) {
      if (trace.steps[i].kind === 'descend') assert.equal(trace.steps[i+1].nodeId, trace.steps[i].childId);
    }
    assert.ok(visits.length <= tree.validate().height + 1);
  }
});

test('uses only safe integer keys and rejects invalid minimum degree', () => {
  for (const degree of [1, 0, 2.5, Infinity, '2', 65]) assert.throws(() => new BTree(degree));
  const tree = new BTree();
  for (const input of ['3', NaN, Infinity, 1.25, Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => tree.insert(input), TypeError);
    assert.throws(() => tree.search(input), TypeError);
  }
  tree.insert(Number.MIN_SAFE_INTEGER);
  tree.insert(Number.MAX_SAFE_INTEGER);
  assert.deepEqual(tree.values(), [Number.MIN_SAFE_INTEGER, Number.MAX_SAFE_INTEGER]);
});

test('property regression: 20 seeded insertion orders, 160 keys each', () => {
  for (const t of [2, 3, 5, 8]) {
    for (let seed = 1; seed <= 20; seed++) {
      const tree = new BTree(t);
      let s = seed;
      const next = () => { s = (s * 1664525 + 1013904223) >>> 0; return s; };
      const expected = new Set();
      for (let i = 0; i < 160; i++) {
        const k = (next() % 500) - 200;
        assert.equal(tree.insert(k), !expected.has(k));
        expected.add(k);
        if (i % 10 === 0) tree.validate();
      }
      const sorted = [...expected].sort((a,b) => a-b);
      assert.deepEqual(tree.values(), sorted);
      assert.equal(tree.validate().keys, expected.size);
      for (let k = -210; k < 310; k += 9) assert.equal(tree.search(k).found, expected.has(k));
    }
  }
});

test('structural validator catches impossible child count and key range', () => {
  const tree = makeExampleTree();
  tree.root.children.pop();
  assert.throws(() => tree.validate(), /child count mismatch/);
  const tree2 = makeExampleTree();
  tree2.root.keys[0] = Number.MIN_SAFE_INTEGER;
  assert.throws(() => tree2.validate(), /key ordering\/range error/);
});
