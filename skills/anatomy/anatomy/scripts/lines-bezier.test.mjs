import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
for (const [name, path, x, y] of [
  ["quadratic then smooth cubic", "M20 60 Q40 20 60 60 S80 100 100 60", 72.5, 75],
  ["cubic then smooth quadratic", "M20 60 C30 20 50 20 60 60 T100 60", 80, 60],
  ["matching cubic continuation", "M20 60 C30 20 50 20 60 60 S80 100 100 60", 76.25, 90],
  ["matching quadratic continuation", "M20 60 Q40 20 60 60 T100 60", 80, 80],
]) test(`native SVG ${name} roots a line on the actual curve`, async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-bezier-control-"));
  try {
    const file = join(directory, "figure.html");
    await writeFile(file, `<!doctype html><div class="iso-plate"><svg width="140" height="120" viewBox="0 0 140 120"><path id="curve" fill="none" stroke="black" d="${path}"/><path class="iso-line" data-free="start" fill="none" stroke="black" d="M${x} 10L${x} ${y}"/></svg></div>`);
    const actions = JSON.stringify([["eval", `document.querySelector('#curve').isPointInStroke(new DOMPoint(${x},${y}))`], ["lines"]]);
    let result;
    try { result = { code: 0, ...await execute(process.execPath, ["scripts/drive.mjs", file, actions], { timeout: 30000 }) }; }
    catch (error) { result = { code: error.code, stdout: error.stdout, stderr: error.stderr }; }
    assert.match(result.stdout, /eval: true/);
    assert.equal(result.code, 0);
    assert.match(result.stdout, /line ends: 0 of 1/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
