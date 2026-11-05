import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execute = promisify(execFile);
const capture = fileURLToPath(new URL("capture.mjs", import.meta.url));

test("capture creates nested output directories for initial and timed screenshots", async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-capture-"));
  try {
    const page = join(directory, "figure.html");
    const output = join(directory, "shots", "closeups", "figure.png");
    await writeFile(page, '<!doctype html><div class="iso-plate" style="width:200px;height:100px;background:papayawhip">Figure</div>');
    const result = await execute(process.execPath, [capture, page, "--out", output, "--wait", "0", "--times", "20", "--scale", "1"], { timeout: 30000 });
    assert.match(result.stdout, /console: clean/);
    for (const name of [output, output.replace(/\.png$/, "-20.png")]) {
      const png = await readFile(name);
      assert.deepEqual([...png.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10]);
      assert.ok(png.length > 100);
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("capture retains existing-directory output", async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-capture-"));
  try {
    const page = join(directory, "figure.html");
    const output = join(directory, "figure.png");
    await writeFile(page, '<!doctype html><div class="iso-plate" style="width:200px;height:100px;background:papayawhip">Figure</div>');
    await execute(process.execPath, [capture, page, "--out", output, "--wait", "0"], { timeout: 30000 });
    assert.ok((await readFile(output)).length > 100);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("capture rejects option values that would be ignored or break the clip", async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-capture-"));
  try {
    const page = join(directory, "figure.html");
    const output = join(directory, "figure.png");
    await writeFile(page, '<!doctype html><div class="iso-plate">Figure</div>');
    const cases = [["--zoom", "1,2", /--zoom needs x,y,w,h/], ["--zoom", "1,2,0,5", /--zoom needs x,y,w,h/], ["--hover", "0.5", /--hover needs fx,fy/], ["--times", "fast", /--times needs milliseconds/], ["--width", "wide", /--width needs a number above 0/], ["--scale", "0", /--scale needs a number above 0/], ["--wait", "abc", /--wait needs a number/], ["--theme", "sepia", /--theme must be dark or light/]];
    for (const [flag, value, message] of cases) {
      const error = await execute(process.execPath, [capture, page, "--out", output, flag, value], { timeout: 30000 }).then(() => null, (failure) => failure);
      assert.equal(error?.code, 1, `${flag} ${value}`);
      assert.match(error.stderr, message);
    }
    await assert.rejects(readFile(output));
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
