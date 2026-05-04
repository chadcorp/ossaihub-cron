// Diagnostic probe — slow, with delays, to avoid tripping Cloudflare rate-limit.
// Tests: does API_KEY header work, what's the response size, does ?limit work?
const KEY = process.env.BASE44_API_KEY;
if (!KEY) throw new Error('BASE44_API_KEY missing');
const BASE = 'https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/toolsApiJson';
const UA = 'Mozilla/5.0 (compatible; ossaihub-cron-probe/1.0)';

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function probe(label, url, headers, gap = 5000) {
  console.log(`\n=== ${label} ===`);
  console.log(`URL: ${url}`);
  console.log(`Headers: ${JSON.stringify(Object.keys(headers))}`);
  try {
    const r = await fetch(url, { headers });
    console.log(`HTTP ${r.status}`);
    const ct = r.headers.get('content-type') || '';
    console.log(`content-type: ${ct}`);
    for (const h of ['link', 'x-total-count', 'x-total', 'total-count', 'x-page-count', 'cf-ray', 'cf-cache-status']) {
      const v = r.headers.get(h);
      if (v) console.log(`${h}: ${v}`);
    }
    const body = await r.text();
    if (!ct.includes('json') || r.status >= 400) {
      console.log(`body (first 200): ${body.slice(0, 200)}`);
      await sleep(gap);
      return null;
    }
    const j = JSON.parse(body);
    if (Array.isArray(j)) {
      console.log(`shape: bare array, length=${j.length}`);
      if (j.length) console.log(`first item keys: ${Object.keys(j[0]).slice(0,15).join(', ')}`);
    } else {
      console.log(`shape: object, keys=[${Object.keys(j).join(', ')}]`);
      for (const k of Object.keys(j)) {
        const v = j[k];
        if (Array.isArray(v)) {
          console.log(`  ${k}: array length=${v.length}`);
          if (v.length && typeof v[0] === 'object') console.log(`    first item keys: ${Object.keys(v[0]).slice(0,15).join(', ')}`);
        } else if (typeof v === 'object' && v !== null) {
          console.log(`  ${k}: object keys=[${Object.keys(v).join(', ')}]`);
        } else {
          console.log(`  ${k}: ${typeof v} = ${String(v).slice(0, 100)}`);
        }
      }
    }
    await sleep(gap);
    return j;
  } catch (e) {
    console.log(`ERROR: ${e.message}`);
    await sleep(gap);
    return null;
  }
}

const baseHeaders = { Accept: 'application/json', 'User-Agent': UA, API_KEY: KEY };

// Probe 1: bare URL — see if it works at all today.
const a = await probe('A: bare URL', BASE, baseHeaders);

// Probe 2: ?limit=10000 — most common Base44 pagination pattern
await probe('B: ?limit=10000', `${BASE}?limit=10000`, baseHeaders);

// Probe 3: ?page=2 — see if there's a page 2 with different data
await probe('C: ?page=2', `${BASE}?page=2`, baseHeaders);

// Probe 4: ?page=1&limit=200 — explicit
await probe('D: ?page=1&limit=200', `${BASE}?page=1&limit=200`, baseHeaders);

// Probe 5: ?_limit=10000 (some platforms use underscore)
await probe('E: ?_limit=10000', `${BASE}?_limit=10000`, baseHeaders);

// Probe 6: scan ?page=1..5 for total coverage if A shows pagination
console.log('\n=== summary ===');
if (a && Array.isArray(a)) console.log(`A bare returned ${a.length} items`);
else if (a && Array.isArray(a.data)) console.log(`A bare returned ${a.data.length} items in .data; total field: ${a.total ?? a.count ?? a.totalCount ?? '(none)'}`);
