import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import { markupBox } from "../kit/audit.mjs";

const execute = promisify(execFile);
for (const [name, markup] of [
  ["relative move after closing a subpath", '<path d="M10 10L20 10L20 20Z m5 0l2 0"/>'],
  ["transformed relative move after closing a subpath", '<g transform="translate(5 3)"><path d="M10 10L20 10L20 20Z m5 0l2 0"/></g>'],
  ["absolute move after closing a subpath", '<path d="M10 10L20 10L20 20Z M15 10L17 10"/>'],
  ["open relative segments", '<path d="M10 10l10 0l0 10m5 0l2 0"/>'],
]) test(`audit bounds match actual native SVG for ${name}`, async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-audit-path-origin-"));
  try {
    const page = join(directory, "figure.html");
    await writeFile(page, `<!doctype html><div class="iso-plate"><svg width="100" height="100" viewBox="0 0 100 100">${markup}</svg></div>`);
    const actions = JSON.stringify([["eval", "(()=>{const b=document.querySelector('svg').getBBox();return [b.x,b.y,b.x+b.width,b.y+b.height]})()"]]);
    const result = await execute(process.execPath, ["scripts/drive.mjs", page, actions], { timeout: 30000 });
    const native = JSON.parse(result.stdout.match(/eval: (.*)/)[1]);
    assert.deepEqual(markupBox(markup), native);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
