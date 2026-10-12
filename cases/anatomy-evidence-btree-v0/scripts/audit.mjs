import { readFileSync } from 'node:fs';
import { BTree, EXAMPLE_KEYS } from '../src/btree.mjs';
import { checkEvidence } from '../src/evidence.mjs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const script = readFileSync(new URL('../src/app.mjs', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
const assertions = [
  ['HTML lang', /lang="zh-CN"/.test(html)],
  ['search button', /id="search-btn"/.test(html)],
  ['keyboard instruction', /ArrowRight/.test(script) && /ArrowLeft/.test(script)],
  ['live region', /aria-live="polite"/.test(html)],
  ['reduced motion', /prefers-reduced-motion/.test(css)],
  ['horizontal local scroll', /overflow-x:\s*auto/.test(css)],
  ['accessibility label', /aria-label="B-tree/.test(html)],
  ['model displayed limitations', /演示假设/.test(html)],
  ['external dependency free', !/https:\/\/.*\.(?:js|css)["']/.test(html)],
];
const tree = new BTree(2);
for (const k of EXAMPLE_KEYS) tree.insert(k);
const structural = tree.validate();
if (structural.height < 2) throw new Error('fixture must exercise a multi-level B-tree');
if (checkEvidence().ok !== true) throw new Error('evidence check failed');
for (const [label, passed] of assertions) {
  if (!passed) throw new Error(`STATIC_AUDIT_FAIL ${label}`);
  console.log(`PASS ${label}`);
}
console.log(JSON.stringify({ gate: 'SEMANTIC_AND_STATIC_PASS', structural, assertions: assertions.length, scope: 'No browser screenshot or Anatomy geometry audit executed' }));
