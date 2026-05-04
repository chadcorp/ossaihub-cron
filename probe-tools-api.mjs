// Diagnostic probe: figure out how to fully load toolsApiJson now that Base44
// gated + paginated it. Prints response shape, keys, and totals for several
// query/header variants so we can pick the right one.
const KEY = process.env.BASE44_API_KEY;
if (!KEY) throw new Error('BASE44_API_KEY missing');
const BASE = 'https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/toolsApiJson';

async function probe(label, url, headers) {
  console.log(`\n=== ${label} ===`);
  console.log(`URL: ${url}`);
  console.log(`Headers: ${JSON.stringify(headers)}`);
  try {
    const r = await fetch(url, { headers });
    console.log(`HTTP ${r.status}`);
    const ct = r.headers.get('content-type') || '';
    console.log(`content-type: ${ct}`);
    const link = r.headers.get('link');
    if (link) console.log(`link header: ${link}`);
    const total = r.headers.get('x-total-count') || r.headers.get('x-total') || r.headers.get('total-count');
    if (total) console.log(`total header: ${total}`);
    const body = await r.text();
    if (!ct.includes('json')) {
      console.log(`body (first 200): ${body.slice(0, 200)}`);
      return;
    }
    const j = JSON.parse(body);
    if (Array.isArray(j)) {
      console.log(`shape: bare array, length=${j.length}`);
    } else {
      console.log(`shape: object, keys=[${Object.keys(j).join(', ')}]`);
      for (const k of Object.keys(j)) {
        const v = j[k];
        if (Array.isArray(v)) console.log(`  ${k}: array length=${v.length}`);
        else if (typeof v === 'object' && v !== null) console.log(`  ${k}: object keys=[${Object.keys(v).join(', ')}]`);
        else console.log(`  ${k}: ${typeof v} = ${String(v).slice(0, 80)}`);
      }
    }
  } catch (e) {
    console.log(`ERROR: ${e.message}`);
  }
}

await probe('A: bare URL, API_KEY header', BASE, { API_KEY: KEY });
await probe('B: ?limit=10000', `${BASE}?limit=10000`, { API_KEY: KEY });
await probe('C: ?per_page=1000', `${BASE}?per_page=1000`, { API_KEY: KEY });
await probe('D: ?page=2&limit=50', `${BASE}?page=2&limit=50`, { API_KEY: KEY });
await probe('E: ?offset=50', `${BASE}?offset=50`, { API_KEY: KEY });
await probe('F: lowercase api_key header', BASE, { api_key: KEY });
await probe('G: x-api-key header', BASE, { 'x-api-key': KEY });
await probe('H: Authorization Bearer', BASE, { Authorization: `Bearer ${KEY}` });
