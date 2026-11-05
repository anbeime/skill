import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { inflateSync } from "node:zlib";
import test from "node:test";

const execute = promisify(execFile);

function pngOf(bytes) {
  assert.equal(bytes.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  const width = bytes.readUInt32BE(16), height = bytes.readUInt32BE(20);
  assert.equal(bytes[24], 8);
  assert.ok([2, 6].includes(bytes[25]));
  const channels = bytes[25] === 2 ? 3 : 4, chunks = [];
  for (let at = 8; at < bytes.length;) {
    const length = bytes.readUInt32BE(at);
    if (bytes.subarray(at + 4, at + 8).toString() === "IDAT") chunks.push(bytes.subarray(at + 8, at + 8 + length));
    at += length + 12;
  }
  const raw = inflateSync(Buffer.concat(chunks)), stride = width * channels;
  assert.equal(raw.length, height * (stride + 1));
  const image = Buffer.alloc(height * stride);
  const paeth = (a, b, c) => {
    const p = a + b - c, da = Math.abs(p - a), db = Math.abs(p - b), dc = Math.abs(p - c);
    return da <= db && da <= dc ? a : db <= dc ? b : c;
  };
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    assert.ok(filter <= 4);
    for (let x = 0; x < stride; x++) {
      const left = x >= channels ? image[y * stride + x - channels] : 0;
      const up = y ? image[(y - 1) * stride + x] : 0;
      const corner = y && x >= channels ? image[(y - 1) * stride + x - channels] : 0;
      const predictor = [0, left, up, Math.floor((left + up) / 2), paeth(left, up, corner)][filter];
      image[y * stride + x] = (raw[y * (stride + 1) + x + 1] + predictor) & 255;
    }
  }
  return { width, height, center: [...image.subarray((Math.floor(height / 2) * width + Math.floor(width / 2)) * channels, (Math.floor(height / 2) * width + Math.floor(width / 2)) * channels + 3)] };
}

async function capture(mode, interaction, timed = false, zoom = false) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-current-crop-"));
  try {
    const page = join(directory, "figure.html"), output = join(directory, "capture.png");
    const change = mode === "resize" ? 'plate.style.width="180px";plate.style.height="120px";' : mode === "move" ? 'plate.style.transform="translate(200px,120px)";' : "";
    await writeFile(page, `<!doctype html><style>body{margin:20px;background:white}.iso-plate{position:relative;width:100px;height:80px;background:#ff0000}[data-readout]{position:absolute;left:0;top:-18px;white-space:nowrap}</style><div class="iso-plate" tabindex="0"><span data-readout></span></div><script>const plate=document.querySelector('.iso-plate');function report(){const r=plate.getBoundingClientRect();plate.querySelector('[data-readout]').textContent='native bounds '+r.width+'x'+r.height+' at '+r.left+','+r.top}function change(){${change}report()}report();plate.addEventListener(${JSON.stringify(interaction === "hover" ? "mouseenter" : "keydown")},event=>{event.preventDefault();${timed ? "setTimeout(change,3000)" : "change()"}},{once:true});</script>`);
    const args = ["scripts/capture.mjs", page, "--out", output, "--wait", "0", "--scale", "1"];
    if (interaction === "hover") args.push("--hover", "0.5,0.5");
    if (interaction === "key") args.push("--key", "ArrowRight");
    if (timed) args.push("--times", "2500");
    if (zoom) args.push("--zoom", "20,20,40,30", "--zoom-scale", "1");
    const result = await execute(process.execPath, args, { timeout: 30000 });
    const png = pngOf(await readFile(timed ? output.replace(/\.png$/, "-2500.png") : output));
    return { ...result, png };
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

for (const [name, mode, interaction, timed, zoom, size, bounds] of [
  ["keyboard resize crops the actual enlarged figure", "resize", "key", false, false, [192, 132], "180x120"],
  ["pointer resize crops the actual enlarged figure", "resize", "hover", false, false, [192, 132], "180x120"],
  ["keyboard movement follows the current figure position", "move", "key", false, false, [112, 92], "100x80 at 220,140"],
  ["timed resize recomputes the later crop", "resize", "key", true, false, [192, 132], "180x120"],
  ["timed movement follows the later figure position", "move", "key", true, false, [112, 92], "100x80 at 220,140"],
  ["relative zoom moves with the interacted figure", "move", "key", false, true, [40, 30], "100x80 at 220,140"],
  ["static figure retains its original crop", "static", null, false, false, [112, 92], "100x80"],
  ["static relative zoom retains its original crop", "static", null, false, true, [40, 30], "100x80"],
]) test(name, async () => {
  const result = await capture(mode, interaction, timed, zoom);
  assert.ok(result.stdout.includes("native bounds " + bounds), result.stdout);
  assert.deepEqual([result.png.width, result.png.height], size);
  assert.deepEqual(result.png.center, [255, 0, 0]);
  assert.match(result.stdout, /console: clean/);
});
