// Pulls every tool from OSS AI Hub, asks GitHub GraphQL for live stats in
// batches of 100, posts the updates to Base44's upsert endpoint.
// No external deps — Node 20+ only.

const { GH_READONLY_TOKEN, BASE44_UPSERT_URL, BASE44_API_KEY } = process.env;
if (!GH_READONLY_TOKEN || !BASE44_UPSERT_URL || !BASE44_API_KEY) {
  throw new Error('Missing required env vars.');
}

// Coverage guard — the 404 purger loses its integrity value if it silently
// skips repos. Fail the job loudly when dropout exceeds this fraction so
// /data-health goes red instead of reporting a fake-green.
const MAX_COVERAGE_LOSS = 0.15; // 15%

// Total-feed floor — Base44 paginated toolsApiJson on 2026-05-04 with a hard
// cap of 100/page. If pagination silently breaks (e.g. server returns hasMore
// but truncates total), refuse to proceed instead of poisoning the directory
// with a 50-tool refresh that drops 1900+ repos as 'unverified'.
const MIN_TOOLS_EXPECTED = 1500;

// Page size and pacing for the paginated GET. Base44 caps limit at 100 even
// if you request more; 1.5s between pages dodges the Cloudflare rate-limit
// that 403s rapid-fire calls (observed during the 2026-05-04 incident).
const TOOLS_PAGE_LIMIT = 100;
const TOOLS_PAGE_DELAY_MS = 1500;
const TOOLS_USER_AGENT = 'ossaihub-cron-refresh-stars/1.0';

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

const normalizeUrl = (u) =>
  (u || '').toLowerCase().trim().replace(/\.git$/, '').replace(/\/$/, '');

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
  // Current shape (2026-05-04+): {data: [...], pagination: {page, limit, total, hasMore}}.
  // Tolerate the legacy bare-array shape too in case Base44 flips back.
  if (Array.isArray(raw)) return { items: raw, pagination: null };
  if (Array.isArray(raw?.data)) return { items: raw.data, pagination: raw.pagination || null };
  const preview = JSON.stringify(raw).slice(0, 300);
  throw new Error(`toolsApiJson page ${page} returned no array (auth/error): ${preview}`);
}

