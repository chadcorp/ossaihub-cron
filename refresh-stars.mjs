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

// Base44 endpoints are flaky — retry transient 5xx with exponential backoff.
async function fetchWithRetry(url, opts = {}, attempts = 5) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      const r = await fetch(url, opts);
      if (r.ok) return r;
      if (r.status >= 500 && r.status < 600) {
        lastErr = new Error(`${r.status} on ${url}`);
        const wait = 1000 * Math.pow(2, i); // 1s, 2s, 4s, 8s, 16s
        console.log(`  retry ${i + 1}/${attempts} after ${wait}ms (${r.status})`);
        await new Promise((res) => setTimeout(res, wait));
        continue;
      }
      // 4xx is terminal
      throw new Error(`${r.status} ${(await r.text()).slice(0, 200)}`);
    } catch (e) {
      lastErr = e;
      const wait = 1000 * Math.pow(2, i);
      await new Promise((res) => setTimeout(res, wait));
    }
  }
  throw lastErr;
}

async function listTools() {
  const r = await fetchWithRetry(TOOLS_LIST_URL, {
    headers: { Accept: 'application/json' },
  });
  const tools = await r.json();
  // Dedupe by github_url so we don't waste GraphQL quota or double-upsert.
  const seen = new Set();
  return tools.filter((t) => {
    if (!t.github_url || seen.has(t.github_url)) return false;
    seen.add(t.github_url);
    return true;
  });
}

async function fetchStats(repos) {
  const out = [];
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
    if (json.errors) console.warn('GraphQL partial errors:', json.errors);

    chunk.forEach((_, idx) => {
      const repo = json.data?.[`r${idx}`];
      if (!repo) return; // repo 404 / deleted / renamed — skip silently
      out.push({
        github_url: `https://github.com/${repo.nameWithOwner}`,
        stars: repo.stargazerCount,
        forks: repo.forkCount,
        last_commit_at: repo.pushedAt,
        archived: repo.isArchived,
        license: repo.licenseInfo?.spdxId ?? null,
      });
    });
  }
  return out;
}

async function upsert(records) {
  // Batch to avoid overwhelming the Base44 function (was 502ing on ~900 records).
  const BATCH = 50;
  let updated = 0;
  let skipped = 0;
  for (let i = 0; i < records.length; i += BATCH) {
    const chunk = records.slice(i, i + BATCH);
    const r = await fetchWithRetry(BASE44_UPSERT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', API_KEY: BASE44_API_KEY },
      body: JSON.stringify(chunk),
    });
    const res = await r.json().catch(() => ({}));
    updated += res.updated ?? 0;
    skipped += res.skipped ?? 0;
    console.log(`  batch ${i / BATCH + 1}: ${chunk.length} sent`);
  }
  console.log(`Upsert totals — updated: ${updated}, skipped: ${skipped}`);
}

(async () => {
  const tools = await listTools();
  const repos = tools.map((t) => parseRepo(t.github_url)).filter(Boolean);
  console.log(`Refreshing ${repos.length} repos`);
  const updates = await fetchStats(repos);
  console.log(`Upserting ${updates.length} records`);
  await upsert(updates);
  console.log('Done.');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
