// Fires every Sunday to generate the current-week digest on ossaihub.com.
// Idempotent — re-running the same week updates the existing record.

const { DIGEST_SECRET, DIGEST_ENDPOINT } = process.env;
if (!DIGEST_SECRET || !DIGEST_ENDPOINT) {
  throw new Error('Missing DIGEST_SECRET or DIGEST_ENDPOINT env vars.');
}

const start = Date.now();

const r = await fetch(DIGEST_ENDPOINT, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ secret: DIGEST_SECRET, useLLM: true }),
});

const text = await r.text();
let parsed;
try { parsed = JSON.parse(text); } catch { parsed = { raw: text.slice(0, 500) }; }

const durSec = Math.round((Date.now() - start) / 1000);

console.log(`=== Weekly digest run in ${durSec}s ===`);
console.log(`HTTP ${r.status}`);
console.log(JSON.stringify(parsed, null, 2));

if (!r.ok) process.exit(1);
