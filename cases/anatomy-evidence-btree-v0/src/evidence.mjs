/** Source identifiers and epistemic labels for the interactive explanation. */
export const EVIDENCE = Object.freeze({
  title: 'B-tree 搜索：有序多路树的交互式档案柜',
  assertion: '每个节点保存有序键；查找在节点中选择键或一个子区间，所有叶处于同一层。',
  claims: Object.freeze([
    { id: 'BT-01', statement: 'B-tree 是有序且保持平衡的多路搜索树。', status: 'SOURCE_BACKED', sourceId: 'NIST-BTREE' },
    { id: 'BT-02', statement: '查找命中节点键时结束，否则沿所属子区间继续，或在叶节点报告未命中。', status: 'SOURCE_BACKED', sourceId: 'OPEN-DSA' },
    { id: 'BT-03', statement: '本演示使用 minimum degree t=2，且不实现删除、磁盘页、并发、B+ 叶链。', status: 'MODEL_ASSUMPTION', sourceId: null },
    { id: 'BT-04', statement: '档案柜造型与动画只是机械隐喻，不是数据库硬件的实物结构。', status: 'INTERPRETATION', sourceId: null }
  ]),
  sources: Object.freeze([
    { id: 'NIST-BTREE', title: 'NIST Dictionary of Algorithms and Data Structures: B-tree', url: 'https://xlinux.nist.gov/dads/HTML/btree.html' },
    { id: 'OPEN-DSA', title: 'OpenDSA: B-Trees', url: 'https://opendsa-server.cs.vt.edu/ODSA/Books/pubbook/odsa-all/fall-2019/Public_Instance/html/BTree.html' }
  ])
});

export function checkEvidence(evidence = EVIDENCE) {
  const sourceIds = new Set(evidence.sources.map(x => x.id));
  const validStatuses = new Set(['SOURCE_BACKED', 'MODEL_ASSUMPTION', 'INTERPRETATION', 'UNVERIFIED']);
  if (!evidence.assertion || !evidence.title) throw new Error('missing claim or title');
  if (sourceIds.size !== evidence.sources.length) throw new Error('duplicate source ID');
  for (const source of evidence.sources) {
    if (!/^https:\/\//.test(source.url) || !source.title) throw new Error(`source must be an HTTPS URL with title: ${source.id}`);
  }
  for (const claim of evidence.claims) {
    if (!validStatuses.has(claim.status)) throw new Error(`invalid evidence status: ${claim.id}`);
    if (claim.status === 'SOURCE_BACKED' && !sourceIds.has(claim.sourceId)) throw new Error(`unbacked source claim: ${claim.id}`);
    if (claim.sourceId !== null && !sourceIds.has(claim.sourceId)) throw new Error(`unknown source ID: ${claim.id}`);
  }
  return { ok: true, claims: evidence.claims.length, sources: sourceIds.size };
}
