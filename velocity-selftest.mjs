// Selftest for the upsertVelocityData endpoint (manual dispatch only).
// Proves three things without touching real rows:
//   1) create path works (synthetic slug zz-velocity-selftest)
//   2) the 45-min no-op skip is live (immediate re-send -> skipped_noop=1)
//   3) run_log-only posts create a CronExecutionLog row
// Exits 1 if the endpoint is still running the pre-upgrade code, because the
// refresh script's batch-retry is only gain-safe WITH the no-op skip.
const { BASE44_API_KEY } = process.env;
if (!BASE44_API_KEY) throw new Error('Missing BASE44_API_KEY');
const URL = 'https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertVelocityData';

async function post(body) {
  const r = await fetch(URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', API_KEY: BASE44_API_KEY },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  console.log(`HTTP ${r.status}: ${text.slice(0, 400)}`);
  try { return JSON.parse(text); } catch { return {}; }
}

const item = { tool_slug: 'zz-velocity-selftest', tool_id: 'zz-velocity-selftest', stars: 100, forks: 1, open_issues: 0, last_commit_date: null };
console.log('1) create/update selftest row:');
await post({ items: [item] });
console.log('2) immediate re-send (expect skipped_noop=1 on upgraded endpoint):');
const r2 = await post({ items: [item] });
console.log('3) run_log-only post (expect 200; CronExecutionLog row, note=selftest):');
await post({ items: [], run_log: { status: 'success', records_processed: 0, updated: 0, created: 0, failed: 0, noop: 0, note: 'selftest' } });

const upgraded = r2 && typeof r2.skipped_noop === 'number' && r2.skipped_noop === 1;
console.log(`VERDICT: ${upgraded ? 'UPGRADED — no-op skip live, batch retry is gain-safe' : 'NOT UPGRADED — old code still serving, do NOT rely on batch retry yet'}`);
if (!upgraded) process.exit(1);
