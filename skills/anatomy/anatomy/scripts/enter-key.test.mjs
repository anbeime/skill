import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
async function run(kind, args) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-enter-key-"));
  try {
    const file = join(directory, "figure.html");
    await writeFile(file, `<!doctype html><div class="iso-plate" style="width:400px;height:180px"><button id="button" type="button" tabindex="0" onclick="window.clicked=(window.clicked||0)+1;document.querySelector('[data-readout]').textContent='activated'">Activate</button><form onsubmit="event.preventDefault();window.submitted=(window.submitted||0)+1"><input id="field" tabindex="0"></form><input id="range" type="range" value="5" min="0" max="10"><span data-readout>waiting</span></div>`);
    return await execute(process.execPath, ["scripts/" + kind + ".mjs", file, ...(kind === "capture" ? ["--out", join(directory, "shot.png"), "--wait", "0", "--key", args] : [JSON.stringify(args)])], { timeout: 30000 });
  } finally { await rm(directory, { recursive: true, force: true }); }
}
for (const code of [undefined, "NumpadEnter"])
  test(`drive Enter ${code || "default"} performs the native button action`, async () => {
    const result = await run("drive", [["key", "Enter", "#button", code], ["eval", "window.clicked||0"]]);
    assert.match(result.stdout, /eval: 1/);
  });
test("drive Enter performs native implicit form submission", async () => {
  const result = await run("drive", [["key", "Enter", "#field"], ["eval", "window.submitted||0"]]);
  assert.match(result.stdout, /eval: 1/);
});
test("capture Enter applies native activation before the screenshot", async () => {
  const result = await run("capture", "Enter");
  assert.match(result.stdout, /readout "activated"/);
});
test("drive preserves native Space, arrow and printable key behavior", async () => {
  const result = await run("drive", [["key", " ", "#button"], ["key", "ArrowRight", "#range"], ["key", "a", "#field"], ["eval", "({clicked:window.clicked||0,range:document.querySelector('#range').value,text:document.querySelector('#field').value})"]]);
  assert.match(result.stdout, /"clicked":1,"range":"6","text":"a"/);
});
test("capture preserves native Space activation", async () => {
  const result = await run("capture", "Space");
  assert.match(result.stdout, /readout "activated"/);
});
