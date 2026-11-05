import { execFile } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { promisify } from 'node:util';

const run = promisify(execFile);
const catalogueFile = new URL('../data/projects.json', import.meta.url);
const readmes = ['README.md', 'README.zh-CN.md', 'README.ja.md'].map(
  (name) => new URL(`../${name}`, import.meta.url),
);
const today = process.argv[2] ?? new Date().toISOString().slice(0, 10);
const catalogue = JSON.parse(await readFile(catalogueFile, 'utf8'));

async function fetchStars(repoUrl) {
  const slug = new URL(repoUrl).pathname.replace(/^\/|\/$/g, '');
  const { stdout } = await run('gh', ['api', `repos/${slug}`, '--jq', '.stargazers_count']);
  return Number(stdout.trim());
}

const failures = [];
const queue = [...catalogue.projects];
await Promise.all(
  Array.from({ length: 8 }, async () => {
    for (let project = queue.shift(); project; project = queue.shift()) {
      try {
        const stars = await fetchStars(project.repoUrl);
        if (!Number.isFinite(stars)) throw new Error('non-numeric star count');
        project.starsAtCapture = stars;
      } catch (error) {
        failures.push(`${project.id}: ${error.message.split('\n')[0]}`);
      }
    }
  }),
);
if (failures.length) throw new Error(`Star refresh failed, nothing written:\n${failures.join('\n')}`);

catalogue.capturedAt = today;
await writeFile(catalogueFile, `${JSON.stringify(catalogue, null, 2)}\n`);

const compact = (n) => `${(n / 1000).toFixed(1)}K`;
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const over1k = catalogue.projects.filter((p) => p.starsAtCapture >= 1000).length;

for (const file of readmes) {
  let text = await readFile(file, 'utf8');
  for (const { repoUrl, starsAtCapture: n } of catalogue.projects) {
    const url = escape(repoUrl);
    // Featured card: "**[Name](url)** · Category · 9.5K stars" (cells never contain "|").
    text = text.replace(
      new RegExp(`(\\*\\*\\[[^\\]]+\\]\\(${url}\\)\\*\\*[^|]*?)\\d+(?:\\.\\d+)?K (stars|Star)`),
      `$1${compact(n)} $2`,
    );
    // List entry: "- [Name](url) · 9,549 stars"
    text = text.replace(
      new RegExp(`(- \\[[^\\]]+\\]\\(${url}\\) · )[\\d,]+ (stars|Star)`),
      `$1${n.toLocaleString('en-US')} $2`,
    );
  }
  text = text.replace(
    /(<td align="center"><strong>)\d+(<\/strong><\/td>\n\s*<td align="center"><strong>10<\/strong><\/td>)/,
    `$1${over1k}$2`,
  );
  text = text.replace(/<strong>\d{4}-\d{2}-\d{2}<\/strong>/, `<strong>${today}</strong>`);
  // Keep the full project list ordered by stars (stable for ties).
  const entry = /^- \[[^\]]+\]\(https:\/\/github\.com\/[^)]+\) · ([\d,]+) (?:stars|Star)$/;
  const lines = text.split('\n');
  const first = lines.findIndex((line) => entry.test(line));
  let last = first;
  while (entry.test(lines[last + 1] ?? '')) last += 1;
  const block = lines.slice(first, last + 1).map((line, index) => ({ line, index, stars: Number(line.match(entry)[1].replace(/,/g, '')) }));
  block.sort((a, b) => b.stars - a.stars || a.index - b.index);
  lines.splice(first, block.length, ...block.map((item) => item.line));
  text = lines.join('\n');
  await writeFile(file, text);
}
console.log(`Refreshed ${catalogue.projects.length} projects; ${over1k} at or above 1K stars; snapshot ${today}.`);