async function listTools() {
  const all = [];
  let page = 1;
  let total = null;
  // Hard ceiling so a misbehaving hasMore can't loop forever.
  const MAX_PAGES = 200;
  while (page <= MAX_PAGES) {
    const { items, pagination } = await fetchPage(page);
    all.push(...items);
    if (pagination) {
      if (total === null && typeof pagination.total === 'number') total = pagination.total;
      console.log(
        `  page ${page}: +${items.length} (running ${all.length}${total !== null ? ` / ${total}` : ''})`
      );
      if (!pagination.hasMore) break;
    } else {
      // Legacy shape — single response, no pagination.
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
    throw new Error(
      `toolsApiJson pagination undercount: loaded ${all.length} but total reported ${total}. Refusing to proceed.`
    );
  }
  if (all.length < MIN_TOOLS_EXPECTED) {
    throw new Error(
      `toolsApiJson returned only ${all.length} tools (< MIN_TOOLS_EXPECTED=${MIN_TOOLS_EXPECTED}). Aborting before this poisons /data-health.`
    );
  }
  console.log(`Loaded ${all.length} tools across ${page} page(s) from toolsApiJson`);
  const byUrl = new Map();
  for (const t of all) {
    if (!t.github_url) continue;
    const k = normalizeUrl(t.github_url);
    if (!byUrl.has(k)) byUrl.set(k, []);
    byUrl.get(k).push(t);
  }
  return byUrl;
}

// One chunk of up to 100 repos. Retries the whole chunk on transient GitHub
// errors (HTTP 5xx, secondary rate-limits, abuse detection) so partial-data
// responses don't silently drop repos from the 404 scan.
async function fetchStatsChunk(chunk, attempt = 0) {
  const MAX_ATTEMPTS = 5;
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

  let json;
  try {
    const res = await fetch('https://api.github.com/graphql', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GH_READONLY_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'ossaihub-refresher',
      },
      body: JSON.stringify({ query: `{${q}}` }),
    });

    // HTTP-level failure — GitHub 5xx, 403 (abuse), 429 (secondary rate-limit)
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      const retriable = res.status >= 500 || res.status === 403 || res.status === 429;
      if (retriable && attempt < MAX_ATTEMPTS - 1) {
        const wait = Math.min(60000, 3000 * Math.pow(2, attempt));
        console.log(
          `  GraphQL chunk HTTP ${res.status} (attempt ${attempt + 1}/${MAX_ATTEMPTS}) — retrying in ${wait}ms. Body: ${body.slice(0, 150)}`
        );
        await new Promise((r) => setTimeout(r, wait));
        return fetchStatsChunk(chunk, attempt + 1);
      }
      throw new Error(`GraphQL HTTP ${res.status}: ${body.slice(0, 300)}`);
    }
    json = await res.json();
  } catch (e) {
    if (attempt < MAX_ATTEMPTS - 1) {
      const wait = Math.min(60000, 3000 * Math.pow(2, attempt));
      console.log(
        `  GraphQL chunk fetch error (attempt ${attempt + 1}/${MAX_ATTEMPTS}) — retrying in ${wait}ms. Error: ${e.message.slice(0, 150)}`
      );
      await new Promise((r) => setTimeout(r, wait));
      return fetchStatsChunk(chunk, attempt + 1);
    }
    throw e;
  }

  // Partition errors: NOT_FOUND means dead repo (legitimate), everything else
  // means partial data — retry the chunk so those repos aren't silently dropped.
  const notFound = new Set();
  const otherErrors = [];
  if (Array.isArray(json.errors)) {
    for (const err of json.errors) {
      if (err.type === 'NOT_FOUND' && Array.isArray(err.path)) {
        notFound.add(err.path[0]);
      } else {
        otherErrors.push(err);
      }
    }
  }

  const hasTransient = otherErrors.some((e) => {
    const t = (e.type || '').toLowerCase();
    const msg = (e.message || '').toLowerCase();
    return (
      t === 'rate_limited' ||
      /rate.?limit|timeout|abuse|secondary|temporar/i.test(msg)
    );
  });
  if (hasTransient && attempt < MAX_ATTEMPTS - 1) {
    const wait = Math.min(60000, 8000 * Math.pow(2, attempt));
    console.log(
      `  GraphQL chunk got transient errors (attempt ${attempt + 1}/${MAX_ATTEMPTS}) — retrying full chunk in ${wait}ms. Errors: ${otherErrors.slice(0, 2).map((e) => e.message || e.type).join('; ').slice(0, 200)}`
    );
    await new Promise((r) => setTimeout(r, wait));
    return fetchStatsChunk(chunk, attempt + 1);
  }
  if (otherErrors.length) {
    console.warn(
      `  GraphQL non-404 errors on chunk (after ${attempt + 1} attempts):`,
      otherErrors.slice(0, 3).map((e) => ({ type: e.type, message: e.message?.slice(0, 120) }))
    );
  }

  const live = [];
  const dead = [];
  let skipped = 0;

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
      // Keep status in lockstep with archived=true.
      if (repo.isArchived) payload.status = 'archived';
      live.push(payload);
    } else if (notFound.has(alias)) {
      dead.push({
        github_url: `https://github.com/${r.owner}/${r.name}`,
        archived: true,
        status: 'archived',
      });
    } else {
      // Got neither live data nor explicit NOT_FOUND — repo was dropped due
      // to an upstream error we couldn't recover from. Count it.
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
    // Short pause between chunks to avoid GitHub secondary rate-limits.
    if (i + 100 < repos.length) {
      await new Promise((r) => setTimeout(r, 600));
    }
  }
  return { live, dead, skipped };
}

async function upsert(records) {
  // Base44's upsert is serial under the hood. Smaller batches + longer pacing
  // keep us below the rate-limit ceiling that caused the 2026-04-23 08:12 failure.
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
  console.log(
    `Refreshing ${repos.length} unique repos (${[...urlMap.values()].reduce((n, g) => n + g.length, 0)} total rows)`
  );
  const { live, dead, skipped } = await fetchStats(repos);

  const covered = live.length + dead.length;
  const coveragePct = (covered / repos.length) * 100;
  const dropPct = (skipped / repos.length) * 100;
  console.log(
    `Coverage: ${coveragePct.toFixed(1)}% (live=${live.length}, dead=${dead.length}, skipped=${skipped} of ${repos.length})`
  );

  // Fail-loudly guardrail: if we dropped too many repos, something upstream
  // is broken — exit non-zero so /data-health flips red instead of reporting
  // a fake-green on a half-completed scan.
  if (dropPct > MAX_COVERAGE_LOSS * 100) {
    throw new Error(
      `Coverage too low: ${dropPct.toFixed(1)}% of repos dropped (${skipped}/${repos.length}). Threshold is ${(MAX_COVERAGE_LOSS * 100).toFixed(0)}%. Failing job so /data-health reflects reality.`
    );
  }

  // Filter dead list to only URLs with at least one NOT-yet-archived row.
  const deadNeedingArchive = dead.filter((item) => {
    const records = urlMap.get(normalizeUrl(item.github_url)) || [];
    return records.some((r) => r.archived !== true);
  });
  const deadAlreadyArchived = dead.length - deadNeedingArchive.length;

  console.log(
    `Live: ${live.length}, dead total: ${dead.length} (already archived: ${deadAlreadyArchived}, new flips: ${deadNeedingArchive.length})`
  );

  await upsert([...deadNeedingArchive, ...live]);
  console.log('Done.');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
