// Module selection only; no browser launch or credential access here.
const path = require('path');
const fs = require('fs');
const configured = process.env.COLLAR_PLAYWRIGHT_MODULE;
if (configured) {
  module.exports = require(configured);
} else {
  const candidates = [
    path.resolve(__dirname, '../.runtime/browser/node_modules/playwright'),
    '/Users/gok/codex/tools/itopya-builder/node_modules/playwright',
  ];
  const found = candidates.find(p => fs.existsSync(path.join(p, 'package.json')));
  module.exports = found ? require(found) : require('playwright');
}
