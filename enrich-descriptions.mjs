// Backfills long_description on Tool records whose long_description is null/empty.
// Reads the tool list from the public toolsApiJson function, fetches the GitHub
// README for each unenriched tool, normalizes the markdown, and upserts the
// result via Base44's Tool upsert endpoint.
//
// Idempotent: the filter (`long_description` missing) means already-enriched
// tools are skipped. Safe to run nightly — self-healing for new submissions.
//
// Rate budget: ~1 README fetch per second (GitHub authenticated limit is 5k/hr;
// we stay well under). Upserts batch 50 with a 6s inter-batch delay, matching
// refresh-stars.mjs pacing so we don't collide with Base44's rolling window.
//
// No external deps — Node 20+ only.

const {
  GH_READONLY_TOKEN,
  BASE44_UPSERT_URL,
  BASE44_API_KEY,
  ENRICH_MAX_PER_RUN,   // optional: cap per-run (default 80 — finishes 175 in ~3 nights)
  ENRICH_DRY_RUN,       // optional: 'true' to log changes without writing
} = process.env;

if (!GH_READONLY_TOKEN || !BASE44_UPSERT_URL || !BASE44_API_KEY) {
  throw new Error('Missing required env vars (GH_READONLY_TOKEN, BASE44_UPSERT_URL, BASE44_API_KEY).');
}

const MAX_PER_RUN = Number(ENRICH_MAX_PER_RUN) || 80;
const DRY_RUN = String(ENRICH_DRY_RUN ?? '').toLowerCase() === 'true';

const TOOLS_LIST_URL =
  'https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/toolsApiJson';

const PER_FETCH_DELAY_MS = 1000;        // 1 req/sec to GitHub
const UPSERT_BATCH = 20;
const UPSERT_INTER_BATCH_DELAY_MS = 30000;
const MIN_DESCRIPTION_CHARS = 200;       // skip if README is empty/too short to be useful
const MAX_DESCRIPTION_WORDS = 600;        // ~2500 chars — enough for Google to index, not overwhelming

const parseRepo = (url) => {
  const m = url?.match(/github\.com\/([^\/]+)\/([^\/?#]+)/);
  return m ? { owner: m[1], name: m[2].replace(/\.git$/, '') } : null;
};

const normalizeUrl = (u) =>
  (u || '').toLowerCase().trim().replace(/\.git$/, '').replace(/\/$/, '');

async function fetchWithRetry(url, opts = {}, attempts = 5) {
  let lastBody = '';
  let lastStatus = 0;
  for (let i = 0; i < attempts; i++) {
    try {
      const r = await fetch(url, opts);
      if (r.ok) return r;
      lastStatus = r.status;
      if (r.status >= 500 && r.status < 600) {
        lastBody = (await r.text()).slice(0, 500);
        const wait = 1000 * Math.pow(2, i);
        console.log(`  retry ${i + 1}/${attempts} after ${wait}ms (${r.status})`);
        await new Promise((res) => setTimeout(res, wait));
        continue;
      }
      throw new Error(`${r.status} ${(await r.text()).slice(0, 300)}`);
    } catch (e) {
      if (!lastStatus) lastStatus = -1;
      const wait = 1000 * Math.pow(2, i);
      await new Promise((res) => setTimeout(res, wait));
    }
  }
  throw new Error(`${lastStatus} on ${url} after ${attempts} retries. Last body: ${lastBody}`);
}

async function listTools() {
  const r = await fetchWithRetry(TOOLS_LIST_URL, {
    headers: { Accept: 'application/json' },
  });
  return r.json();
}

// README → clean markdown. Strips badges, HTML wrappers, and truncates to a
// digestible excerpt. Intentionally conservative — we'd rather skip a bad
// README than publish slop.
function normalizeReadme(raw, githubUrl) {
  if (!raw || typeof raw !== 'string') return null;

  let text = raw;

  // Strip HTML comments.
  text = text.replace(/<!--[\s\S]*?-->/g, '');

  // Strip opening <p align="center">...</p> / <div align="center">...</div>
  // blocks that typically hold logos + badges. Do this before the generic
  // HTML strip so we can kill multi-line blocks cleanly.
  text = text.replace(
    /<(p|div|center)[^>]*align=["']?center["']?[^>]*>[\s\S]*?<\/\1>/gi,
    ''
  );

  // Strip all remaining HTML tags (a, img, br, etc.) but keep their text.
  text = text.replace(/<\/?[a-zA-Z][^>]*>/g, '');

  // Strip shields.io / img.shields.io / badge-style image references on their
  // own. Also kill generic image references at the top of the doc (logos).
  text = text.replace(/!\[[^\]]*\]\([^)]*(shields\.io|badge|coveralls|travis-ci|circleci|appveyor|codecov|snyk|github\.com\/.*\/workflows|github\.com\/.*\/actions)[^)]*\)/gi, '');
  text = text.replace(/\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)/g, '');
  text = text.replace(/!\[[^\]]*\]\([^)]*\)/g, '');

  // Strip standalone reference-style badge definitions.
  text = text.replace(/^\[[^\]]+\]:\s*https?:\/\/.*(shields\.io|badge).*$/gim, '');

  // Strip lone "---" / "===" separator lines that create weird empty sections.
  // (But preserve markdown heading underlines, which are next to heading text.)
  text = text.replace(/^[-=]{3,}\s*$/gm, '');

  // Collapse 3+ blank lines to 2, trim leading blanks.
  text = text.replace(/\n{3,}/g, '\n\n').replace(/^\s+/, '').trim();

  // Truncate to MAX_DESCRIPTION_WORDS without mid-sentence chop.
  const words = text.split(/\s+/);
  if (words.length > MAX_DESCRIPTION_WORDS) {
    text = words.slice(0, MAX_DESCRIPTION_WORDS).join(' ');
    // Trim back to last full paragraph for cleanliness.
    const lastBreak = text.lastIndexOf('\n\n');
    if (lastBreak > text.length * 0.6) text = text.slice(0, lastBreak);
    text = text.replace(/[\s,.;:]+$/, '') + '…';
  }

  if (text.length < MIN_DESCRIPTION_CHARS) return null;

  // Append a "read more" anchor. Gives users a next click; gives Google an
  // outbound authority signal to the actual repo.
  text += `\n\n---\n\n📖 [Full documentation on GitHub →](${githubUrl})`;

  return text;
}

