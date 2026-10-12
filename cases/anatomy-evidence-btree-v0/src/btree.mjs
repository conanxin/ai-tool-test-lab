/** Deterministic B-tree with minimum degree t. No UI/framework dependencies. */
export class BTree {
  constructor(t = 2) {
    if (!Number.isSafeInteger(t) || t < 2 || t > 64) throw new RangeError('minimum degree t must be an integer from 2 to 64');
    this.t = t;
    this._nextId = 1;
    this.root = this._makeNode(true);
    this.size = 0;
  }

  _makeNode(leaf) {
    return { id: `n${this._nextId++}`, keys: [], children: [], leaf };
  }

  _key(value) {
    if (!Number.isSafeInteger(value)) throw new TypeError('keys must be safe integers');
    return value;
  }

  search(value) {
    const key = this._key(value);
    const steps = [];
    let node = this.root;
    let depth = 0;
    while (node) {
      let index = 0;
      while (index < node.keys.length && key > node.keys[index]) index++;
      steps.push({ kind: 'visit', nodeId: node.id, depth, index, keys: [...node.keys] });
      if (index < node.keys.length && key === node.keys[index]) {
        steps.push({ kind: 'found', nodeId: node.id, depth, index, key });
        return { found: true, key, nodeId: node.id, index, steps };
      }
      if (node.leaf) {
        steps.push({ kind: 'missing', nodeId: node.id, depth, index, key });
        return { found: false, key, nodeId: node.id, index, steps };
      }
      steps.push({ kind: 'descend', nodeId: node.id, childId: node.children[index].id, childIndex: index, depth });
      node = node.children[index];
      depth++;
    }
    throw new Error('invalid tree: search fell outside a node');
  }

  insert(value) {
    const key = this._key(value);
    if (this.search(key).found) return false;
    const max = 2 * this.t - 1;
    if (this.root.keys.length === max) {
      const oldRoot = this.root;
      const next = this._makeNode(false);
      next.children.push(oldRoot);
      this._splitChild(next, 0);
      this.root = next;
    }
    this._insertNonFull(this.root, key);
    this.size++;
    return true;
  }

  _splitChild(parent, index) {
    const t = this.t;
    const left = parent.children[index];
    if (left.keys.length !== 2 * t - 1) throw new Error('only a full node can split');
    const right = this._makeNode(left.leaf);
    const median = left.keys[t - 1];
    right.keys = left.keys.slice(t);
    left.keys = left.keys.slice(0, t - 1);
    if (!left.leaf) {
      right.children = left.children.slice(t);
      left.children = left.children.slice(0, t);
    }
    parent.keys.splice(index, 0, median);
    parent.children.splice(index + 1, 0, right);
  }

  _insertNonFull(node, key) {
    let i = node.keys.length - 1;
    if (node.leaf) {
      while (i >= 0 && key < node.keys[i]) i--;
      node.keys.splice(i + 1, 0, key);
      return;
    }
    while (i >= 0 && key < node.keys[i]) i--;
    i++;
    if (node.children[i].keys.length === 2 * this.t - 1) {
      this._splitChild(node, i);
      if (key > node.keys[i]) i++;
    }
    this._insertNonFull(node.children[i], key);
  }

  values() {
    const result = [];
    const visit = (node) => {
      for (let i = 0; i < node.keys.length; i++) {
        if (!node.leaf) visit(node.children[i]);
        result.push(node.keys[i]);
      }
      if (!node.leaf) visit(node.children[node.keys.length]);
    };
    visit(this.root);
    return result;
  }

  serialize() {
    const clone = (n) => ({ id: n.id, leaf: n.leaf, keys: [...n.keys], children: n.children.map(clone) });
    return { minimumDegree: this.t, size: this.size, root: clone(this.root) };
  }

  validate() {
    const ids = new Set();
    const leafDepths = new Set();
    let count = 0;
    const walk = (node, lower, upper, depth, root = false) => {
      if (ids.has(node.id)) throw new Error(`cycle or duplicate node ID: ${node.id}`);
      ids.add(node.id);
      if (node.keys.length > 2 * this.t - 1) throw new Error(`node too large: ${node.id}`);
      if (node.keys.length < (root ? (node.leaf ? 0 : 1) : this.t - 1)) throw new Error(`node too small: ${node.id}`);
      for (let i = 0; i < node.keys.length; i++) {
        const k = node.keys[i];
        if (!Number.isSafeInteger(k) || (lower !== null && k <= lower) || (upper !== null && k >= upper) || (i && k <= node.keys[i-1])) {
          throw new Error(`key ordering/range error: ${node.id}`);
        }
      }
      count += node.keys.length;
      if (node.leaf) {
        if (node.children.length) throw new Error(`leaf has children: ${node.id}`);
        leafDepths.add(depth);
      } else {
        if (node.children.length !== node.keys.length + 1) throw new Error(`child count mismatch: ${node.id}`);
        for (let i = 0; i <= node.keys.length; i++) {
          walk(node.children[i], i === 0 ? lower : node.keys[i - 1], i === node.keys.length ? upper : node.keys[i], depth + 1);
        }
      }
    };
    walk(this.root, null, null, 0, true);
    if (leafDepths.size !== 1) throw new Error('leaves are not at equal depth');
    if (count !== this.size) throw new Error(`size mismatch: stored ${this.size}, counted ${count}`);
    return { ok: true, nodes: ids.size, keys: count, height: [...leafDepths][0], minimumDegree: this.t };
  }
}

export const EXAMPLE_KEYS = Object.freeze([40, 10, 20, 70, 50, 30, 60, 80, 90, 15, 55, 35, 45, 65, 75, 85, 5, 25]);
export function makeExampleTree(t = 2) {
  const tree = new BTree(t);
  for (const value of EXAMPLE_KEYS) tree.insert(value);
  tree.validate();
  return tree;
}
