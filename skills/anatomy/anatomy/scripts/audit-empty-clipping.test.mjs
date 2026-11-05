import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import { turning } from "../kit/turn-build.mjs";
const small='<rect x="2" y="2" width="2" height="2"/>';
const fixtures=[
  ["fully disjoint primitive",'<defs><clipPath id="cut"><rect width="10" height="10"/></clipPath></defs><rect x="20" y="20" width="10" height="10" clip-path="url(#cut)"/>'+small],
  ["nested disjoint clips",'<defs><clipPath id="one"><rect width="10" height="10"/></clipPath><clipPath id="two"><rect x="20" y="20" width="10" height="10"/></clipPath></defs><g clip-path="url(#one)"><g clip-path="url(#two)"><rect width="64" height="64"/></g></g>'+small],
  ["zero area clip",'<defs><clipPath id="cut"><rect width="0" height="10"/></clipPath></defs><rect width="64" height="64" clip-path="url(#cut)"/>'+small],
  ["empty declared clip",'<defs><clipPath id="cut"/></defs><rect width="64" height="64" clip-path="url(#cut)"/>'+small],
  ["ordinary intersecting clip",'<defs><clipPath id="cut"><rect x="2" y="2" width="4" height="4"/></clipPath></defs><rect width="64" height="64" clip-path="url(#cut)"/>'],
  ["ordinary visible primitives",small+'<rect x="10" y="10" width="4" height="4"/>'],
  ["fully invisible clipped drawing",'<defs><clipPath id="cut"><rect width="10" height="10"/></clipPath></defs><rect x="20" y="20" width="10" height="10" clip-path="url(#cut)"/>'],
];
let pixels;const directory=await mkdtemp(join(tmpdir(),"anatomy-empty-clipping-"));
try{
  const page=join(directory,"figure.html");await writeFile(page,'<!doctype html><div class="iso-plate"></div>');
  const expression=`(async()=>{const fixtures=${JSON.stringify(fixtures.map(([,m])=>m))};const result=[];for(const m of fixtures){const svg='<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'+m+'</svg>';const image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg)});const c=document.createElement('canvas');c.width=c.height=64;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);const data=ctx.getImageData(0,0,64,64).data;let box=null;for(let y=0;y<64;y++)for(let x=0;x<64;x++)if(data[(y*64+x)*4+3])box=box?[Math.min(box[0],x),Math.min(box[1],y),Math.max(box[2],x+1),Math.max(box[3],y+1)]:[x,y,x+1,y+1];result.push(box);}return result;})()`;
  const result=await promisify(execFile)(process.execPath,["scripts/drive.mjs",page,JSON.stringify([["eval",expression]])],{timeout:30000});pixels=JSON.parse(result.stdout.match(/eval: (.*)/)[1]);assert.equal(pixels.length,fixtures.length);
}finally{await rm(directory,{recursive:true,force:true});}
const P={origin:[0,0],scale:1,azimuth:45,elevation:30};
fixtures.forEach(([name,markup],i)=>test(`public clipped bounds match actual native SVG pixels for ${name}`,()=>{
  assert.deepEqual(A.markupBox(markup),pixels[i]);
  if(pixels[i]){const T=turning(P);T.layer("figure");const part=T.fixed({name:"fixed",svg:markup,anchor:[0,0,0],shapes:[A.ball([0,0,0],50)]});assert.deepEqual(part.spec.box,pixels[i].map((v,j)=>v+(j<2?-.5:.5)));}
}));
test("coverage accepts the true visible plane without an invisible clipped outlier",()=>{
  const cam=A.cameraBasis(P),F={o:[0,0,0],a:cam.V,u:cam.R,v:cam.D};
  const shape=A.prism(F,[[2,2],[4,2],[4,4],[2,4]].map(p=>p.map(v=>v/cam.k)),0,.01);
  assert.deepEqual(A.coverage([{name:"plane",svg:fixtures[0][1],shapes:[shape]}],P),[]);
});
test("clipped visible line bounds preserve their degenerate axis",()=>{
  assert.deepEqual(A.markupBox('<defs><clipPath id="cut"><rect width="10" height="10"/></clipPath></defs><line x1="4" y1="2" x2="4" y2="8" clip-path="url(#cut)"/>'),[4,2,4,8]);
});
