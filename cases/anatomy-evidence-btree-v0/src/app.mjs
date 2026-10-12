import { makeExampleTree } from './btree.mjs';

const svg = document.querySelector('#btree-svg');
const query = document.querySelector('#query-key');
const stateText = document.querySelector('#trace-text');
const stateCount = document.querySelector('#trace-count');
const nextBtn = document.querySelector('#next-btn');
const prevBtn = document.querySelector('#prev-btn');
const resetBtn = document.querySelector('#reset-btn');
const nodeCount = document.querySelector('#node-count');
const keyCount = document.querySelector('#key-count');

let tree = makeExampleTree();
let trace = null;
let stepIndex = -1;

// Layout uses actual in-memory B-tree nodes. There is no hard-coded lookup path.
function cardWidth(node) { return Math.max(112, 66 + 44 * node.keys.length); }
function subtreeWidth(node) {
  const own = cardWidth(node) + 12;
  if (node.leaf) return own;
  return Math.max(own, node.children.reduce((sum, child) => sum + subtreeWidth(child), 0) + (node.children.length - 1) * 22);
}

function positions() {
  const root = tree.root;
  const total = subtreeWidth(root);
  const layout = new Map();
  const walk = (node, left, depth) => {
    const span = subtreeWidth(node);
    const x = left + span / 2;
    layout.set(node.id, { x, y: 68 + depth * 154, width: cardWidth(node), node });
    if (!node.leaf) {
      const sum = node.children.reduce((v, child) => v + subtreeWidth(child), 0) + (node.children.length - 1) * 22;
      let at = left + (span - sum) / 2;
      for (const child of node.children) {
        walk(child, at, depth + 1);
        at += subtreeWidth(child) + 22;
      }
    }
  };
  walk(root, 45, 0);
  return { layout, width: Math.max(760, total + 90), height: (tree.validate().height + 1) * 154 + 85 };
}

function draw() {
  const { layout, width, height } = positions();
  const active = trace && stepIndex >= 0 ? trace.steps[stepIndex] : null;
  const visited = new Set(trace ? trace.steps.slice(0, stepIndex + 1).filter(s=>s.kind === 'visit').map(s=>s.nodeId) : []);
  const nodes = [...layout.values()];
  const isFound = active?.kind === 'found';
  const links = [];
  for (const from of nodes) {
    const parent = from.node;
    if (parent.leaf) continue;
    for (let i = 0; i < parent.children.length; i++) {
      const child = layout.get(parent.children[i].id);
      const route = active?.kind === 'descend' && active.nodeId === parent.id && active.childId === child.node.id;
      const x1 = from.x + ((i + .5) / parent.children.length - .5) * (from.width - 44);
      links.push(`<path d="M ${x1} ${from.y + 50} C ${x1} ${from.y+98}, ${child.x} ${child.y - 58}, ${child.x} ${child.y - 12}" fill="none" stroke="${route ? '#d68c51' : '#9eaaa2'}" stroke-width="${route ? 5 : 2.7}" stroke-linecap="round" />`);
      links.push(`<circle cx="${x1}" cy="${from.y+50}" r="4" fill="${route ? '#d68c51' : '#899b92'}" />`);
    }
  }
  const cards = nodes.map(({x, y, width:w, node}) => {
    const current = active?.nodeId === node.id;
    const outline = current ? (isFound ? '#51995e' : '#227a7d') : (visited.has(node.id) ? '#76a2a3' : '#7c8b84');
    const fill = current ? (isFound ? '#e5f4e0' : '#dbefec') : '#e9ece6';
    const left = x - w/2;
    const keyCards = node.keys.map((k,i) => {
      const target = current && active?.kind==='found' && active.index===i;
      return `<g><rect x="${left+22+i*44}" y="${y+10}" width="40" height="30" rx="3" fill="${target ? '#9fd5a6' : '#fffdf6'}" stroke="${target ? '#398f56' : '#a9aaa1'}" stroke-width="1"/><text x="${left+42+i*44}" y="${y+30}" text-anchor="middle" font-family="ui-monospace,monospace" font-size="13" font-weight="700" fill="#304349">${k}</text></g>`;
    }).join('');
    return `<g aria-label="节点 ${node.id}，键 ${node.keys.join(', ')}"><title>Node ${node.id}: [${node.keys.join(', ')}]</title>` +
      `<rect x="${left+4}" y="${y+5}" width="${w}" height="47" rx="7" fill="#aab4ac" opacity=".44"/>` +
      `<path d="M${left+7} ${y-10} L${left+w+6} ${y-10} L${left+w} ${y-3} L${left} ${y-3} Z" fill="#f8f8ee" stroke="#98a49c"/>` +
      `<rect x="${left}" y="${y-3}" width="${w}" height="53" rx="5" fill="${fill}" stroke="${outline}" stroke-width="${current ? 3 : 1.6}"/>` +
      `<path d="M${left+8} ${y+42} H${left+w-8}" stroke="#acb7ac" stroke-width="1"/>` +
      `<circle cx="${left+9}" cy="${y+7}" r="2.5" fill="#c39a53"/><circle cx="${left+w-9}" cy="${y+7}" r="2.5" fill="#c39a53"/>` +
      `<text x="${x}" y="${y-21}" font-family="ui-monospace,monospace" font-size="11" text-anchor="middle" fill="#6b7b77">${node.id} · ${node.leaf ? 'LEAF' : 'INDEX'}</text>` + keyCards + `</g>`;
  }).join('');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('aria-label', `B-tree 具有 ${tree.size} 个键、${nodes.length} 个节点、深度 ${tree.validate().height}；${active ? stepDescription(active) : '当前未检索'}`);
  svg.innerHTML = `<defs><pattern id="grain" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="3" cy="4" r=".45" fill="#7e9386" opacity=".23"/></pattern></defs><rect x="0" y="0" width="${width}" height="${height}" fill="url(#grain)" />` + links.join('') + cards;
  nodeCount.textContent = String(nodes.length);
  keyCount.textContent = String(tree.size);
}

