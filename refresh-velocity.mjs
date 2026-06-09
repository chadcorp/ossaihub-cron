// Refreshes the GitHubVelocity entity for every OSS AI Hub tool.
//
// WHY THIS EXISTS (2026-06-09): the previous path — the Base44-native
// `syncGitHubVelocity` function — wrote velocity rows with per-record
// entity.update() calls and NO retry, capped at 200 tools/run. Base44's
// per-row write rate-limit let only ~50 of 200 land per run, and failed
// writes never advanced `synced_at`, so the most-stale tail starved: ~445
// rows froze for 2+ weeks (hermes-agent stuck 25 days), which in turn froze
// the public Weekly Digest headline ("Hermes Agent led the week with +5,352
// stars") for four straight weeks.
//
// This script mirrors refresh-stars.mjs: it computes nothing locally (gains
// are computed server-side by the `upsertVelocityData` function), and posts
// per-tool velocity rows in small paced batches with aggressive retry so we
// stay under the rate-limit ceiling. Every tool is attempted every run, so
// nothing starves. No external deps — Node 20+ only.

const { GH_READONLY_TOKEN, BASE44_API_KEY } = process.env;
if (!GH_READONLY_TOKEN || !BASE44_API_KEY) {
  throw new Error('Missing required env vars (GH_READONLY_TOKEN, BASE44_API_KEY).');
}

const APP_ID = '69a91ff6770c8ca0347ae03d';
const TOOLS_LIST_URL = `https://base44.app/api/apps/${APP_ID}/functions/toolsApiJson`;
const VELOCITY_UPSERT_URL = `https://base44.app/api/apps/${APP_ID}/functions/upsertVelocityData`;

// Coverage guard — fail the job loudly when GitHub dropout exceeds this
// fraction so /data-health goes red instead of reporting a fake-green.
const MAX_COVERAGE_LOSS = 0.15; // 15%
// Total-feed floor — refuse to proceed on a truncated tool list rather than
// poison velocity with a partial refresh.
const MIN_TOOLS_EXPECTED = 1500;

const TOOLS_PAGE_LIMIT = 100;
const TOOLS_PAGE_DELAY_MS = 1500;
const TOOLS_USER_AGENT = 'ossaihub-cron-refresh-velocity/1.0';

