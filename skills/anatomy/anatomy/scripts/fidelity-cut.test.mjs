import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";
import { pathToFileURL } from "node:url";
import test from "node:test";
const execute = promisify(execFile);
async function run(kind, split = false, open = false, corrupt = null, options = {}) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-fidelity-cut-"));
  try {
    const file = join(directory, "fixture.mjs");
    const module = pathToFileURL(resolve("kit/turn-build.mjs")).href;
    const frameModule = pathToFileURL(resolve("kit/lathe.mjs")).href;
    const runtime = pathToFileURL(resolve("kit/turn.mjs")).href;
    const origin = options.origin ?? [0, 0, 0];
    const axis = options.axis ?? [0, 0, 1];
    const polygon = options.polygon ?? [[-2, -2], [2, -2], [2, 2], [-2, 2]];
    const cutPlane = options.cutPlane ?? { n: [0, 0, 1], d: 5 };
    await writeFile(file, `import {turning} from ${JSON.stringify(module)};import * as G from ${JSON.stringify(frameModule)};
export const P={origin:[0,0],scale:1,azimuth:45,elevation:30};export const T=turning(P);T.layer('parts');const group=T.group('assembly',{turn:{pivot:[5,2]}});const F=G.frameAlong(${JSON.stringify(origin)},${JSON.stringify(axis)});const base={name:'body',group,F,s0:0,s1:10};const part=${kind === "prism" ? `T.prism({...base,polygon:${JSON.stringify(polygon)}})` : `T.round({...base,r:2,fixed:false,ends:${open ? "['open','flat']" : "['flat','flat']"}})`};${split ? `T.split(part,${JSON.stringify(cutPlane)});` : ""}T.build();${corrupt ? `const {TURN}=await import(${JSON.stringify(runtime)});const emit=TURN.emit;TURN.emit=(run,cam,frame)=>{const f=emit(run,cam,frame);for(const role of ${JSON.stringify(corrupt === "edge" ? ["edge"] : corrupt === "fill" ? ["fill"] : ["fill", "edge"])})if(run.role[role]!==undefined)f.d[run.role[role]]=f.d[run.role[role]].replace(/-?\\d+(?:\\.\\d+)?/g,n=>String(Number(n)+20));return f;};` : ""}`);
    return await execute(process.execPath, ["scripts/turn-check.mjs", file, "--fidelity", "--angles", "0,45,90,180"], { timeout: 30000 });
  } finally { await rm(directory, { recursive: true, force: true }); }
}
function compared(stdout, kind) {
  if (kind === "prism") assert.ok(Number(stdout.match(/over (\d+) faces/)[1]) > 0);
  else {
    assert.ok(Number(stdout.match(/rounds: (\d+) frames/)[1]) > 0);
    assert.ok(Number(stdout.match(/of (\d+) interior cells/)[1]) > 0);
  }
}
for (const kind of ["prism", "round"]) test(`actual fidelity CLI accepts split ${kind} with intentionally unstroked cuts`, async () => {
  const result = await run(kind, true);
  assert.match(result.stdout, /fidelity passed/);
  compared(result.stdout, kind);
  if (kind === "prism") assert.match(result.stdout, /control .*fails as it should/);
});
test("actual fidelity CLI honors an unsplit open round end", async () => {
  const result = await run("round", false, true);
  assert.match(result.stdout, /fidelity passed/);
  compared(result.stdout, "round");
});
for (const kind of ["prism", "round"]) test(`actual fidelity CLI preserves an unsplit closed ${kind} control`, async () => {
  const result = await run(kind);
  assert.match(result.stdout, /fidelity passed/);
  compared(result.stdout, kind);
  if (kind === "prism") assert.match(result.stdout, /control .*fails as it should/);
});
for (const split of [false, true]) test(`actual fidelity CLI transforms upright frame prism (${split ? "split along axis" : "unsplit"})`, async () => {
  const result = await run("prism", split, false, null, { origin: [4, -3, 2], polygon: [[-3, -1], [3, -1], [3, 1], [-3, 1]], cutPlane: { n: [1, 0, 0], d: 4 } });
  assert.match(result.stdout, /fidelity passed/);
  compared(result.stdout, "prism");
  assert.match(result.stdout, /control .*fails as it should/);
});
test("actual fidelity CLI transforms upright frame prism with downward axis", async () => {
  const result = await run("prism", false, false, null, { origin: [4, -3, 12], axis: [0, 0, -1], polygon: [[-3, -1], [3, -1], [3, 1], [-3, 1]] });
  assert.match(result.stdout, /fidelity passed/);
  compared(result.stdout, "prism");
  assert.match(result.stdout, /control .*fails as it should/);
});
for (const kind of ["prism", "round"]) for (const split of [false, true]) for (const fault of (split ? ["edge", "geometry", "fill"] : ["edge", "geometry"]))
  test(`actual fidelity CLI detects ${fault} corruption of ${split ? "split" : "unsplit"} ${kind}`, async () => {
    await assert.rejects(run(kind, split, false, fault), (error) => {
      assert.equal(error.code, 1);
      assert.match(error.stdout, /(?:prisms|rounds) FAILED/);
      assert.match(error.stdout, /fidelity failed/);
      return true;
    });
  });
