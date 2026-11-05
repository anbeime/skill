import assert from 'node:assert/strict';
import { readFile, readdir, access } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import test from 'node:test';
const root = new URL('../', import.meta.url);
const read = path => readFile(new URL(path, root), 'utf8');
const catalogue = JSON.parse(await read('data/projects.json'));
const { scenarios } = JSON.parse(await read('data/scenarios.json'));

test('scenario references resolve to real, unique projects with localized editorial guidance', () => {
  const ids = new Set(catalogue.projects.map(p => p.id));
  assert.equal(new Set(scenarios.map(s => s.id)).size, scenarios.length);
  for (const scene of scenarios) {
    assert.match(scene.id, /^[a-z0-9-]+$/);
    assert.equal(new Set(scene.projects.map(p => p.projectId)).size, scene.projects.length);
    assert.ok(scene.projects.length > 0);
    for (const lang of ['en','zh','ja']) {
      for (const field of ['title','description','flow']) assert.ok(scene[field][lang]);
      for (const ref of scene.projects) {
        assert.ok(ids.has(ref.projectId), `orphan: ${ref.projectId}`);
        assert.ok(ref.reference[lang]);
      }
    }
  }
});

test('README and scenario navigation resolves locally, including fragment anchors', async () => {
  const files = ['README.md','README.zh-CN.md','README.ja.md',
    ...(await readdir(new URL('scenarios/',root))).map(f=>'scenarios/'+f),
    ...(await readdir(new URL('docs/',root))).filter(f=>f.startsWith('agent-search.')).map(f=>'docs/'+f)];
  for (const file of files) {
    const text = await read(file);
    const links = [...text.matchAll(/\]\(([^)]+)\)|href="([^"]+)"/g)].map(m=>m[1]??m[2]);
    for (const link of links) {
      if (/^https?:/.test(link)) continue;
      const [path, fragment] = link.split('#');
      const target = resolve(dirname(new URL(file,root).pathname),path || file.split('/').at(-1));
      await access(target);
      if (fragment) {
        const contents = await readFile(target,'utf8');
        assert.ok(contents.includes(`id="${fragment}"`), `${file}: missing ${link}`);
      }
    }
  }
});

test('generation is repeatable and preserves all catalogue projects in every language', async () => {
  const files=['README.md','README.zh-CN.md','README.ja.md',...(await readdir(new URL('scenarios/',root))).map(f=>'scenarios/'+f)];
  const before=await Promise.all(files.map(read));
  execFileSync(process.execPath,['scripts/sync-readmes.mjs'],{cwd:root});
  const after=await Promise.all(files.map(read));
  assert.deepEqual(after,before);
  for (const doc of after.slice(0,3)) for (const p of catalogue.projects) assert.ok(doc.includes(p.repoUrl));
});
