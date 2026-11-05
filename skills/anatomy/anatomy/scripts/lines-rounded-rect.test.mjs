import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
for (const [name, attributes, x, y, rooted, transform = ""] of [
  ["rounded cutaway rejects square-corner attachment", 'width="100" height="80" rx="30"', 0, 0, false],
  ["rounded curve accepts its native attachment", 'width="100" height="80" rx="30"', 8.78679656440357, 8.786796564403573, true],
  ["elliptical corner accepts its native attachment", 'width="100" height="80" rx="30" ry="10"', 4.019237886466836, 5, true],
  ["missing horizontal radius follows vertical radius", 'width="100" height="80" ry="20"', 5.857864376269049, 5.857864376269051, true],
  ["oversized radii clamp independently", 'width="100" height="80" rx="200" ry="200"', 14.644660940672622, 11.715728752538102, true],
  ["affine corner preserves transformed attachment", 'width="100" height="80" rx="30"', 8.78679656440357, 8.786796564403573, true, "matrix(2 .2 .4 1 50 50)"],
  ["ordinary square retains its original attachment", 'width="100" height="80"', 0, 0, true],
  ["explicit zero radius remains square", 'width="100" height="80" rx="0" ry="30"', 0, 0, true],
]) test(name, async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-rounded-rect-lines-"));
  try {
    const file = join(directory, "figure.html");
    await writeFile(file, `<!doctype html><div class="iso-plate"><svg width="360" height="300" viewBox="0 0 360 300"><g transform="${transform}"><rect id="outline" x="0" y="0" ${attributes} fill="none" stroke="black"/><path class="iso-line" data-free="start" fill="none" stroke="black" d="M${x} -20 L${x} ${y}"/></g></svg></div>`);
    const actions = JSON.stringify([["eval", `document.querySelector('#outline').isPointInStroke(new DOMPoint(${x},${y}))`], ["lines"]]);
    let result;
    try { result = { code: 0, ...await execute(process.execPath, ["scripts/drive.mjs", file, actions], { timeout: 30000 }) }; }
    catch (error) { result = { code: error.code, stdout: error.stdout, stderr: error.stderr }; }
    assert.match(result.stdout, new RegExp(`eval: ${rooted}`));
    assert.equal(result.code, rooted ? 0 : 1, result.stderr);
    assert.match(result.stdout, new RegExp(`line ends: ${rooted ? 0 : 1} of 1`));
  } finally { await rm(directory, { recursive: true, force: true }); }
});
