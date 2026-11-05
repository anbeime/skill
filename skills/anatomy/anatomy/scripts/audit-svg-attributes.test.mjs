import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import { turning } from "../kit/turn-build.mjs";
const P={origin:[0,0],scale:1,azimuth:45,elevation:30};
const fixtures=[
  ["single quoted rectangle", "<rect x='10' y='20' width='30' height='40'/>"],
  ["spaces around attribute equals", '<rect x = "10" y = "20" width = "30" height = "40"/>'],
  ["single quoted nested transform", "<g transform = 'translate(5 3)'><path d='M10 10L20 10L20 20Z'/></g>"],
  ["numeric XML path references", '<path d="M&#49;0 &#x32;0L40 20L40 60Z"/>'],
  ["numeric XML transform references", '<g transform="translate(&#49;0 5)"><circle cx="10" cy="10" r="5"/></g>'],
  ["mixed attribute quotes and multiline path", "<path d='M10 20\nL40 20L40 60Z' transform=\"translate(2 3)\"/>"],
  ["single quoted ellipse", "<ellipse cx='10' cy='20' rx='4' ry='2'/>"],
  ["quoted attribute text is not geometry", `<rect data-label="x='99'" x='10' y='20' width='30' height='40'/>`],
  ["quoted greater-than delimiter", `<rect data-label='a > b' x="10" y="20" width="30" height="40"/>`],
  ["quoted less-than delimiter", `<rect data-label="a &lt; b" x='10' y='20' width='30' height='40'/>`],
  ["ordinary double quoted rectangle", '<rect x="10" y="20" width="30" height="40"/>'],
  ["ordinary transformed circle", '<g transform="translate(2 3)"><circle cx="10" cy="10" r="5"/></g>'],
];
let native;const directory=await mkdtemp(join(tmpdir(),"anatomy-svg-attributes-"));
try{
  const page=join(directory,"figure.html");await writeFile(page,`<!doctype html><div class="iso-plate"><svg width="100" height="100">${fixtures.map(([,m],i)=>`<g id="f${i}">${m}</g>`).join("")}</svg></div>`);
  const expression=`Array.from({length:${fixtures.length}},(_,i)=>{const b=document.querySelector('#f'+i).getBBox();return[b.x,b.y,b.x+b.width,b.y+b.height]})`;
  const result=await promisify(execFile)(process.execPath,["scripts/drive.mjs",page,JSON.stringify([["eval",expression]])],{timeout:30000});native=JSON.parse(result.stdout.match(/eval: (.*)/)[1]);
}finally{await rm(directory,{recursive:true,force:true});}
fixtures.forEach(([name,markup],i)=>test(`public SVG bounds and fixed parts decode ${name}`,()=>{
  assert.deepEqual(A.markupBox(markup),native[i]);
  const T=turning(P);T.layer("figure");const part=T.fixed({name:"fixed",svg:markup,anchor:[0,0,0],shapes:[A.ball([0,0,0],50)]});
  assert.deepEqual(part.spec.box,native[i].map((v,j)=>v+(j<2?-.5:.5)));
}));
test("coverage rejects a stand-in for single quoted real geometry",()=>{
  const item={name:"quoted",svg:fixtures[0][1],shapes:[A.ball([0,0,0],.1)]};assert.equal(A.coverage([item],P).length,1);
  assert.equal(A.coverage([{...item,shapes:[A.ball([0,0,0],50)]}],P).length,0);
});
test("quoted and escaped clip identifiers retain authored clipping",()=>{
  const markup="<defs><clipPath id = 'cut&amp;1'><rect x='2' y='3' width='4' height='5'/></clipPath></defs><rect width='100' height='100' clip-path = 'url(#cut&amp;1)'/>";
  assert.deepEqual(A.markupBox(markup),[2,3,6,8]);
});
test("quoted halo class remains excluded from authored bounds",()=>{
  assert.deepEqual(A.markupBox("<circle class = 'iso-halo' cx='50' cy='50' r='40'/><rect x='2' y='3' width='4' height='5'/>"),[2,3,6,8]);
});
