import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execute = promisify(execFile);

async function drive(expression, action = "eval") {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-drive-test-"));
  try {
    const page = join(directory, "figure.html");
    const actions = join(directory, "actions.json");
    await writeFile(page, '<!doctype html><div class="iso-plate" tabindex="0">Owned figure</div>');
    await writeFile(actions, JSON.stringify([[action, expression, 200]]));
    try {
      return { code: 0, ...await execute(process.execPath, [fileURLToPath(new URL("drive.mjs", import.meta.url)), page, "--actions", actions], { timeout: 30000 }) };
    } catch (error) {
      return { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

test("drive fails when a browser assertion throws", async () => {
  const result = await drive("(()=>{throw new Error('drive assertion failed')})()");
  assert.equal(result.code, 1);
  assert.match(result.stderr, /drive assertion failed/);
  assert.doesNotMatch(result.stdout, /console: clean/);
});

test("drive fails when an awaited browser promise rejects", async () => {
  const result = await drive("Promise.reject(new Error('drive async assertion failed'))");
  assert.equal(result.code, 1);
  assert.match(result.stderr, /drive async assertion failed/);
});

test("drive preserves a successful JSON evaluation", async () => {
  const result = await drive("({checked: true})");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /eval: \{"checked":true\}/);
  assert.match(result.stdout, /console: clean/);
});

test("drive preserves a successful undefined evaluation", async () => {
  const result = await drive("void 0");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /eval: undefined/);
  assert.match(result.stdout, /console: clean/);
});

test("drive reports a browser evaluation syntax error", async () => {
  const result = await drive("(()");
  assert.equal(result.code, 1);
  assert.match(result.stderr, /SyntaxError/);
});

test("drive reports an assertion thrown while waiting for a condition", async () => {
  const result = await drive("(()=>{throw new Error('until assertion failed')})()", "until");
  assert.equal(result.code, 1);
  assert.match(result.stderr, /until assertion failed/);
});

test("drive accepts a condition that is already true however short the wait", async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-drive-test-"));
  try {
    const page = join(directory, "figure.html");
    const actions = join(directory, "actions.json");
    await writeFile(page, '<!doctype html><div class="iso-plate" tabindex="0">Owned figure</div>');
    await writeFile(actions, JSON.stringify([["until", "true", 1], ["until", "Promise.resolve(1)", 1]]));
    const result = await execute(process.execPath, [fileURLToPath(new URL("drive.mjs", import.meta.url)), page, "--actions", actions], { timeout: 30000 });
    assert.match(result.stdout, /console: clean/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("drive preserves a successful wait condition", async () => {
  const result = await drive("document.querySelector('.iso-plate') !== null", "until");
  assert.equal(result.code, 0);
  assert.match(result.stdout, /console: clean/);
});
