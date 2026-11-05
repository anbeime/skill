#!/usr/bin/env node
/**
 * One-off: select ~56 high-value projects from competitor missing pool
 * and merge into data/projects.json (keep existing 44 untouched).
 * Target total ~100. Prefer stars >= 50, then distinctive decision-point fills.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');

const TARGET_TOTAL = 100;
const TARGET_ADDED = TARGET_TOTAL - 44; // ~56
const STAR_FLOOR = 50;

const CATEGORY_MAP = {
  'Browser & OS Action': 'browser-computer-use',
  'SDK & Decision Frameworks': 'sdk-integrations',
  'SDK & Integrations': 'sdk-integrations',
  'Routing & Cost Optimization': 'routing-optimization',
  'Security & Guardrails': 'safety-review',
  'Domain & Vertical Tools': 'domain-tools',
  'High-Frequency & Simulation': 'domain-tools',
  'Data & Search': 'search-data',
  'MCP & Integrations': 'developer-tools',
  'CLI & Pipelines': 'developer-tools',
  'Evaluation & Observability': 'developer-tools',
  'Codebase & Graph Pathfinding': 'developer-tools',
  'Context GC & Filter': 'agent-workflows',
  'Decision Tools': 'agent-workflows',
  'Classification & Taxonomy': 'agent-workflows',
  'Creative Tools': 'interfaces',
  'Voice & Conversation': 'interfaces',
};

const args = process.argv.slice(2);
function argValue(flag, fallback) {
  const i = args.indexOf(flag);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}

const competitorPath = resolve(
  argValue('--competitor', resolve(ROOT, '../.local-jev/competitor-projects.json')),
);
const missingPath = resolve(
  argValue('--missing', resolve(ROOT, '../.local-jev/missing.json')),
);
const cataloguePath = resolve(argValue('--catalogue', resolve(ROOT, 'data/projects.json')));
const dryRun = args.includes('--dry-run');

function normUrl(u) {
  if (!u) return '';
  return String(u)
    .trim()
    .replace(/\/$/, '')
    .replace(/\.git$/i, '')
    .replace(/^https?:\/\/(www\.)?github\.com\//i, 'https://github.com/')
    .toLowerCase();
}

function titleCaseName(name, id) {
  const raw = (name || id || '').trim();
  if (!raw) return 'Untitled';
  // Already has spaces / mixed case → keep light touch
  if (/\s/.test(raw) || /[A-Z]/.test(raw.slice(1))) return raw;
  // slug-like: foo-bar-baz → Foo Bar Baz (keep known short tokens)
  return raw
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => {
      const lower = part.toLowerCase();
      if (['ai', 'sdk', 'api', 'cli', 'mcp', 'os', 'ui', 'llm', 'rag'].includes(lower)) {
        return lower.toUpperCase();
      }
      if (['jev', 'typesafe'].includes(lower)) {
        return lower === 'jev' ? 'JEV' : 'TypeSafe';
      }
      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(' ');
}

function sanitizeId(id) {
  return String(id || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9:_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 120);
}

function decisionText(c) {
  return String(c.jevDecisionPointEn || c.jevDecisionPoint || '').trim();
}

function summaryText(c) {
  return String(c.plainSummaryEn || c.plainSummary || '').trim();
}

function hasGithubUrl(c) {
  const u = c.url || '';
  return /^https:\/\/github\.com\/[^/]+\/[^/]+/i.test(u);
}

function mapCategory(cat) {
  return CATEGORY_MAP[cat] || 'developer-tools';
}

function decisionPatternKey(text) {
  const t = text.toLowerCase();
  const buckets = [];
  if (/rout|complexit|model pick|tier|cost/.test(t)) buckets.push('routing');
  if (/tool|function.?call|invoke|mcp/.test(t)) buckets.push('tool-pick');
  if (/safet|guard|policy|allow|deny|jail|pii|moderat/.test(t)) buckets.push('safety');
  if (/browser|dom|click|action|computer.?use|os /.test(t)) buckets.push('browser');
  if (/retriev|search|rank|rerank|chunk|filter.?context|gc/.test(t)) buckets.push('retrieval');
  if (/classif|taxonom|label|categor/.test(t)) buckets.push('classify');
  if (/score|eval|judge|grade|rubric|observ/.test(t)) buckets.push('eval');
  if (/voice|speech|dialog|convers/.test(t)) buckets.push('voice');
  if (/code|pathfind|graph|repo|symbol/.test(t)) buckets.push('code');
  if (!buckets.length) buckets.push('other');
  return buckets[0];
}

function isEligible(c) {
  if (!hasGithubUrl(c)) return false;
  if (!summaryText(c)) return false;
  if (!decisionText(c)) return false;
  const license = (c.license || '').trim();
  const licenseUnknown = !license || /^unknown$/i.test(license);
  if (licenseUnknown && !decisionText(c)) return false; // already have decision, so allow
  return true;
}

function toOurProject(c) {
  const evidenceUrl =
    (Array.isArray(c.evidence) && c.evidence[0] && c.evidence[0].url) ||
    c.sourceUrl ||
    c.url;
  const id = sanitizeId(c.id);
  const enSummary = String(c.plainSummaryEn || c.plainSummary || '').trim();
  const zhSummary = String(c.plainSummary || c.plainSummaryEn || '').trim();
  const enDecision = String(c.jevDecisionPointEn || c.jevDecisionPoint || '').trim();
  const zhDecision = String(c.jevDecisionPoint || c.jevDecisionPointEn || '').trim();

  return {
    id,
    name: titleCaseName(c.name, c.id),
    owner: c.author || (c.repo || '').split('/')[0] || 'unknown',
    category: mapCategory(c.category),
    repoUrl: String(c.url).replace(/\/$/, ''),
    evidenceUrl,
    source: {
      type: 'github',
      label: 'GitHub source',
      url: evidenceUrl,
    },
    language: c.language || '',
    license: c.license || 'Unknown',
    starsAtCapture: Number(c.stars) || 0,
    summary: { en: enSummary, zh: zhSummary },
    decision: { en: enDecision, zh: zhDecision },
    verification: 'source-reviewed',
    runtimeVerified: false,
  };
}

function selectAdditions(missing, existingIds, existingUrls, want) {
  const eligible = missing
    .filter(isEligible)
    .filter((c) => {
      const id = sanitizeId(c.id);
      const url = normUrl(c.url);
      if (!id || existingIds.has(id)) return false;
      if (url && existingUrls.has(url)) return false;
      return true;
    })
    .sort((a, b) => (b.stars || 0) - (a.stars || 0));

  const selected = [];
  const usedIds = new Set();
  const usedUrls = new Set();
  const catCounts = new Map();
  const patternCounts = new Map();

  // Soft caps for diversity (allow overflow only if pool too thin)
  const softCatCap = Math.max(4, Math.ceil(want / 8)); // ~7 for 56
  const softPatternCap = Math.max(5, Math.ceil(want / 7));

  function tryTake(pool, { ignoreCaps = false } = {}) {
    for (const c of pool) {
      if (selected.length >= want) break;
      const id = sanitizeId(c.id);
      const url = normUrl(c.url);
      if (usedIds.has(id) || (url && usedUrls.has(url))) continue;

      const cat = mapCategory(c.category);
      const pattern = decisionPatternKey(decisionText(c));
      const catN = catCounts.get(cat) || 0;
      const patN = patternCounts.get(pattern) || 0;
      if (!ignoreCaps && (catN >= softCatCap || patN >= softPatternCap)) continue;

      selected.push(c);
      usedIds.add(id);
      if (url) usedUrls.add(url);
      catCounts.set(cat, catN + 1);
      patternCounts.set(pattern, patN + 1);
    }
  }

  const high = eligible.filter((c) => (c.stars || 0) >= STAR_FLOOR);
  const low = eligible.filter((c) => (c.stars || 0) < STAR_FLOOR);

  // Pass 1: stars >= 50 with diversity caps
  tryTake(high);

  // Pass 1b: fill underrepresented categories (high first, then distinctive lower-star)
  const ourCats = [
    'browser-computer-use','sdk-integrations','routing-optimization','safety-review',
    'domain-tools','search-data','developer-tools','agent-workflows','interfaces',
  ];
  const lowForBalance = [...low].sort((a, b) => {
    const ae = Array.isArray(a.evidence) && a.evidence[0]?.url ? 1 : 0;
    const be = Array.isArray(b.evidence) && b.evidence[0]?.url ? 1 : 0;
    if (be !== ae) return be - ae;
    return decisionText(b).length - decisionText(a).length || (b.stars || 0) - (a.stars || 0);
  });
  const under = ourCats
    .map((cat) => ({ cat, n: catCounts.get(cat) || 0 }))
    .filter((x) => x.n < 4)
    .sort((a, b) => a.n - b.n);
  for (const { cat } of under) {
    if (selected.length >= want) break;
    const target = 4;
    for (const pool of [high, lowForBalance]) {
      for (const c of pool) {
        if (selected.length >= want) break;
        if ((catCounts.get(cat) || 0) >= target) break;
        if (mapCategory(c.category) !== cat) continue;
        const id = sanitizeId(c.id);
        const url = normUrl(c.url);
        if (usedIds.has(id) || (url && usedUrls.has(url))) continue;
        if (!decisionText(c)) continue;
        selected.push(c);
        usedIds.add(id);
        if (url) usedUrls.add(url);
        catCounts.set(cat, (catCounts.get(cat) || 0) + 1);
        const pattern = decisionPatternKey(decisionText(c));
        patternCounts.set(pattern, (patternCounts.get(pattern) || 0) + 1);
      }
    }
  }

  // Pass 2: relax caps on remaining >=50
  tryTake(high, { ignoreCaps: true });
  // Pass 3: distinctive lower-star fills (prefer those with evidence[0].url)
  const lowPreferred = [...low].sort((a, b) => {
    const ae = Array.isArray(a.evidence) && a.evidence[0]?.url ? 1 : 0;
    const be = Array.isArray(b.evidence) && b.evidence[0]?.url ? 1 : 0;
    if (be !== ae) return be - ae;
    // Prefer longer/more specific decision text as "clear unique pattern"
    return decisionText(b).length - decisionText(a).length || (b.stars || 0) - (a.stars || 0);
  });
  tryTake(lowPreferred);
  tryTake(lowPreferred, { ignoreCaps: true });

  return { selected, eligibleCount: eligible.length, highCount: high.length };
}

const catalogue = JSON.parse(await readFile(cataloguePath, 'utf8'));
const competitor = JSON.parse(await readFile(competitorPath, 'utf8'));
let missing;
try {
  missing = JSON.parse(await readFile(missingPath, 'utf8'));
} catch {
  missing = null;
}

const existing = catalogue.projects;
const existingIds = new Set(existing.map((p) => p.id));
const existingUrls = new Set(existing.map((p) => normUrl(p.repoUrl)).filter(Boolean));

if (!missing) {
  missing = competitor.filter((c) => {
    const id = sanitizeId(c.id);
    const url = normUrl(c.url);
    if (id && existingIds.has(id)) return false;
    if (url && existingUrls.has(url)) return false;
    return true;
  });
}

const want = Math.max(0, TARGET_TOTAL - existing.length);
const { selected, eligibleCount, highCount } = selectAdditions(
  missing,
  existingIds,
  existingUrls,
  want,
);

const mapped = selected.map(toOurProject);

// Final dedupe safety
const finalProjects = [...existing];
const seenIds = new Set(existingIds);
const seenUrls = new Set(existingUrls);
const added = [];
for (const p of mapped) {
  const url = normUrl(p.repoUrl);
  if (seenIds.has(p.id) || (url && seenUrls.has(url))) continue;
  seenIds.add(p.id);
  if (url) seenUrls.add(url);
  finalProjects.push(p);
  added.push(p);
}

catalogue.capturedAt = '2026-09-20';
catalogue.projects = finalProjects;

// Stats
const byCat = {};
for (const p of added) byCat[p.category] = (byCat[p.category] || 0) + 1;
const bands = { '>=1000': 0, '100-999': 0, '50-99': 0, '1-49': 0, '0': 0 };
for (const p of added) {
  const s = p.starsAtCapture;
  if (s >= 1000) bands['>=1000']++;
  else if (s >= 100) bands['100-999']++;
  else if (s >= 50) bands['50-99']++;
  else if (s >= 1) bands['1-49']++;
  else bands['0']++;
}

const report = {
  existing: existing.length,
  missingPool: missing.length,
  eligibleInMissing: eligibleCount,
  starsGe50InEligible: highCount,
  added: added.length,
  total: finalProjects.length,
  categoryBreakdown: byCat,
  starBands: bands,
  topAdditions: [...added]
    .sort((a, b) => b.starsAtCapture - a.starsAtCapture)
    .slice(0, 12)
    .map((p) => ({ id: p.id, stars: p.starsAtCapture, category: p.category, name: p.name })),
};

console.log(JSON.stringify(report, null, 2));

if (!dryRun) {
  await writeFile(cataloguePath, `${JSON.stringify(catalogue, null, 2)}\n`);
  console.log(`\nWrote ${finalProjects.length} projects to ${cataloguePath}`);

  // Persist selection list for audit
  const auditDir = resolve(ROOT, '../.local-jev');
  await mkdir(auditDir, { recursive: true });
  await writeFile(
    resolve(auditDir, 'supplement-selection.json'),
    `${JSON.stringify({ capturedAt: catalogue.capturedAt, added: added.map((p) => p.id), report }, null, 2)}\n`,
  );
}
