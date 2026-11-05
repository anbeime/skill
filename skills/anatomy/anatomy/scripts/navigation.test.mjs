import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execute = promisify(execFile);

async function run(name, kind) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-navigation-"));
  try {
    let target = join(directory, "figure.html");
    if (kind === "valid") await writeFile(target, '<!doctype html><div class="iso-plate" style="width:100px;height:100px">Figure</div>');
    if (kind === "refused") {
      const server = createServer();
      await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
      target = `http://127.0.0.1:${server.address().port}/`;
      await new Promise((resolve) => server.close(resolve));
    }
    const args = [fileURLToPath(new URL(`${name}.mjs`, import.meta.url)), target, ...(name === "capture" ? ["--out", join(directory, "shot.png"), "--wait", "0"] : ["[]"])];
    try {
      return { code: 0, ...await execute(process.execPath, args, { timeout: 30000 }) };
    } catch (error) {
      return { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

for (const name of ["capture", "drive"]) {
  test(`${name} fails a missing local page`, async () => {
    const result = await run(name, "missing");
    assert.equal(result.code, 1);
    assert.match(result.stderr, /Navigation failed.*ERR_FILE_NOT_FOUND/);
    assert.doesNotMatch(result.stdout, /console: clean/);
  });

  test(`${name} fails refused HTTP navigation`, async () => {
    const result = await run(name, "refused");
    assert.equal(result.code, 1);
    assert.match(result.stderr, /Navigation failed.*ERR_CONNECTION_REFUSED/);
    assert.doesNotMatch(result.stdout, /console: clean/);
  });

  test(`${name} preserves successful local navigation`, async () => {
    const result = await run(name, "valid");
    assert.equal(result.code, 0);
    assert.match(result.stdout, /console: clean/);
  });
}
