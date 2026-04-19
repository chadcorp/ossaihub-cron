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

async function listTools() {
  const r = await fetch(TOOLS_LIST_URL, {
    headers: { Accept: 'application/json' },
  });
  if (!r.ok) throw new Error(`Tool list fetch failed: ${r.status}`);
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
  const r = await fetch(BASE44_UPSERT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', API_KEY: BASE44_API_KEY },
    body: JSON.stringify(records),
  });
  if (!r.ok) throw new Error(`Upsert failed: ${r.status} ${await r.text()}`);
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
