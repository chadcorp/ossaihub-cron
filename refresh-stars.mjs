// Pulls every tool from OSS AI Hub, asks GitHub GraphQL for live stats in
// batches of 100, posts the updates to Base44's upsert endpoint.
// No external deps — Node 20+ only.

const { GH_READONLY_TOKEN, BASE44_UPSERT_URL, BASE44_API_KEY } = process.env;
if (!GH_READONLY_TOKEN || !BASE44_UPSERT_URL || !BASE44_API_KEY) {
  throw new Error('Missing required env vars.');
}

const parseRepo = (url) => {
  const m = url?.match(/github\.com\/([^\/]+)\/([^\/?#]+)/);
  return m ? { owner: m[1], name: m[2].replace(/\.git$/, '') } : null;
};

const TOOLS_LIST_URL =
  'https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/toolsApiJson';

// Base44's upsert endpoint rate-limits under sustained load. It often
// wraps the rate-limit response as HTTP 500 with body {error: "... 429"}.
// Detect that pattern and apply longer backoffs specifically for rate-limits.
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
        // Rate-limits get a longer floor + slower growth; transient 5xx get
        // the normal exponential ramp.
        const baseWait = isRateLimit ? 15000 : 1000;
        const wait = Math.min(120000, baseWait * Math.pow(1.7, i));
        console.log(
          `  retry ${i + 1}/${attempts} after ${wait}ms (${r.status}${isRateLimit ? ' rate-limit' : ''}) body=${lastBody.slice(0, 150)}`
        );
        await new Promise((res) => setTimeout(res, wait));
        continue;
      }
      // 4xx is terminal
      throw new Error(`${r.status} ${(await r.text()).slice(0, 300)}`);
    } catch (e) {
      if (!lastStatus) lastStatus = -1;
      const wait = Math.min(30000, 1000 * Math.pow(2, i));
      await new Promise((res) => setTimeout(res, wait));
    }
  }
  throw new Error(`${lastStatus} on ${url} after ${attempts} retries. Last body: ${lastBody}`);
}

const normalizeUrl = (u) =>
  (u || '').toLowerCase().trim().replace(/\.git$/, '').replace(/\/$/, '');

async function listTools() {
  const r = await fetchWithRetry(TOOLS_LIST_URL, {
    headers: { Accept: 'application/json' },
  });
  const raw = await r.json();
  // Group records by normalized github_url so we can check current archived state
  // AND know when an archive-flip payload would be a wasteful no-op.
  const byUrl = new Map();
  for (const t of raw) {
    if (!t.github_url) continue;
    const k = normalizeUrl(t.github_url);
    if (!byUrl.has(k)) byUrl.set(k, []);
    byUrl.get(k).push(t);
  }
  return byUrl; // Map: normalized_url -> array of Tool records
}

async function fetchStats(repos) {
  const live = [];
  const dead = []; // repos GitHub explicitly reports as NOT_FOUND — auto-archive
  for (let i = 0; i < repos.length; i += 100) {
    const chunk = repos.slice(i, i + 100);
    const q = chunk
      .map(
        (r, idx) => `
      r${idx}: repository(owner: "${r.owner}", name: "${r.name}") {
        nameWithOwner
        stargazerCount forkCount pushedAt isArchived
        licenseInfo { spdxId }
      }`
      )
      .join('\n');

    const res = await fetch('https://api.github.com/graphql', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GH_READONLY_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'ossaihub-refresher',
      },
      body: JSON.stringify({ query: `{${q}}` }),
    });
    const json = await res.json();

    // Collect explicit NOT_FOUND aliases so we can auto-archive them.
    const notFound = new Set();
    if (Array.isArray(json.errors)) {
      for (const err of json.errors) {
        if (err.type === 'NOT_FOUND' && Array.isArray(err.path)) {
          notFound.add(err.path[0]); // e.g. 'r57'
        }
      }
      const other = json.errors.filter((e) => e.type !== 'NOT_FOUND');
      if (other.length) console.warn('GraphQL non-404 errors:', other);
    }

    chunk.forEach((r, idx) => {
      const alias = `r${idx}`;
      const repo = json.data?.[alias];
      if (repo) {
        const payload = {
          github_url: `https://github.com/${repo.nameWithOwner}`,
          stars: repo.stargazerCount,
          forks: repo.forkCount,
          last_commit_at: repo.pushedAt,
          archived: repo.isArchived,
          license: repo.licenseInfo?.spdxId ?? null,
        };
        // Keep status in lockstep with archived=true so the directory can't
        // claim an archived tool is still "approved" or "featured". The browse
        // UI filters by archived, but status leaks into JSON-LD, sitemaps, and
        // anywhere the public feed is consumed — trust-critical to keep aligned.
        if (repo.isArchived) payload.status = 'archived';
        live.push(payload);
      } else if (notFound.has(alias)) {
        // Only auto-archive on explicit NOT_FOUND — transient errors are ignored.
        dead.push({
          github_url: `https://github.com/${r.owner}/${r.name}`,
          archived: true,
          status: 'archived',
        });
      }
    });
  }
  return { live, dead };
}