function stepDescription(step) {
  switch(step.kind) {
    case 'visit': return `检查节点 ${step.nodeId}：[${step.keys.join('，') || '空'}]。第 ${step.index+1} 个键位置决定下一步。`;
    case 'descend': return `目标不等于当前节点任何键：沿第 ${step.childIndex+1} 条指针前往 ${step.childId}。`;
    case 'found': return `命中！在节点 ${step.nodeId} 的第 ${step.index+1} 个键位找到 ${step.key}。`;
    case 'missing': return `未命中：已到叶节点 ${step.nodeId}，未发现键 ${step.key}。`;
    default: return '未定义的查找事件';
  }
}

function refresh() {
  const step = trace && stepIndex >= 0 ? trace.steps[stepIndex] : null;
  stateCount.textContent = trace ? `步骤 ${stepIndex + 1} / ${trace.steps.length}` : '准备就绪';
  stateText.textContent = step ? stepDescription(step) : '选择一个键值并检索。青色标出当前正在检查的节点，橙色表示下一条分支。';
  prevBtn.disabled = !trace || stepIndex <= 0;
  nextBtn.disabled = !trace || stepIndex >= trace.steps.length - 1;
  draw();
}

function getInputKey() {
  const value = Number(query.value);
  if (!query.value.trim() || !Number.isSafeInteger(value) || value < -999 || value > 999) {
    throw new Error('请输入 -999 至 999 的整数。');
  }
  return value;
}

function searchFor(key) {
  trace = tree.search(key);
  stepIndex = 0;
  refresh();
}

document.querySelector('#query-form').addEventListener('submit', event => {
  event.preventDefault();
  try { searchFor(getInputKey()); }
  catch(error) { stateText.textContent = error.message; }
});

document.querySelector('#insert-btn').addEventListener('click', () => {
  try {
    const key = getInputKey();
    const inserted = tree.insert(key);
    tree.validate();
    trace = null;
    stepIndex = -1;
    refresh();
    stateText.textContent = inserted ? `已插入 ${key}。如节点已满，参考 B-tree 实现自动拆分。现在可以查找它。` : `键 ${key} 已存在，未重复插入。`;
  } catch(error) { stateText.textContent = error.message; }
});

nextBtn.addEventListener('click', () => { if (trace && stepIndex < trace.steps.length - 1) { stepIndex++; refresh(); } });
prevBtn.addEventListener('click', () => { if (trace && stepIndex > 0) { stepIndex--; refresh(); } });
resetBtn.addEventListener('click', () => { tree = makeExampleTree(); query.value = '55'; trace = null; stepIndex = -1; refresh(); });

for (const b of document.querySelectorAll('[data-example]')) b.addEventListener('click', () => { query.value = b.dataset.example; searchFor(Number(b.dataset.example)); });
window.addEventListener('keydown', event => {
  if (event.target instanceof HTMLInputElement) return;
  if (event.key === 'ArrowRight' && !nextBtn.disabled) { event.preventDefault(); nextBtn.click(); }
  if (event.key === 'ArrowLeft' && !prevBtn.disabled) { event.preventDefault(); prevBtn.click(); }
});
refresh();