async function fetchReadme({ owner, name }) {
  const url = `https://api.github.com/repos/${owner}/${name}/readme`;
  const r = await fetch(url, {
    headers: {
      Authorization: `Bearer ${GH_READONLY_TOKEN}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'ossaihub-enricher',
    },
  });
  if (r.status === 404) return { notFound: true };
  if (!r.ok) return { error: `${r.status} ${r.statusText}` };
  const json = await r.json();
  if (!json.content) return { error: 'no content field' };
  const raw = Buffer.from(json.content, json.encoding || 'base64').toString('utf8');
  return { raw };
}

async function upsert(records) {
  if (!records.length) return;
  if (DRY_RUN) {
    console.log(`[DRY RUN] would upsert ${records.length} records. Skipping network write.`);
    console.log(`  sample:`, JSON.stringify(records[0]).slice(0, 400));
    return;
  }
  let rowsUpdated = 0;
  let rowsFailed = 0;
  let groupsUpdated = 0;
  let groupsNotMatched = 0;
  const totalBatches = Math.ceil(records.length / UPSERT_BATCH);
  for (let i = 0; i < records.length; i += UPSERT_BATCH) {
    const chunk = records.slice(i, i + UPSERT_BATCH);
    const batchNum = i / UPSERT_BATCH + 1;
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
      `  upsert batch ${batchNum}/${totalBatches}: ${chunk.length} sent, rows_updated=${res.rows_updated ?? '?'}, failed=${res.rows_failed ?? 0}`
    );
    if (i + UPSERT_BATCH < records.length) {
      await new Promise((res) => setTimeout(res, UPSERT_INTER_BATCH_DELAY_MS));
    }
  }
  console.log(
    `Upsert totals — rows_updated: ${rowsUpdated}, rows_failed: ${rowsFailed}, url_groups_updated: ${groupsUpdated}, url_groups_not_matched: ${groupsNotMatched}`
  );
}

(async () => {
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}; max this run: ${MAX_PER_RUN}`);

  const tools = await listTools();
  console.log(`Fetched ${tools.length} total tool records from toolsApiJson.`);

  // If the public feed doesn't expose long_description we can't filter locally.
  // Bail with a clear message rather than hammer GitHub for 2k+ READMEs.
  const sampleHasField = tools.some((t) => 'long_description' in t);
  if (!sampleHasField) {
    console.error(
      'ABORT: toolsApiJson does not expose `long_description`. ' +
      'Add it to the function response so this script can filter unenriched tools. ' +
      'Exiting to avoid unnecessary GitHub API usage.'
    );
    process.exit(2);
  }

  // Dedup by normalized github_url — tools can appear in multiple category rows.
  const seen = new Set();
  const candidates = [];
  for (const t of tools) {
    if (t.status && t.status !== 'approved') continue;
    if (t.archived === true) continue;
    if (!t.github_url) continue;
    if (t.long_description && t.long_description.trim().length >= MIN_DESCRIPTION_CHARS) continue;
    const key = normalizeUrl(t.github_url);
    if (seen.has(key)) continue;
    seen.add(key);
    const repo = parseRepo(t.github_url);
    if (!repo) continue;
    candidates.push({ github_url: t.github_url, repo, name: t.name, slug: t.slug });
  }

  console.log(`Unenriched candidates (unique github_urls): ${candidates.length}`);
  const batch = candidates.slice(0, MAX_PER_RUN);
  console.log(`Processing ${batch.length} this run (cap=${MAX_PER_RUN}).`);

  const updates = [];
  const stats = { fetched: 0, notFound: 0, tooShort: 0, errors: 0 };
  for (let i = 0; i < batch.length; i++) {
    const { github_url, repo, name } = batch[i];
    try {
      const r = await fetchReadme(repo);
      if (r.notFound) {
        stats.notFound++;
        console.log(`  [${i + 1}/${batch.length}] 404 ${name} (${repo.owner}/${repo.name}) — skipping`);
      } else if (r.error) {
        stats.errors++;
        console.log(`  [${i + 1}/${batch.length}] ERR ${name}: ${r.error}`);
      } else {
        const clean = normalizeReadme(r.raw, github_url);
        if (!clean) {
          stats.tooShort++;
          console.log(`  [${i + 1}/${batch.length}] thin ${name} — README too short after clean, skipping`);
        } else {
          stats.fetched++;
          updates.push({ github_url, long_description: clean });
          console.log(`  [${i + 1}/${batch.length}] ok   ${name} (${clean.length} chars)`);
        }
      }
    } catch (e) {
      stats.errors++;
      console.log(`  [${i + 1}/${batch.length}] THROW ${name}: ${e.message}`);
    }
    if (i + 1 < batch.length) {
      await new Promise((res) => setTimeout(res, PER_FETCH_DELAY_MS));
    }
  }

  console.log(
    `Fetch summary — enriched: ${stats.fetched}, 404: ${stats.notFound}, tooShort: ${stats.tooShort}, errors: ${stats.errors}`
  );

  await upsert(updates);
  console.log('Done.');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
