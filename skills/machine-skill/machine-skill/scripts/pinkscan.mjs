#!/usr/bin/env node
// Scan films for magenta flash frames (a dying headless GPU returns #FF00FF). Exit 1 if any frame is
// more than 25 % pink, or blinks magenta against its neighbours in a dark scene.
//   node scripts/pinkscan.mjs out/*.mp4
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
export function scanFile(file) {
  return new Promise((ok, fail) => {
    const W = 64, H = 36, FR = W * H * 3
    const p = spawn(process.env.FFMPEG || 'ffmpeg', ['-loglevel', 'error', '-i', file, '-vf', `scale=${W}:${H}:flags=area`, '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'])
    let buf = Buffer.alloc(0), n = 0
    const bad = []
    let fps = 30
    const pr = spawn(process.env.FFPROBE || 'ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', file])
    pr.stdout.on('data', (d) => { const [a, b] = String(d).trim().split('/').map(Number); if (a && b) fps = a / b })
    let prevMag = 0
    p.stdout.on('data', (d) => {
      buf = Buffer.concat([buf, d])
      while (buf.length >= FR) {
        const f = buf.subarray(0, FR); buf = buf.subarray(FR)
        let pink = 0, mag = 0
        for (let i = 0; i < FR; i += 3) {
          const r = f[i], g = f[i + 1], b = f[i + 2]
          if (r > 150 && b > 110 && g < 0.7 * Math.min(r, b)) pink++
          if (r > 90 && b > 90 && g < 0.35 * Math.min(r, b)) mag++
        }
        const k = pink / (W * H), m = mag / (W * H)
        if (k > 0.25 || (m > 0.4 && m - prevMag > 0.3)) bad.push(n / fps)
        prevMag = m; n++
      }
    })
    p.on('close', (c) => c === 0 ? ok(bad) : fail(new Error('ffmpeg failed on ' + file)))
  })
}
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  let dirty = 0
  for (const f of process.argv.slice(2)) {
    const bad = await scanFile(f)
    if (bad.length) { dirty++; console.log(`PINK ${f}: ${bad.length} frame(s) at ${bad.slice(0, 12).map((t) => t.toFixed(2)).join(', ')} s`) } else console.log(`clean ${f}`)
  }
  process.exit(dirty ? 1 : 0)
}
