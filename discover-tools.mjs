// Runs nightly GitHub-search-driven discovery of new OSS AI tools.
// Each Base44 discoverGitHubTools call handles one category (~40s), so we
// iterate the category list sequentially with breathing room between calls.
// Auto-approved by default: the cron stars-refresh job will archive anything
// that 404s next day.

const { DISCOVERY_SECRET, DISCOVERY_ENDPOINT } = process.env;
if (!DISCOVERY_SECRET || !DISCOVERY_ENDPOINT) {
  throw new Error('Missing DISCOVERY_SECRET or DISCOVERY_ENDPOINT env vars.');
}

const CATEGORIES = [
  'llms-foundation',
  'agent-frameworks',
  'ai-coding-ide-tools',
  'computer-vision',
  'nlp-speech',
  'multimodal',
  'mlops-deployment',
  'ai-devops-deployment',
  'ethics-safety',
  'audio-music-ai',
  'embodied-robotics',
  'mobile-on-device-ai',
  'reinforcement-learning-simulators',
  'mcp-tool-infrastructure',
  'prompt-engineering-structured-output',
  'model-training-finetuning',
  'agent-memory-systems',
  'rag-knowledge-graphs',
  'desktop-personal-agents',
  'vector-databases-embeddings',
  'llm-gateways-routing',
  'video-generation',
  'llm-observability-tracing',
  'llm-evaluation-benchmarks',
  'document-intelligence-parsing',
  'data-labeling-annotation',
  'browser-computer-use-agents',
];

const MAX_PER_CATEGORY = 10;
const INTER_CATEGORY_MS = 15000; // 15s between categories to preserve GitHub rate limit

async function runCategory(cat) {
  const body = {
    secret: DISCOVERY_SECRET,
    category: cat,
    maxPerCategory: MAX_PER_CATEGORY,
    autoApprove: true,
  };
  const r = await fetch(DISCOVERY_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  let parsed;
  try { parsed = JSON.parse(text); } catch { parsed = { raw: text.slice(0, 300) }; }
  return { status: r.status, parsed };
}

(async () => {
  const start = Date.now();
  const totals = { discovered: 0, promoted: 0, filtered: 0, errors: 0 };
  const perCat = {};
  for (const cat of CATEGORIES) {
    try {
      const { status, parsed } = await runCategory(cat);
      if (status !== 200) {
        totals.errors++;
        perCat[cat] = { status, error: parsed.raw || parsed.error || 'non-200' };
        console.log(`  ${cat}: ERROR http=${status}`);
      } else {
        const b = parsed.body || parsed;
        const d = b.discovered || 0;
        const p = b.promoted || 0;
        const f = b.filtered || 0;
        totals.discovered += d;
        totals.promoted += p;
        totals.filtered += f;
        perCat[cat] = { discovered: d, promoted: p, filtered: f };
        console.log(`  ${cat}: discovered=${d} promoted=${p} filtered=${f}`);
      }
    } catch (e) {
      totals.errors++;
      perCat[cat] = { error: String(e.message || e).slice(0, 200) };
      console.log(`  ${cat}: EXCEPTION ${e.message}`);
    }
    await new Promise((r) => setTimeout(r, INTER_CATEGORY_MS));
  }
  const durSec = Math.round((Date.now() - start) / 1000);
  console.log('');
  console.log(`=== Nightly discovery done in ${durSec}s ===`);
  console.log(`discovered=${totals.discovered}  promoted=${totals.promoted}  filtered=${totals.filtered}  errors=${totals.errors}`);
  console.log('');
  console.log('Per-category:');
  console.log(JSON.stringify(perCat, null, 2));
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
