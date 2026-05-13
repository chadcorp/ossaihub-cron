// Fires every Sunday to generate the current-week digest on ossaihub.com.
// Idempotent — re-running the same week updates the existing record.

const { API_KEY, DIGEST_ENDPOINT } = process.env;
if (!API_KEY || !DIGEST_ENDPOINT) {
  throw new Error('Missing API_KEY or DIGEST_ENDPOINT env vars.');
}

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36';

const start = Date.now();

const r = await fetch(DIGEST_ENDPOINT, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': UA,
    'API_KEY': API_KEY,
  },
  body: JSON.stringify({ useLLM: true }),
});

const text = await r.text();
let parsed;
try { parsed = JSON.parse(text); } catch { parsed = { raw: text.slice(0, 500) }; }

const durSec = Math.round((Date.now() - start) / 1000);

console.log(`=== Weekly digest run in ${durSec}s ===`);
console.log(`HTTP ${r.status}`);
console.log(JSON.stringify(parsed, null, 2));

if (!r.ok) process.exit(1);
