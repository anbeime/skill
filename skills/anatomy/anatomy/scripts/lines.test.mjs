import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execute = promisify(execFile);
const lines = fileURLToPath(new URL("lines.mjs", import.meta.url));

async function check(path) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-lines-"));
  try {
    const page = join(directory, "figure.html");
    await writeFile(page, `<!doctype html><svg id="figure" width="200" height="100" viewBox="0 0 200 100"><path class="iso-line" fill="none" stroke="black" d="${path}"/></svg>`);
    try {
      return { code: 0, ...await execute(process.execPath, [lines, page, "--select", "#figure", "--wait", "0"], { timeout: 30000 }) };
    } catch (error) {
      return { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

test("a selected SVG checks its own floating lines", async () => {
  const result = await check("M20 20L180 20");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 2 of 2 ends on 1 lines float/);
});

test("a selected SVG preserves closed-path exemption", async () => {
  const result = await check("M20 20L180 20L180 80L20 80Z");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /line ends: 0/);
});
