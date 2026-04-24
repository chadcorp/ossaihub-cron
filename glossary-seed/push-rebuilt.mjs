// Pushes the merged rebuilt-glossary.json to Base44 via /functions/upsertGlossaryTerm.
// Chunks 50 records per request, 500ms inter-batch delay, retries on 5xx.
//
// Usage:
//   API_KEY=$TOOLS_UPSERT_API_KEY node glossary-seed/push-rebuilt.mjs
//   API_KEY=... CHUNK=25 DRY_RUN=true node glossary-seed/push-rebuilt.mjs
//
// Idempotent on the Base44 side — same slug runs again just update fields.

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const inFile = join(here, 'rebuilt-glossary.json');

const {
  API_KEY,
  UPSERT_URL = 'https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertGlossaryTerm',
  CHUNK = '50',
  INTER_BATCH_MS = '500',
  DRY_RUN = 'false',
  ONLY_SLUGS = '',           // optional comma-separated subset
} = process.env;

if (!API_KEY) throw new Error('API_KEY env var required');

const chunkSize = Number(CHUNK);
const interBatchMs = Number(INTER_BATCH_MS);
const dryRun = String(DRY_RUN).toLowerCase() === 'true';
const onlySlugs = ONLY_SLUGS ? new Set(ONLY_SLUGS.split(',').map(s => s.trim())) : null;

const all = JSON.parse(readFileSync(inFile, 'utf8'));
const items = onlySlugs ? all.filter(x => onlySlugs.has(x.slug)) : all;

console.log(`Mode: ${dryRun ? 'DRY RUN' : 'LIVE'}`);
console.log(`Loaded ${all.length} terms; pushing ${items.length} (chunk=${chunkSize}, delay=${interBatchMs}ms)`);

async function postChunk(chunk, attempts = 5) {
  for (let i = 0; i < attempts; i++) {
    try {
      const r = await fetch(UPSERT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', API_KEY },
        body: JSON.stringify({ items: chunk }),
      });
      if (r.ok) return await r.json();
      if (r.status >= 500 && r.status < 600) {
        const wait = 1000 * Math.pow(2, i);
        console.log(`  retry ${i + 1}/${attempts} after ${wait}ms (${r.status})`);
        await new Promise(res => setTimeout(res, wait));
        continue;
      }
      throw new Error(`${r.status} ${(await r.text()).slice(0, 300)}`);
    } catch (e) {
      if (i === attempts - 1) throw e;
      const wait = 1000 * Math.pow(2, i);
      await new Promise(res => setTimeout(res, wait));
    }
  }
}

const totals = { sent: 0, updated: 0, created: 0, failed: 0, errors: [] };
const totalBatches = Math.ceil(items.length / chunkSize);

for (let i = 0; i < items.length; i += chunkSize) {
  const chunk = items.slice(i, i + chunkSize);
  const batchNum = i / chunkSize + 1;
  if (dryRun) {
    console.log(`[DRY] would post batch ${batchNum}/${totalBatches}: ${chunk.length} items (slugs: ${chunk.slice(0, 3).map(x => x.slug).join(', ')}...)`);
    totals.sent += chunk.length;
  } else {
    const res = await postChunk(chunk);
    totals.sent += chunk.length;
    totals.updated += res.rows_updated ?? 0;
    totals.created += res.rows_created ?? 0;
    totals.failed += res.rows_failed ?? 0;
    if (Array.isArray(res.errors)) totals.errors.push(...res.errors);
    console.log(`  batch ${batchNum}/${totalBatches}: sent=${chunk.length}, updated=${res.rows_updated ?? '?'}, created=${res.rows_created ?? 0}, failed=${res.rows_failed ?? 0}`);
  }
  if (i + chunkSize < items.length) {
    await new Promise(res => setTimeout(res, interBatchMs));
  }
}

console.log('\n--- TOTALS ---');
console.log(`sent:    ${totals.sent}`);
console.log(`updated: ${totals.updated}`);
console.log(`created: ${totals.created}`);
console.log(`failed:  ${totals.failed}`);
if (totals.errors.length) {
  console.log(`errors (first 10):`);
  for (const e of totals.errors.slice(0, 10)) console.log(`  - ${JSON.stringify(e)}`);
}
