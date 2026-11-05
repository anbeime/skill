import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { access, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);

async function capture(selector, svgOnly = false, keys = false) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-capture-target-"));
  try {
    const page = join(directory, "figure.html");
    const out = join(directory, "capture.png");
    const content = svgOnly
      ? '<svg width="80" height="40" xmlns="http://www.w3.org/2000/svg"><rect width="80" height="40" fill="green"/></svg>'
      : `<div class="iso-plate" tabindex="0" id="first" style="width:100px;height:80px;background:blue"><span data-readout>first:0</span></div><div class="iso-plate" tabindex="0" id="second" style="width:60px;height:40px;background:red"><span data-readout>second:0</span></div><script>for(const plate of document.querySelectorAll('.iso-plate'))plate.addEventListener('keydown',e=>{if(e.key==='ArrowRight')plate.querySelector('[data-readout]').textContent=plate.id+':1'})</script>`;
    await writeFile(page, '<!doctype html><style>body{margin:20px}</style>' + content);
    const args = ["scripts/capture.mjs", page, "--out", out, "--wait", "0", "--scale", "1"];
    if (selector !== undefined) args.push("--select", selector);
    if (keys) args.push("--key", "ArrowRight");
    let result;
    try {
      result = { code: 0, ...await execute(process.execPath, args, { timeout: 30000 }) };
    } catch (error) {
      result = { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
    let png;
    try {
      await access(out);
      png = await readFile(out);
    } catch {}
    return { ...result, png };
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

function dimensions(png) {
  assert.ok(png);
  assert.equal(png.subarray(1, 4).toString(), "PNG");
  return [png.readUInt32BE(16), png.readUInt32BE(20)];
}

test("an absent explicit figure selector fails without an unrelated screenshot", async () => {
  const result = await capture("#removed-figure");
  assert.equal(result.code, 1);
  assert.match(result.stderr, /Capture target not found: #removed-figure/);
  assert.equal(result.png, undefined);
  assert.doesNotMatch(result.stdout, /saved /);
});

test("a malformed explicit selector retains an actionable capture diagnostic", async () => {
  const result = await capture("[invalid");
  assert.equal(result.code, 1);
  assert.match(result.stderr, /Capture target not found: \[invalid/);
  assert.equal(result.png, undefined);
});

test("a matching selector captures the requested second figure", async () => {
  const result = await capture("#second");
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual(dimensions(result.png), [72, 52]);
  assert.match(result.stdout, /60x40/);
});

test("default selection retains the first plate", async () => {
  const result = await capture(undefined);
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual(dimensions(result.png), [112, 92]);
  assert.match(result.stdout, /100x80/);
});

test("default selection retains the standalone SVG fallback", async () => {
  const result = await capture(undefined, true);
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual(dimensions(result.png), [92, 52]);
  assert.match(result.stdout, /80x40/);
});

test("an explicit target reports that figure's readout", async () => {
  const result = await capture("#second");
  assert.equal(result.code, 0, result.stderr);
  assert.match(result.stdout, /readout "second:0"/);
});

test("keyboard interaction reaches the explicitly selected figure", async () => {
  const result = await capture("#second", false, true);
  assert.equal(result.code, 0, result.stderr);
  assert.match(result.stdout, /readout "second:1"/);
  assert.deepEqual(dimensions(result.png), [72, 52]);
});

async function driveTarget(actions, standaloneLines = false) {
  const directory=await mkdtemp(join(tmpdir(),"anatomy-drive-target-"));
  try{
    const page=join(directory,"figure.html"),out=join(directory,"selected.png"),file=join(directory,"actions.json");
    const svg='<svg width="60" height="40" viewBox="0 0 60 40"><rect x="10" y="10" width="30" height="20" fill="none" stroke="black"/><path class="iso-line" d="M10 20L40 20" fill="none" stroke="black"/></svg>';
    await writeFile(page,`<!doctype html><style>body{margin:20px}</style><div class="iso-plate" id="first" tabindex="0" style="width:100px;height:80px"><span data-readout>first:0</span>${svg}</div><div class="iso-plate" id="second" tabindex="0" style="width:60px;height:40px"><span data-readout>second:0</span>${svg}</div><script>for(const el of document.querySelectorAll('.iso-plate'))el.addEventListener('keydown',event=>{if(event.key==='ArrowRight')el.querySelector('[data-readout]').textContent=el.id+':1'})</script>`);
    await writeFile(file,JSON.stringify(actions.map(action=>action.map(value=>value==='OUTPUT'?out:value))));
    const args=standaloneLines?["scripts/lines.mjs",page,"--select","#missing","--wait","0"]:["scripts/drive.mjs",page,"--actions",file];
    let result;try{result={code:0,...await execute(process.execPath,args,{timeout:30000})};}catch(error){result={code:error.code,stdout:error.stdout,stderr:error.stderr};}
    let png;try{png=await readFile(out);}catch{}return{...result,png};
  }finally{await rm(directory,{recursive:true,force:true});}
}
for(const [name,action] of [
  ["shot",["shot","OUTPUT","#missing"]],
  ["move",["move","#missing",.5,.5]],
  ["click",["click","#missing"]],
  ["drag",["drag","#missing",0,0,1,1]],
  ["scroll",["scroll","#missing"]],
  ["key",["key","ArrowRight","#missing"]],
  ["lines",["lines",null,"#missing"]],
])test(`drive ${name} rejects an absent explicit target instead of continuing`,async()=>{
  const result=await driveTarget([action,["eval","'after missing target'"]]);assert.equal(result.code,1,result.stdout);assert.match(result.stderr,/(Drive|Line) target not found: #missing/);assert.doesNotMatch(result.stdout,/after missing target/);assert.equal(result.png,undefined);
});
test("standalone lines rejects an absent selected figure",async()=>{
  const result=await driveTarget([],true);assert.equal(result.code,1,result.stdout);assert.match(result.stderr,/Line target not found: #missing/);
});
test("drive targets the requested figure for keyboard input screenshot and reported readout",async()=>{
  const result=await driveTarget([["key","ArrowRight","#second"],["shot","OUTPUT","#second"],["eval","document.querySelector('#first [data-readout]').textContent"]]);
  assert.equal(result.code,0,result.stderr);assert.match(result.stdout,/readout "second:1"/);assert.match(result.stdout,/eval: "first:0"/);assert.deepEqual(dimensions(result.png),[68,48]);
});
test("drive defaults preserve first-figure keyboard focus and reporting",async()=>{
  const result=await driveTarget([["key","ArrowRight"],["shot","OUTPUT"],["eval","document.querySelector('#second [data-readout]').textContent"]]);
  assert.equal(result.code,0,result.stderr);assert.match(result.stdout,/readout "first:1"/);assert.match(result.stdout,/eval: "second:0"/);assert.deepEqual(dimensions(result.png),[108,88]);
});
test("line selection preserves real rooted-line checks on the requested SVG",async()=>{
  const result=await driveTarget([["lines",null,"#second svg"]]);assert.equal(result.code,0,result.stderr);assert.match(result.stdout,/line ends: 0 of [1-9]\d* ends on [1-9]\d* lines float/);
});