async function upsert(records) {
  // Base44's upsert is serial under the hood. Smaller batches + longer pacing
  // keep us below the rate-limit ceiling that caused the 2026-04-23 failure.
  const BATCH = 25;
  const INTER_BATCH_DELAY_MS = 8000;
  let rowsUpdated = 0;
  let rowsFailed = 0;
  let groupsUpdated = 0;
  let groupsNotMatched = 0;
  const totalBatches = Math.ceil(records.length / BATCH);
  for (let i = 0; i < records.length; i += BATCH) {
    const chunk = records.slice(i, i + BATCH);
    const batchNum = i / BATCH + 1;
    const r = await fetchWithRetry(BASE44_UPSERT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', API_KEY: BASE44_API_KEY },
      body: JSON.stringify({ items: chunk }),
    });
    const res = await r.json().catch(() => ({}));
    rowsUpdated += res.rows_updated ?? res.updated ?? 0;
    rowsFailed += res.rows_failed ?? 0;
    groupsUpdated += res.url_groups_updated ?? 0;
    groupsNotMatched += res.url_groups_not_matched ?? 0;
    console.log(
      `  batch ${batchNum}/${totalBatches}: ${chunk.length} sent, rows_updated=${res.rows_updated ?? '?'}, failed=${res.rows_failed ?? 0}`
    );
    if (i + BATCH < records.length) {
      await new Promise((res) => setTimeout(res, INTER_BATCH_DELAY_MS));
    }
  }
  console.log(
    `Upsert totals — rows_updated: ${rowsUpdated}, rows_failed: ${rowsFailed}, url_groups_updated: ${groupsUpdated}, url_groups_not_matched: ${groupsNotMatched}`
  );
}

(async () => {
  const urlMap = await listTools();
  const uniqueUrls = [...urlMap.keys()];
  const repos = uniqueUrls.map((u) => parseRepo(u)).filter(Boolean);
  console.log(`Refreshing ${repos.length} unique repos (${[...urlMap.values()].reduce((n,g)=>n+g.length,0)} total rows)`);
  const { live, dead } = await fetchStats(repos);

  // Filter dead list to only URLs with at least one NOT-yet-archived row —
  // every write must land on a new flip, not overwrite an already-archived record.
  const deadNeedingArchive = dead.filter((item) => {
    const records = urlMap.get(normalizeUrl(item.github_url)) || [];
    return records.some((r) => r.archived !== true);
  });
  const deadAlreadyArchived = dead.length - deadNeedingArchive.length;

  console.log(
    `Live: ${live.length}, dead total: ${dead.length} (already archived: ${deadAlreadyArchived}, new flips: ${deadNeedingArchive.length})`
  );

  // Process archive-flip records FIRST so they land before rate-limit degrades throughput.
  await upsert([...deadNeedingArchive, ...live]);
  console.log('Done.');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