const parseRepo = (url) => {
  const m = url?.match(/github\.com\/([^\/]+)\/([^\/?#]+)/);
  return m ? { owner: m[1], name: m[2].replace(/\.git$/, '') } : null;
};
const normalizeUrl = (u) =>
  (u || '').toLowerCase().trim().replace(/\.git$/, '').replace(/\/$/, '');

// Base44's upsert endpoint rate-limits under sustained load. It often wraps
// the rate-limit response as HTTP 500 with body {error: "... 429"}. Detect
// that pattern and apply longer backoffs specifically for rate-limits.
async function fetchWithRetry(url, opts = {}, attempts = 10) {
  let lastBody = '';
  let lastStatus = 0;
  for (let i = 0; i < attempts; i++) {
    try {
      const r = await fetch(url, opts);
      if (r.ok) return r;
      lastStatus = r.status;
      if (r.status >= 500 && r.status < 600) {
        lastBody = (await r.text()).slice(0, 500);
        const isRateLimit = /429/.test(lastBody);
        const baseWait = isRateLimit ? 15000 : 1000;
        const wait = Math.min(120000, baseWait * Math.pow(1.7, i));
        console.log(
          `  retry ${i + 1}/${attempts} after ${wait}ms (${r.status}${isRateLimit ? ' rate-limit' : ''}) body=${lastBody.slice(0, 150)}`
        );
        await new Promise((res) => setTimeout(res, wait));
        continue;
      }
      throw new Error(`${r.status} ${(await r.text()).slice(0, 300)}`);
    } catch (e) {
      if (!lastStatus) lastStatus = -1;
      const wait = Math.min(30000, 1000 * Math.pow(2, i));
      await new Promise((res) => setTimeout(res, wait));
    }
  }
  throw new Error(`${lastStatus} on ${url} after ${attempts} retries. Last body: ${lastBody}`);
}

async function fetchPage(page) {
  const url = `${TOOLS_LIST_URL}?page=${page}&limit=${TOOLS_PAGE_LIMIT}`;
  const r = await fetchWithRetry(url, {
    headers: {
      Accept: 'application/json',
      'User-Agent': TOOLS_USER_AGENT,
      API_KEY: BASE44_API_KEY,
    },
  });
  const raw = await r.json();
  if (Array.isArray(raw)) return { items: raw, pagination: null };
  if (Array.isArray(raw?.data)) return { items: raw.data, pagination: raw.pagination || null };
  const preview = JSON.stringify(raw).slice(0, 300);
  throw new Error(`toolsApiJson page ${page} returned no array (auth/error): ${preview}`);
}

// Returns Map(normalizedUrl -> [{ slug, github_url }, ...]). One GitHub repo
// can back several tools, so velocity is written per-tool (keyed by slug).
async function listTools() {
  const all = [];
  let page = 1;
  let total = null;
  const MAX_PAGES = 200;
  while (page <= MAX_PAGES) {
    const { items, pagination } = await fetchPage(page);
    all.push(...items);
    if (pagination) {
      if (total === null && typeof pagination.total === 'number') total = pagination.total;
      console.log(`  page ${page}: +${items.length} (running ${all.length}${total !== null ? ` / ${total}` : ''})`);
      if (!pagination.hasMore) break;
    } else {
      console.log(`  legacy bare-array response: ${items.length} items`);
      break;
    }
    page += 1;
    await new Promise((res) => setTimeout(res, TOOLS_PAGE_DELAY_MS));
  }
  if (page > MAX_PAGES) {
    throw new Error(`toolsApiJson exceeded MAX_PAGES=${MAX_PAGES} — pagination loop is broken`);
  }
  if (total !== null && all.length < total) {
    throw new Error(`toolsApiJson pagination undercount: loaded ${all.length} but total reported ${total}. Refusing to proceed.`);
  }
  if (all.length < MIN_TOOLS_EXPECTED) {
    throw new Error(`toolsApiJson returned only ${all.length} tools (< MIN_TOOLS_EXPECTED=${MIN_TOOLS_EXPECTED}). Aborting.`);
  }
  console.log(`Loaded ${all.length} tools across ${page} page(s) from toolsApiJson`);
  const byUrl = new Map();
  for (const t of all) {
    if (!t.github_url || !t.slug) continue;
    const k = normalizeUrl(t.github_url);
    if (!byUrl.has(k)) byUrl.set(k, []);
    byUrl.get(k).push({ slug: t.slug, github_url: t.github_url });
  }
  return byUrl;
}

// One chunk of up to 100 repos. Retries the whole chunk on transient GitHub
// errors so partial-data responses don't silently drop repos. Each chunk entry
// is { owner, name, url, tools } and results carry `tools` through so stats can
// be fanned back out to every tool sharing the repo.
async function fetchStatsChunk(chunk, attempt = 0) {
  const MAX_ATTEMPTS = 5;
  const q = chunk
    .map(
      (r, idx) => `
      r${idx}: repository(owner: "${r.owner}", name: "${r.name}") {
        nameWithOwner
        stargazerCount forkCount pushedAt
        openIssues: issues(states: OPEN) { totalCount }
      }`
    )
    .join('\n');

  let json;
  try {
    const res = await fetch('https://api.github.com/graphql', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GH_READONLY_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'ossaihub-velocity-refresher',
      },
      body: JSON.stringify({ query: `{${q}}` }),
    });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      const retriable = res.status >= 500 || res.status === 403 || res.status === 429;
      if (retriable && attempt < MAX_ATTEMPTS - 1) {
        const wait = Math.min(60000, 3000 * Math.pow(2, attempt));
        console.log(`  GraphQL chunk HTTP ${res.status} (attempt ${attempt + 1}/${MAX_ATTEMPTS}) — retrying in ${wait}ms. Body: ${body.slice(0, 150)}`);
        await new Promise((r) => setTimeout(r, wait));
        return fetchStatsChunk(chunk, attempt + 1);
      }
      throw new Error(`GraphQL HTTP ${res.status}: ${body.slice(0, 300)}`);
    }
    json = await res.json();
  } catch (e) {
    if (attempt < MAX_ATTEMPTS - 1) {
      const wait = Math.min(60000, 3000 * Math.pow(2, attempt));
      console.log(`  GraphQL chunk fetch error (attempt ${attempt + 1}/${MAX_ATTEMPTS}) — retrying in ${wait}ms. Error: ${e.message.slice(0, 150)}`);
      await new Promise((r) => setTimeout(r, wait));
      return fetchStatsChunk(chunk, attempt + 1);
    }
    throw e;
  }

  const notFound = new Set();
  const otherErrors = [];
  if (Array.isArray(json.errors)) {
    for (const err of json.errors) {
      if (err.type === 'NOT_FOUND' && Array.isArray(err.path)) notFound.add(err.path[0]);
      else otherErrors.push(err);
    }
  }
  const hasTransient = otherErrors.some((e) => {
    const t = (e.type || '').toLowerCase();
    const msg = (e.message || '').toLowerCase();
    return t === 'rate_limited' || /rate.?limit|timeout|abuse|secondary|temporar/i.test(msg);
  });
  if (hasTransient && attempt < MAX_ATTEMPTS - 1) {
    const wait = Math.min(60000, 8000 * Math.pow(2, attempt));
    console.log(`  GraphQL chunk transient errors (attempt ${attempt + 1}/${MAX_ATTEMPTS}) — retrying full chunk in ${wait}ms.`);
    await new Promise((r) => setTimeout(r, wait));
    return fetchStatsChunk(chunk, attempt + 1);
  }
  if (otherErrors.length) {
    console.warn(`  GraphQL non-404 errors on chunk (after ${attempt + 1} attempts):`, otherErrors.slice(0, 3).map((e) => ({ type: e.type, message: e.message?.slice(0, 120) })));
  }

  const live = [];
  const dead = [];
  let skipped = 0;
  chunk.forEach((r, idx) => {
    const alias = `r${idx}`;
    const repo = json.data?.[alias];
    if (repo) {
      live.push({
        tools: r.tools,
        stars: repo.stargazerCount ?? 0,
        forks: repo.forkCount ?? 0,
        open_issues: repo.openIssues?.totalCount ?? 0,
        last_commit_date: repo.pushedAt ?? null,
      });
    } else if (notFound.has(alias)) {
      dead.push({ tools: r.tools });
    } else {
      skipped++;
    }
  });
  return { live, dead, skipped };
}

