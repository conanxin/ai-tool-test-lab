const { add } = require('./calc');

if (add(1, 2) !== 3) {
  console.error('FAIL: add(1, 2) should be 3, got:', add(1, 2));
  process.exit(1);
}

console.log('PASS');
