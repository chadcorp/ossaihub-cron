// Probe v2 — extra auth shapes
const { DISCOVERY_SECRET, DISCOVERY_ENDPOINT, API_KEY } = process.env;
if (!DISCOVERY_ENDPOINT) throw new Error('Missing DISCOVERY_ENDPOINT');

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36';
const BASE_BODY = { category: 'llms-foundation', maxPerCategory: 1, autoApprove: false };

const variants = [
  { name: 'E: API_KEY header = DISCOVERY_SECRET value',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA, 'API_KEY': DISCOVERY_SECRET },
    body:    BASE_BODY },
  { name: 'F: x-api-key header = DISCOVERY_SECRET',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA, 'x-api-key': DISCOVERY_SECRET },
    body:    BASE_BODY },
  { name: 'G: Authorization Bearer DISCOVERY_SECRET',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA, 'Authorization': `Bearer ${DISCOVERY_SECRET}` },
    body:    BASE_BODY },
  { name: 'H: Authorization Bearer TOOLS_UPSERT_API_KEY',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA, 'Authorization': `Bearer ${API_KEY}` },
    body:    BASE_BODY },
  { name: 'I: GET with API_KEY (smoke: does function exist?)',
    method: 'GET',
    headers: { 'User-Agent': UA, 'API_KEY': API_KEY } },
  { name: 'J: no auth at all',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA },
    body:    BASE_BODY },
];

for (const v of variants) {
  let r, text;
  try {
    const opts = { method: v.method || 'POST', headers: v.headers };
    if (v.body) opts.body = JSON.stringify(v.body);
    r = await fetch(DISCOVERY_ENDPOINT, opts);
    text = await r.text();
  } catch (e) {
    console.log(`\n=== ${v.name} ===\nEXCEPTION ${e.message}`);
    continue;
  }
  console.log(`\n=== ${v.name} ===`);
  console.log(`HTTP ${r.status}`);
  console.log(`Headers: ${JSON.stringify(Object.fromEntries(r.headers.entries()))}`);
  console.log(text.slice(0, 400));
  await new Promise((res) => setTimeout(res, 3000));
}
