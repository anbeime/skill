#!/usr/bin/env node
// Screenshots for self review (Claude reads every PNG it makes).
//   node scripts/shot.mjs examples/turbofan.html out/review.png [--wait 4] [--js "lab.toggle('cut', true)"] [--then 2] [--w 1920 --h 1080]
//   node scripts/shot.mjs examples/turbofan.html out/film --film 1.5,8,14,20   (film stills at those times)
// Reports page errors, frame time and the part / triangle count.
//   --steps views.json   more views from the same load: [{ "js": "lab.toggle('explode', true)", "wait": 3, "out": "out/ex.png" }]
import { dirname, resolve, relative } from 'node:path'
import { mkdirSync } from 'node:fs'
import { serve } from './lib/serve.mjs'
import { launch } from './lib/browser.mjs'
const a = process.argv.slice(2)
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d }
const pos = a.filter((x, i) => !x.startsWith('--') && !(i > 0 && a[i - 1].startsWith('--')))
const [PAGE, OUT] = pos
const W = Number(opt('--w', 1920)), H = Number(opt('--h', 1080))
const file = resolve(PAGE), root = resolve(opt('--root', dirname(dirname(file))))
const srv = await serve(root)
const film = opt('--film')
const url = `${srv.url}/${relative(root, file)}${film ? '?film=1&shot=' + opt('--shot', 'main') : ''}${opt('--q') ? (film ? '&' : '?') + opt('--q') : ''}`
mkdirSync(dirname(resolve(OUT)), { recursive: true })
const { browser, page } = await launch({ width: W, height: H })
await page.goto(url, { waitUntil: 'load', timeout: 120000 })
if (film) {
  await page.waitForFunction(() => window.__film?.ready && window.__film.loaded(), null, { timeout: 180000 })
  await page.evaluate(() => document.fonts.ready)
  await page.evaluate(() => window.__film.start())
  for (let k = 0; k < 4; k++) await page.evaluate(() => window.__film.step(0))
  for (const t of film.split(',').map(Number)) {
    await page.evaluate((t) => window.__film.seek(t), t)
    await page.screenshot({ path: `${OUT}_${t.toFixed(1)}.jpg`, type: 'jpeg', quality: 90 }); console.log('still', t)
  }
} else {
  await page.waitForFunction(() => window.__lab?.renderer, null, { timeout: 120000 })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(Number(opt('--wait', 4.5)) * 1000)
  if (opt('--js')) { await page.evaluate((s) => { const lab = window.__lab; return eval(s) }, opt('--js')); await page.waitForTimeout(Number(opt('--then', 2.5)) * 1000) }
  const info = await page.evaluate(async () => { const lab = window.__lab; const t0 = performance.now(); let n = 0; await new Promise((r) => { const f = () => { n++; if (performance.now() - t0 < 1000) requestAnimationFrame(f); else r() }; requestAnimationFrame(f) }); return { fps: n, parts: lab.partCount(), tris: lab.tris, materials: lab.matCount, calls: lab.renderer.info.render.calls } })
  console.log(JSON.stringify(info))
  await page.screenshot({ path: OUT, timeout: 600000 })
  // --steps file.json: [{ "js": "...", "wait": 3, "out": "out/x.png" }, ...] more views from the same page load
  if (opt('--steps')) {
    const { readFileSync } = await import('node:fs')
    for (const st of JSON.parse(readFileSync(opt('--steps'), 'utf8'))) {
      if (st.js) await page.evaluate((s) => { const lab = window.__lab; return eval(s) }, st.js)
      await page.waitForTimeout((st.wait ?? 3) * 1000)
      await page.screenshot({ path: st.out, timeout: 600000 }); console.log('shot', st.out)
    }
  }
}
await browser.close(); srv.server.close()
