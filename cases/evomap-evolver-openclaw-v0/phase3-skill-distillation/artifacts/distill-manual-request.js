const fs = require('fs');
const path = require('path');
const skillDistiller = require('/home/conanxin/.local/lib/node_modules/@evomap/evolver/src/gep/skillDistiller.js');

// Build a minimal manual distillation request that satisfies the gating logic
const manualRequest = {
  type: 'skill_distillation',
  source: 'manual_phase3a',
  created_at: new Date().toISOString(),
  hint: 'openclaw-tool-use-discipline',
  data: {
    successCapsules: [],
    allCapsules: [],
    events: [],
    graphEntries: [],
    grouped: { by_gene: {}, by_signal: { 'tool_bypass:exec-on-grep': 1, 'session_context:openclaw': 1 } },
    dataHash: 'manual_phase3a'
  }
};

const requestPath = skillDistiller.distillRequestPath();
fs.writeFileSync(requestPath, JSON.stringify(manualRequest, null, 2));
console.log('Wrote manual request to:', requestPath);
console.log('---');
console.log(fs.readFileSync(requestPath, 'utf8'));

// Now try completeDistillation
const responsePath = path.resolve('cases/evomap-evolver-openclaw-v0/phase3-skill-distillation/inputs/skill-as-llm-response.md');
const responseText = fs.readFileSync(responsePath, 'utf8');
console.log('---');
console.log('Calling completeDistillation with manual request...');
const result = skillDistiller.completeDistillation(responseText);
console.log(JSON.stringify(result, null, 2));
process.exit(result && result.ok ? 0 : 3);
