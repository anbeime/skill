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

async function check(arc, line) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-lines-arcs-"));
  try {
    const page = join(directory, "figure.html");
    await writeFile(page, `<!doctype html><div class="iso-plate"><svg width="200" height="100" viewBox="0 0 200 100"><path fill="none" stroke="black" d="${arc}"/><path class="iso-line" fill="none" stroke="black" d="${line}"/></svg></div>`);
    try {
      return { code: 0, ...await execute(process.execPath, [lines, page, "--wait", "0"], { timeout: 30000 }) };
    } catch (error) {
      return { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

test("the empty chord of an arc does not root a line", async () => {
  const result = await check("M20 50A30 30 0 0 1 80 50", "M50 50L50 70");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 2 of 2/);
});

test("the actual middle of an arc roots a line", async () => {
  const result = await check("M20 50A30 30 0 0 1 80 50", "M50 20L50 0");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 1 of 2/);
});

test("relative arcs retain their endpoint and curvature", async () => {
  const result = await check("M20 50a30 30 0 0 1 60 0", "M50 20L50 0");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 1 of 2/);
});

test("arc endpoints preserve fully rooted lines", async () => {
  const result = await check("M20 50A30 30 0 0 1 80 50", "M20 50L80 50");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /line ends: 0/);
});
