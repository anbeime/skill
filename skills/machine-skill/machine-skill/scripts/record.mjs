#!/usr/bin/env node
// Turn any Machine Skill page into a film, frame exact, in one command.
//
//   node scripts/record.mjs examples/turbofan.html out/turbofan.mp4
//   node scripts/record.mjs examples/turbofan.html out/turbofan.mp4 --shot main --music freepd:Classical/Easy_Lemon
//
// The page runs in film mode (?film=1&shot=NAME): its clock only moves when the recorder calls
// window.__film.step(1/fps), so every frame is rendered completely, at any machine speed.
// Options:
//   --shot NAME     film to record (default main; the page's autoFilm() if it defines none)
//   --fps 30        frames per second (60 for very fast motion)
//   --w 1920 --h 1080   size (1080x1350 for a feed portrait, 1080x1920 for a story)
//   --ss 1.5        supersampling: the page renders at ss x the size, the frame is scaled down
//   --blur 2        motion blur: render k sub-frames per frame and average them
//   --from s --to s record only part of the film
//   --stills 2,9.5  write stills (jpg) at these times instead of a film
//   --music X       a music bed: a file path, an https URL, or freepd:<Category>/<Name> (CC0 from archive.org)
//   --gain -14      music level in LUFS (integrated), default -18 (a soft bed)
//   --root DIR      folder to serve (default: the folder above the page, so ../kit resolves)
import { spawn, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve, relative, basename, join } from 'node:path'
import { homedir } from 'node:os'
import { serve } from './lib/serve.mjs'
import { launch } from './lib/browser.mjs'
import { scanFile } from './pinkscan.mjs'

const a = process.argv.slice(2)
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d }
const pos = a.filter((x, i) => !x.startsWith('--') && !(i > 0 && a[i - 1].startsWith('--')))
const [PAGE, OUT] = pos
if (!PAGE || !OUT) { console.log('usage: node scripts/record.mjs <page.html|url> <out.mp4> [--shot main] [--music freepd:Category/Name]'); process.exit(1) }
const FPS = Number(opt('--fps', 30)), W = Number(opt('--w', 1920)), H = Number(opt('--h', 1080))
const SS = Number(opt('--ss', 1.5)), BLUR = Number(opt('--blur', 1)), SHOT = opt('--shot', 'main')
const STILLS = opt('--stills') ? opt('--stills').split(',').map(Number) : null
const FFMPEG = process.env.FFMPEG || 'ffmpeg'

let url, srv
if (/^https?:/.test(PAGE)) url = PAGE
else {
  const file = resolve(PAGE), root = resolve(opt('--root', dirname(dirname(file))))
  srv = await serve(root)
  url = `${srv.url}/${relative(root, file).split('\\').join('/')}`
}
const sep = url.includes('?') ? '&' : '?'
url += `${sep}film=1&shot=${encodeURIComponent(SHOT)}&ss=${SS}`
mkdirSync(dirname(resolve(OUT)), { recursive: true })

const { browser, page } = await launch({ width: W, height: H })
console.log('open', url)
await page.goto(url, { waitUntil: 'load', timeout: 120000 })
await page.waitForFunction(() => window.__film?.ready && window.__film.loaded(), null, { timeout: 180000, polling: 250 })
await page.evaluate(() => document.fonts.ready)
await page.evaluate(() => { document.querySelector('canvas')?.addEventListener('webglcontextlost', () => { window.__lost = true }) })
const LEN = await page.evaluate(() => window.__film.len)
const FROM = Number(opt('--from', 0)), TO = Number(opt('--to', LEN))
await page.evaluate(() => window.__film.start())
// warm up: compile shaders, fill render targets and shadow maps before the first captured frame
for (let k = 0; k < 6; k++) await page.evaluate(() => window.__film.step(0))
await page.waitForTimeout(400)
if (FROM > 0) await page.evaluate((t) => window.__film.seek(t), FROM)

