// Direct test of completeDistillation with our SKILL.md as the LLM response.
// We do NOT connect to Hub. We do NOT publish. We do NOT use --loop.
// We just exercise the distillation function and capture the result.
const path = require('path');
const fs = require('fs');

process.chdir('/mnt/d/AI/ai-tool-test-lab');

const responsePath = path.resolve('cases/evomap-evolver-openclaw-v0/phase3-skill-distillation/inputs/skill-as-llm-response.md');
if (!fs.existsSync(responsePath)) {
  console.error('Missing response file: ' + responsePath);
  process.exit(2);
}

const responseText = fs.readFileSync(responsePath, 'utf8');
console.log('[client] response file size: ' + responseText.length + ' chars');

try {
  const skillDistiller = require('/home/conanxin/.local/lib/node_modules/@evomap/evolver/src/gep/skillDistiller.js');
  console.log('[client] skillDistiller exports: ' + Object.keys(skillDistiller).join(', '));
  if (typeof skillDistiller.completeDistillation !== 'function') {
    console.error('[client] completeDistillation is not a function');
    process.exit(2);
  }
  const result = skillDistiller.completeDistillation(responseText);
  console.log('[client] result:');
  console.log(JSON.stringify(result, null, 2));
  process.exit(result && result.ok ? 0 : 3);
} catch (e) {
  console.error('[client] error: ' + (e.stack || e.message || e));
  process.exit(2);
}
