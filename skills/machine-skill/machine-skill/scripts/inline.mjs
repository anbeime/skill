#!/usr/bin/env node
// Paste kit/lab-kit.js into every page between <!-- lab-kit:start --> and <!-- lab-kit:end -->,
// so the page is ONE self-contained file (three.js still comes from the pinned CDN).
//   node scripts/inline.mjs examples/turbofan.html [more.html ...]
//   node scripts/inline.mjs --link examples/turbofan.html   (back to <script src> for kit development)
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
const here = dirname(fileURLToPath(import.meta.url))
const kitPath = resolve(here, '../kit/lab-kit.js')
const kit = readFileSync(kitPath, 'utf8')
const args = process.argv.slice(2)
const link = args.includes('--link')
for (const f of args.filter((a) => !a.startsWith('--'))) {
  const src = readFileSync(f, 'utf8')
  const re = /<!-- lab-kit:start -->[\s\S]*?<!-- lab-kit:end -->/
  if (!re.test(src)) { console.error(`${f}: no lab-kit markers`); process.exitCode = 1; continue }
  const block = link
    ? `<!-- lab-kit:start -->\n<script type="module" src="${relative(dirname(resolve(f)), kitPath)}"></script>\n<!-- lab-kit:end -->`
    : `<!-- lab-kit:start -->\n<script type="module">\n${kit.replace(/<\/script/gi, '<\\/script')}\n</script>\n<!-- lab-kit:end -->`
  writeFileSync(f, src.replace(re, () => block))
  console.log(`${link ? 'linked' : 'inlined'} kit into ${f}`)
}
