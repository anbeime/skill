import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";
import { pathToFileURL } from "node:url";
import test from "node:test";
const execute = promisify(execFile);
async function run(mode = "healthy", role = "body", caps = true) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-fidelity-tube-"));
  try {
    const file = join(directory, "fixture.mjs");
    const build = pathToFileURL(resolve("kit/turn-build.mjs")).href;
    const runtime = pathToFileURL(resolve("kit/turn.mjs")).href;
    await writeFile(file, `import {turning} from ${JSON.stringify(build)};import {TURN} from ${JSON.stringify(runtime)};
export const P={origin:[0,0],scale:1,azimuth:45,elevation:30};export const T=turning(P);T.layer('parts');const group=T.group('assembly',{turn:{pivot:[5,2]}});T.tube({name:'route',group,route:[[0,0,0],[0,0,10]],r:1,chunk:20,caps:${caps}});T.build();
const emit=TURN.emit;TURN.emit=(run,cam,frame)=>{const f=emit(run,cam,frame);if(run.kind==='tube'&&${JSON.stringify(mode)}!=='healthy'){const index=run.role[${JSON.stringify(role)}];if(index!==undefined)f.d[index]=f.d[index].replace(/M([^M]*)/g,(all,body)=>{const nums=(body.match(/-?\\d+(?:\\.\\d+)?/g)??[]).map(Number);const mode=${JSON.stringify(mode)};if(mode==='empty')return'M';if(mode==='single')return'M'+nums.slice(0,2).join(' ');if(mode==='partial')return'M'+[0,2,4].map(i=>nums.slice(i,i+2).join(' ')).join('L')+(/Z\\s*$/.test(body)?'Z':'');if(mode==='offset')return all.replace(/-?\\d+(?:\\.\\d+)?/g,n=>String(Number(n)+20));const pts=[];for(let i=0;i<nums.length;i+=2){if(i)pts.push([(nums[i-2]+nums[i])/2,(nums[i-1]+nums[i+1])/2]);pts.push([nums[i],nums[i+1]]);}return'M'+pts.map(p=>p.join(' ')).join('L')+(/Z\\s*$/.test(body)?'Z':'');});}return f;};`);
    return await execute(process.execPath, ["scripts/turn-check.mjs", file, "--fidelity", "--angles", "0,45,90,180"], { timeout: 30000 });
  } finally { await rm(directory, { recursive: true, force: true }); }
}
for (const role of ["body", "edges"]) for (const mode of ["empty", "single", "partial"]) test(`native fidelity rejects ${mode} ${role} path coverage`, async () => {
  await assert.rejects(run(mode, role), (error) => {
    assert.equal(error.code, 1);
    assert.match(error.stdout, /tubes FAILED/);
    assert.match(error.stdout, /fidelity failed/);
    return true;
  });
});
for (const caps of [true, false]) test(`native fidelity preserves a healthy ${caps ? "capped" : "open"} tube`, async () => {
  const result = await run("healthy", "body", caps);
  assert.match(result.stdout, /tubes: [1-9]\d* chunk frames at 4 angles/);
  assert.match(result.stdout, /fidelity passed/);
});
for (const role of ["body", "edges"]) test(`native fidelity permits equivalent ${role} resampling`, async () => {
  assert.match((await run("resample", role)).stdout, /fidelity passed/);
});
test("native fidelity continues rejecting displaced tube geometry", async () => {
  await assert.rejects(run("offset"), (error) => error.code === 1 && /tubes FAILED/.test(error.stdout));
});
