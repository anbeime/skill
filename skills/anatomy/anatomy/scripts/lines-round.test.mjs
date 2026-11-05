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

async function check(shape, path) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-lines-round-"));
  try {
    const page = join(directory, "figure.html");
    await writeFile(page, `<!doctype html><div class="iso-plate"><svg width="200" height="100" viewBox="0 0 200 100">${shape}<path class="iso-line" fill="none" stroke="black" d="${path}"/></svg></div>`);
    try {
      return { code: 0, ...await execute(process.execPath, [lines, page, "--wait", "0"], { timeout: 30000 }) };
    } catch (error) {
      return { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

test("line ends above a flat ellipse are floating", async () => {
  const result = await check('<ellipse cx="50" cy="50" rx="40" ry="5" fill="black"/>', "M30 30L50 30");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 2 of 2/);
});

test("line ends inside an unfilled circle are floating", async () => {
  const result = await check('<circle cx="50" cy="50" r="40" fill="none" stroke="black"/>', "M30 50L50 50");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 2 of 2/);
});

test("line ends on ellipse rims remain rooted", async () => {
  const result = await check('<ellipse cx="50" cy="50" rx="40" ry="5" fill="none" stroke="black"/>', "M10 50L90 50");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /line ends: 0/);
});

test("a nonuniformly scaled circle does not root nearby floating ends", async () => {
  const result = await check('<circle cx="25" cy="25" r="20" transform="scale(2,.25)" fill="black"/>', "M30 20L50 20");
  assert.equal(result.code, 1);
  assert.match(result.stdout, /line ends: 2 of 2/);
});

test("line ends inside a filled ellipse remain rooted", async () => {
  const result = await check('<ellipse cx="50" cy="50" rx="40" ry="5" fill="black"/>', "M30 50L50 50");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /line ends: 0/);
});
