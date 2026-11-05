import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import { turning } from "../kit/turn-build.mjs";
const P = { origin: [0, 0], scale: 1, azimuth: 45, elevation: 30 };
const fixtures = [
  ["rotated rectangle", '<rect width="10" height="10" transform="rotate(45)"/>'],
  ["rotated circle", '<circle r="10" transform="rotate(45)"/>'],
  ["rotated ellipse", '<ellipse rx="10" ry="2" transform="rotate(45)"/>'],
  ["nested affine ellipse", '<g transform="translate(10 5) scale(2 .5)"><ellipse cx="2" cy="3" rx="7" ry="2" transform="rotate(30)"/></g>'],
  ["horizontal skew", '<rect x="2" y="3" width="10" height="10" transform="skewX(45)"/>'],
  ["vertical skew", '<rect x="2" y="3" width="10" height="10" transform="skewY(-30)"/>'],
  ["ordinary rectangle", '<rect x="2" y="3" width="10" height="4"/>'],
  ["ordinary circle", '<circle cx="2" cy="3" r="4"/>'],
  ["ordinary transformed line", '<line x1="2" y1="3" x2="10" y2="7" transform="rotate(30)"/>'],
];
let native;
const directory = await mkdtemp(join(tmpdir(), "anatomy-affine-bounds-"));
try {
  const page = join(directory, "figure.html");
  await writeFile(page, `<!doctype html><div class="iso-plate"><svg width="400" height="400">${fixtures.map(([,markup],i)=>`<g id="fixture-${i}">${markup}</g>`).join("")}</svg></div>`);
  const expression = `Array.from({length:${fixtures.length}},(_,i)=>{const group=document.querySelector('#fixture-'+i),shape=group.querySelector('rect,circle,ellipse,line'),matrix=shape.getCTM(),points=[];if(shape.tagName==='rect'){const b=shape.getBBox();for(const [x,y] of [[b.x,b.y],[b.x+b.width,b.y],[b.x+b.width,b.y+b.height],[b.x,b.y+b.height]])points.push(new DOMPoint(x,y).matrixTransform(matrix));}else{const length=shape.getTotalLength();for(let j=0;j<=4096;j++)points.push(shape.getPointAtLength(length*j/4096).matrixTransform(matrix));}const b=group.getBBox();return{geometry:[Math.min(...points.map(p=>p.x)),Math.min(...points.map(p=>p.y)),Math.max(...points.map(p=>p.x)),Math.max(...points.map(p=>p.y))],groupBox:[b.x,b.y,b.x+b.width,b.y+b.height]}})`;
  const result = await promisify(execFile)(process.execPath, ["scripts/drive.mjs", page, JSON.stringify([["eval",expression]])], { timeout: 30000 });
  const observations = JSON.parse(result.stdout.match(/eval: (.*)/)[1]);
  console.log("native SVG group bounds:", JSON.stringify(observations.map(v=>v.groupBox)));
  native = observations.map(v=>v.geometry);
} finally { await rm(directory, { recursive: true, force: true }); }
fixtures.forEach(([name,markup],i)=>test(`public bounds and fixed parts match native SVG geometry for ${name}`,()=>{
  const expected = native[i];
  const observed = A.markupBox(markup);
  for(let j=0;j<4;j++)assert.ok(Math.abs(observed[j]-expected[j])<.002, `${name} bound ${j}: ${observed[j]} != ${expected[j]}`);
  const T = turning(P);T.layer("figure");
  const part = T.fixed({name:"authored",svg:markup,anchor:[0,0,0],shapes:[A.ball([0,0,0],20)]});
  for(let j=0;j<4;j++)assert.ok(Math.abs(part.spec.box[j]-(expected[j]+(j<2?-.5:.5)))<.002);
}));
test("coverage rejects a narrow stand-in for a rotated rectangle",()=>{
  const cam=A.cameraBasis(P);
  const end=cam.D.map(v=>v*Math.sqrt(200)/cam.k);
  const standIn=A.tube([[0,0,0],end],.15);
  const item={name:"plate",svg:fixtures[0][1],shapes:[standIn]};
  const result=A.coverage([item],P,{pad:0});
  assert.equal(result.length,1);assert.ok(result[0].share<.1);
  assert.equal(A.coverage([{...item,shapes:[A.ball([0,0,0],20)]}],P,{pad:0}).length,0);
});
test("transformed rectangular clips keep every corner",()=>{
  const clipped='<defs><clipPath id="cut"><rect width="10" height="10"/></clipPath></defs><g transform="rotate(45)" clip-path="url(#cut)"><rect x="-100" y="-100" width="200" height="200"/></g>';
  const observed=A.markupBox(clipped),root=Math.sqrt(50);
  for(const [i,v] of [-root,0,root,2*root].entries())assert.ok(Math.abs(observed[i]-v)<1e-8);
});