const t0 = Date.now()
if (STILLS) {
  let t = FROM
  for (const s of STILLS.sort((x, y) => x - y)) {
    await page.evaluate(([a, b]) => window.__film.seek(b), [t, s]); t = s
    const f = OUT.replace(/\.(mp4|jpg|png)$/i, '') + `_${s.toFixed(1)}.jpg`
    await page.screenshot({ path: f, type: 'jpeg', quality: 93 }); console.log('still', f)
  }
  await browser.close(); srv?.server.close(); process.exit(0)
}

const silent = OUT.replace(/\.mp4$/i, '') + '.video.mp4'
const vf = BLUR > 1 ? ['-vf', `tmix=frames=${BLUR},select='not(mod(n\\,${BLUR}))',setpts=N/${FPS}/TB`] : []
const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * BLUR), '-c:v', 'png', '-i', 'pipe:0', ...vf, '-r', String(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-tune', 'film', '-movflags', '+faststart', silent], { stdio: ['pipe', 'inherit', 'inherit'] })
const N = Math.round((TO - FROM) * FPS)
for (let i = 0; i < N; i++) {
  for (let k = 0; k < BLUR; k++) {
    if (i > 0 || k > 0) await page.evaluate((dt) => window.__film.step(dt), 1 / (FPS * BLUR))
    if (await page.evaluate(() => !!window.__lost)) { console.error('WebGL context lost: take aborted'); process.exit(3) }
    const png = await page.screenshot({ type: 'png', timeout: 600000 })
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r))
  }
  if (i % 60 === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)} s`)
}
ff.stdin.end(); await new Promise((r) => ff.on('close', r))
await browser.close(); srv?.server.close()

// music bed
const music = opt('--music')
if (music) {
  let src = music
  if (music.startsWith('freepd:')) {
    const [cat, name] = music.slice(7).split('/')
    const dir = join(homedir(), '.cache', 'machine-skill', 'music'); mkdirSync(dir, { recursive: true })
    src = join(dir, `${cat}_${name}.mp3`)
    if (!existsSync(src)) {
      const u = `https://archive.org/download/freepd/${encodeURIComponent(cat)}/${encodeURIComponent(name)}.mp3`
      console.log('download', u)
      // archive.org mirrors fail now and then: retry with backoff, and keep the film silent if it never comes
      let ok = false
      for (let k = 0; k < 6 && !ok; k++) {
        try { const r = await fetch(u); if (r.ok) { writeFileSync(src, Buffer.from(await r.arrayBuffer())); ok = true } else console.log('music download', r.status, 'retry', k + 1) } catch (e) { console.log('music download error, retry', k + 1) }
        if (!ok) await new Promise((r) => setTimeout(r, 3000 * (k + 1)))
      }
      if (!ok) { console.error('music download failed: film kept silent at', silent, '(mux later with --music <file>)'); process.exit(4) }
    }
  }
  const len = TO - FROM, lufs = Number(opt('--gain', -18))
  const af = `afade=t=in:st=0:d=1.2,afade=t=out:st=${Math.max(0, len - 2.4).toFixed(2)}:d=2.4,loudnorm=I=${lufs}:TP=-2:LRA=9`
  const r = spawnSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', silent, '-i', src, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', af, '-c:a', 'aac', '-b:a', '192k', '-t', String(len), '-movflags', '+faststart', OUT], { stdio: 'inherit' })
  if (r.status !== 0) process.exit(5)
} else spawnSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', silent, '-c', 'copy', '-movflags', '+faststart', OUT], { stdio: 'inherit' })
spawnSync('rm', ['-f', silent])
console.log('done', OUT, `${((Date.now() - t0) / 1000).toFixed(0)} s`)
// no pink frames, ever
const bad = await scanFile(OUT)
if (bad.length) { console.error(`PINK FRAMES in ${basename(OUT)} at`, bad.map((t) => t.toFixed(2) + ' s').join(', ')); process.exit(6) }
console.log('pinkscan clean')
