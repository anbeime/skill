import assert from "node:assert/strict";
import test from "node:test";
import { turning } from "../kit/turn-build.mjs";
import { identity } from "./turn-fidelity.mjs";
const P = { origin: [0, 0], scale: 1, azimuth: 45, elevation: 30 };
const fixture = () => { const T = turning(P); T.layer("parts"); return T; };
const prism = (T, group) => T.prism({ name: "pointer", group, plan: { x: 0, y: 0, w: 4, d: 2, r: 0 }, z: 0, h: 1 });
test("missing named part groups cannot silently pass as static geometry", () => {
  const T = fixture(); T.group("dial", { turn: {} });
  assert.throws(() => { prism(T, "dail"); T.build(); identity(T, P, [0, 90]); }, /turning: unknown group dail/);
  assert.equal(T.parts.length, 0);
});
test("missing named parent groups cannot silently root nested motion", () => {
  const T = fixture(); T.group("dial", { turn: {} });
  assert.throws(() => T.group("slide", { parent: "dail", slide: { direction: [1, 0, 0], travel: 5 } }), /turning: unknown group dail/);
  assert.equal(T.groups.length, 1);
});
test("duplicate group names cannot alias incompatible motion values", () => {
  const T = fixture(); T.group("dial", { turn: {} });
  assert.throws(() => T.group("dial", { slide: { direction: [1, 0, 0], travel: 5 } }), /turning: duplicate group dial/);
  assert.equal(T.groups.length, 1);
});
test("existing named and object group references retain native fidelity", () => {
  for (const named of [false, true]) {
    const T = fixture(); const group = T.group("dial", { turn: {} });
    const part = prism(T, named ? "dial" : group);
    const child = T.group("slide", { parent: named ? "dial" : group, slide: { direction: [1, 0, 0], travel: 5 } });
    assert.equal(part.group, group); assert.equal(child.parent, group);
    T.build(); const result = identity(T, P, [0, 90]);
    assert.equal(result.pass, true);
    assert.match(result.text, /over [1-9]\d* faces/);
  }
});
test("omitted and explicit null groups keep supported static geometry", () => {
  for (const group of [undefined, null]) {
    const T = fixture(); const part = prism(T, group);
    assert.equal(part.group, null);
    T.build(); assert.equal(T.parts.length, 1);
  }
});
