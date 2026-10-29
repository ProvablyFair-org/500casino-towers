// Layer 2 and layer 3: the captured client's own arithmetic, evaluated in JavaScript.
//
//   layer 2  client 3-decimal ladder label  Math.floor(1e3 * Math.pow(step, row)) / 1e3   (live 1828.89aa27f6.js)
//            archived variant               Math.floor(step ** row * 1e3) / 1e3            (archived towers.55a86d17.js)
//   layer 3  client 2-decimal tile label    Math.floor(100 * label3) / 100                   (live multiplierText)
//
// step is the Number returned by roundMultiplier (see data/payout-parameters.json). These are client display
// values; they are not a statement about how the server settles.
//
// Usage: node analysis/client_ladders.mjs --out <dir>      writes <dir>/client-ladders.json
// Reads only data/payout-parameters.json. Writes nothing else. Exit 1 on any internal inconsistency.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outIdx = process.argv.indexOf('--out');
if (outIdx < 0 || !process.argv[outIdx + 1]) { console.error('usage: node analysis/client_ladders.mjs --out <dir>'); process.exit(2); }
const OUT = path.resolve(process.argv[outIdx + 1]);
const params = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/payout-parameters.json'), 'utf8')).towers;

const rows = [];
let problems = 0;
for (const [difficulty, d] of Object.entries(params.difficulties)) {
  const step = Number(d.client_step_number);
  const binaryProduct = (d.choices / (d.choices - d.bombs)) * (1 - Number(params.house_edge));
  for (let row = 1; row <= params.rows; row++) {
    const label3 = Math.floor(1e3 * Math.pow(step, row)) / 1e3;
    const label3Archived = Math.floor(step ** row * 1e3) / 1e3;
    const label2 = Math.floor(100 * label3) / 100;
    const label3IfBinary = Math.floor(1e3 * Math.pow(binaryProduct, row)) / 1e3;
    if (label3 !== label3Archived) problems++;
    rows.push({
      difficulty, row,
      client_label_3dp: label3.toFixed(3),
      client_label_3dp_js_number: String(label3),
      archived_client_label_3dp: label3Archived.toFixed(3),
      client_tile_label_2dp: label2.toFixed(2),
      label_3dp_if_step_were_binary_product: label3IfBinary.toFixed(3),
    });
  }
}
fs.mkdirSync(OUT, { recursive: true });
const result = {
  layer: 'Captured client display arithmetic, evaluated by the JavaScript engine. Not a settlement observation.',
  formula_3dp: 'Math.floor(1e3*Math.pow(step,row))/1e3',
  formula_2dp: 'Math.floor(100*label3)/100',
  steps: Object.fromEntries(Object.entries(params.difficulties).map(([k, d]) => [k, String(Number(d.client_step_number))])),
  live_vs_archived_expression_mismatches: problems,
  rows,
};
fs.writeFileSync(path.join(OUT, 'client-ladders.json'), JSON.stringify(result, null, 1) + '\n');
console.log(`client ladders (node ${process.version}): ${rows.length} rows; live/archived expression mismatches: ${problems}`);
process.exit(problems === 0 ? 0 : 1);
