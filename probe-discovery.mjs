// Temp probe — DO NOT keep. Determines which auth pattern Base44 accepts now.
const { DISCOVERY_SECRET, DISCOVERY_ENDPOINT, API_KEY } = process.env;
if (!DISCOVERY_ENDPOINT) throw new Error('Missing DISCOVERY_ENDPOINT');

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36';
const BASE_BODY = { category: 'llms-foundation', maxPerCategory: 1, autoApprove: false };

const variants = [
  { name: 'A: body.secret only (current prod pattern)',
    headers: { 'Content-Type': 'application/json' },
    body:    { ...BASE_BODY, secret: DISCOVERY_SECRET } },
  { name: 'B: body.secret + browser UA',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA },
    body:    { ...BASE_BODY, secret: DISCOVERY_SECRET } },
  { name: 'C: API_KEY header only (enrichBacklog pattern)',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA, 'API_KEY': API_KEY },
    body:    BASE_BODY },
  { name: 'D: API_KEY header + body.secret (belt and braces)',
    headers: { 'Content-Type': 'application/json', 'User-Agent': UA, 'API_KEY': API_KEY },
    body:    { ...BASE_BODY, secret: DISCOVERY_SECRET } },
];

for (const v of variants) {
  let r, text;
  try {
    r = await fetch(DISCOVERY_ENDPOINT, { method: 'POST', headers: v.headers, body: JSON.stringify(v.body) });
    text = await r.text();
  } catch (e) {
    console.log(`\n=== ${v.name} ===\nEXCEPTION ${e.message}`);
    continue;
  }
  console.log(`\n=== ${v.name} ===`);
  console.log(`HTTP ${r.status}`);
  console.log(text.slice(0, 500));
  await new Promise((res) => setTimeout(res, 3000));
}
