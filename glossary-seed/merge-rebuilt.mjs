// Merge per-category rebuilt JSON files into one rebuilt-glossary.json that
// can be POSTed to /functions/upsertGlossaryTerm or fetched by seedGlossary.
//
// Usage:  node glossary-seed/merge-rebuilt.mjs
// Output: glossary-seed/rebuilt-glossary.json (top-level array, one entry per term)
//
// No external deps — Node 20+ only.

import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const rebuiltDir = join(here, 'rebuilt');
const outFile = join(here, 'rebuilt-glossary.json');

const files = readdirSync(rebuiltDir).filter(f => f.endsWith('.json')).sort();
const all = [];
const seen = new Set();
const counts = {};

for (const f of files) {
  const fp = join(rebuiltDir, f);
  const arr = JSON.parse(readFileSync(fp, 'utf8'));
  if (!Array.isArray(arr)) {
    console.error(`SKIP ${f}: not a JSON array`);
    continue;
  }
  let added = 0, dupes = 0;
  for (const item of arr) {
    if (!item.slug) {
      console.error(`SKIP record in ${f}: no slug`);
      continue;
    }
    if (seen.has(item.slug)) {
      dupes++;
      continue;
    }
    seen.add(item.slug);
    all.push(item);
    added++;
  }
  counts[f] = { added, dupes };
}

writeFileSync(outFile, JSON.stringify(all, null, 2), 'utf8');

console.log(`Merged ${files.length} category files into ${outFile}`);
console.log(`Total unique slugs: ${all.length}`);
for (const [f, c] of Object.entries(counts)) {
  console.log(`  ${f}: +${c.added} (${c.dupes} dupes)`);
}
