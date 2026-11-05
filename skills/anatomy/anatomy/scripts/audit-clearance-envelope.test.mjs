import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";
const route = (x, r, name) => A.tube([[x, 0, 0], [x, 0, 200]], r, { name, owner: name });
const run = (tubes, solids, options = {}) => A.clearances(tubes, solids, { spacing: 10, mounts: new Map(), ...options });
test("large pipe detects the required clearance to a real solid", () => {
  const tube = route(0,20,"pipe"),solid = A.ball([29,0,100],1,{name:"solid"});
  assert.equal(A.sdf(solid,[20,0,100]),8);
  const result = run([tube],[solid]);
  assert.equal(result.length,1);assert.equal(result[0].kind,"close");assert.equal(result[0].need,10);assert.ok(Math.abs(result[0].clearance-8)<1e-8);
});
test("large parallel pipes detect required clearance in either order", () => {
  const tubes = [route(0,20,"first"),route(48,20,"second")];
  for(const input of [tubes,[...tubes].reverse()]){
    const result = run(input,[]);assert.equal(result.length,1);assert.equal(result[0].need,10);assert.equal(result[0].clearance,8);
  }
});
test("explicit least clearance also controls both broad phases", () => {
  const tube=route(0,1,"pipe"),solid=A.ball([10,0,100],1,{name:"solid"});
  assert.equal(run([tube],[solid],{least:10})[0]?.clearance,8);
  assert.equal(run([tube,route(10,1,"other")],[],{least:10})[0]?.clearance,8);
});
test("posed pipes retain their authored required clearance", () => {
  const tube={...route(0,20,"pipe"),move:[5,0,0],ride:"pipe"};
  const solid=A.ball([34,0,100],1,{name:"solid"});
  const result=run([tube],[solid],{state:{shares:{pipe:1},label:"apart"}});
  assert.equal(result.length,1);assert.equal(result[0].clearance,8);assert.equal(result[0].state,"apart");
});
test("healthy gaps, explicit smaller clearance and touch exemptions remain accepted", () => {
  const tube=route(0,20,"pipe");
  assert.equal(run([tube],[A.ball([32,0,100],1,{name:"solid"})]).length,0);
  assert.equal(run([tube],[A.ball([29,0,100],1,{name:"solid"})],{ratio:.1}).length,0);
  assert.equal(run([{...tube,touch:["solid"]}],[A.ball([29,0,100],1,{name:"solid"})]).length,0);
  assert.equal(run([tube,route(51,20,"other")],[]).length,0);
});
test("existing small penetrating and separated pipes keep their results", () => {
  assert.equal(run([route(0,1,"first"),route(1.5,1,"second")],[])[0]?.kind,"through");
  assert.equal(run([route(0,1,"first"),route(4,1,"second")],[]).length,0);
});