async function fetchStats(repos) {
  const live = [];
  const dead = [];
  let skipped = 0;
  const totalChunks = Math.ceil(repos.length / 100);
  for (let i = 0; i < repos.length; i += 100) {
    const chunk = repos.slice(i, i + 100);
    const chunkNum = Math.floor(i / 100) + 1;
    const result = await fetchStatsChunk(chunk);
    live.push(...result.live);
    dead.push(...result.dead);
    skipped += result.skipped;
    if (result.skipped > 0) {
      console.log(`  chunk ${chunkNum}/${totalChunks}: ${result.live.length} live + ${result.dead.length} dead + ${result.skipped} SKIPPED`);
    }
    if (i + 100 < repos.length) await new Promise((r) => setTimeout(r, 600));
  }
  return { live, dead, skipped };
}

// POST per-tool velocity items to upsertVelocityData in small paced batches
// with retry (same pattern as refresh-stars.mjs upsert()).
async function upsert(items) {
  const BATCH = 25;
  const INTER_BATCH_DELAY_MS = 8000;
  let updated = 0;
  let created = 0;
  let failed = 0;
  const totalBatches = Math.ceil(items.length / BATCH);
  for (let i = 0; i < items.length; i += BATCH) {
    const chunk = items.slice(i, i + BATCH);
    const batchNum = i / BATCH + 1;
    const r = await fetchWithRetry(VELOCITY_UPSERT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', API_KEY: BASE44_API_KEY },
      body: JSON.stringify({ items: chunk }),
    });
    const res = await r.json().catch(() => ({}));
    updated += res.updated ?? 0;
    created += res.created ?? 0;
    failed += res.failed ?? 0;
    console.log(`  batch ${batchNum}/${totalBatches}: ${chunk.length} sent, updated=${res.updated ?? '?'}, created=${res.created ?? 0}, failed=${res.failed ?? 0}`);
    if (i + BATCH < items.length) await new Promise((res) => setTimeout(res, INTER_BATCH_DELAY_MS));
  }
  console.log(`Velocity upsert totals — updated: ${updated}, created: ${created}, failed: ${failed}`);
}

(async () => {
  const urlMap = await listTools();
  const repos = [];
  for (const [url, tools] of urlMap.entries()) {
    const parsed = parseRepo(url);
    if (parsed) repos.push({ ...parsed, url, tools });
  }
  const totalTools = [...urlMap.values()].reduce((n, g) => n + g.length, 0);
  console.log(`Refreshing velocity for ${repos.length} unique repos (${totalTools} tool rows)`);

  const { live, dead, skipped } = await fetchStats(repos);
  const covered = live.length + dead.length;
  const coveragePct = (covered / repos.length) * 100;
  const dropPct = (skipped / repos.length) * 100;
  console.log(`Coverage: ${coveragePct.toFixed(1)}% (live=${live.length}, dead=${dead.length}, skipped=${skipped} of ${repos.length})`);
  if (dropPct > MAX_COVERAGE_LOSS * 100) {
    throw new Error(`Coverage too low: ${dropPct.toFixed(1)}% of repos dropped (${skipped}/${repos.length}). Threshold is ${(MAX_COVERAGE_LOSS * 100).toFixed(0)}%. Failing job so /data-health reflects reality.`);
  }

  // Fan stats back out to one velocity item per tool (keyed by slug).
  const items = [];
  for (const l of live) {
    for (const t of l.tools) {
      items.push({
        tool_slug: t.slug,
        stars: l.stars,
        forks: l.forks,
        open_issues: l.open_issues,
        last_commit_date: l.last_commit_date,
      });
    }
  }
  for (const d of dead) {
    for (const t of d.tools) {
      items.push({ tool_slug: t.slug, sync_error: 'repo_not_found' });
    }
  }
  console.log(`Posting ${items.length} per-tool velocity rows (${live.length} live repos, ${dead.length} dead)`);
  await upsert(items);
  console.log('Done.');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
