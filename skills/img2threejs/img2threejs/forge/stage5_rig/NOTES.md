# Milestone 0 findings that don't belong in the gate report

These are things discovered while building the Milestone 0 rig emitter
(`forge/stage5_rig/`) that are true regardless of Milestone 0's pass/fail
result, and that matter to whoever does rig *integration* later. Read-only
findings — nothing here changes any file outside `forge/stage5_rig/` or
`forge/tests/test_rig_milestone0.py`.

## `THREE.CapsuleGeometry`'s raw seam is a real defect; the "66 non-manifold after weld" figure was not

> **CORRECTED 2026-07-30 (credit: worker-flatten).** The paragraph below
> originally claimed that even a "correct" weld of `THREE.CapsuleGeometry`
> left 66 non-manifold edges, and used that to argue the primitive needed a
> hand-built replacement rather than a better weld. That specific claim was
> wrong — it was a measurement artifact of `BufferGeometryUtils.mergeVertices`,
> not a real topology defect. I reproduced worker-flatten's finding
> independently (see below) before editing this file, rather than taking the
> correction on faith. The **raw boundary-edge finding (194 edges) is still
> real and still verified** — only the "non-manifold after weld" half of the
> story was wrong.

**What's actually true, verified directly:** the exact capsule call the
pipeline used to emit (`new THREE.CapsuleGeometry(0.35, 0.7, 16, 32)`, from
`CAPSULE_CAP_SEGMENTS = 16` / `CAPSULE_RADIAL_SEGMENTS = 32` — see "Update on
the real pipeline" below for what's changed since) has a genuine UV-seam
defect in its raw, unwelded form:

| Method | vertices | triangles | boundary edges | non-manifold edges |
|---|---|---|---|---|
| as-is, unwelded | 2178 | 4160 | **194** | 0 |
| position-only + `BufferGeometryUtils.mergeVertices(geometry, 1e-5)` | 2050 | 4160 | 0 | 66 *(artifact — see below)* |
| position-key dedup + **drop degenerate triangles** (no `mergeVertices`) | 2050 | 4096 (64 dropped) | 0 | **0** |

**Root cause of the "66" artifact:** `mergeVertices` re-indexes vertices by
position but does not drop triangles that become degenerate (two or more
corners collapsed to the same vertex) after that re-indexing. A degenerate
triangle `(a, a, b)` contributes the undirected edge `(a, b)` to the tally
**twice**, silently turning a legitimate 2-incidence (ordinary, non-manifold)
edge into an apparent 4 — which a naive `count > 2` check flags as
non-manifold even though the actual geometry, once the degenerate triangles
are also dropped, is a perfectly ordinary closed 2-manifold. There are
exactly 64 such degenerate triangles for this configuration — the "64
dropped" figure in the corrected row above, which I measured myself and
which matches worker-flatten's number exactly. This is
stable across weld tolerances from `1e-4` down to `1e-10` (ruling out a
tolerance-size explanation), and matches independently between two different
implementations (mine, replicated here; worker-flatten's, done separately in
`generate_threejs_factory.py`'s context) with the exact same numbers.

**So the raw-boundary finding (194 edges) stands, but the conclusion drawn
from it does not fully stand:** `THREE.CapsuleGeometry` is fixable with an
ordinary weld — it just needs a weld that also drops degenerate triangles,
which `mergeVertices` alone does not do. A hand-built watertight primitive
(what Milestone 0 uses; see below) is *a* valid fix, but it was not, as I
originally implied, the *only* practical one.

**Correction to my prior report to team-lead (kept for the record, still
accurate on its own terms):** I previously wrote that
`createRiggedDragon.ts:422-432`'s position-only `rawGeometry` strip-then-merge
pattern exists "exactly because" of the UV-seam attribute-matching problem
below. That was an inference from reading the code's *shape*, not something
the code itself states, and team-lead is right that it postdates a different
purpose (copying vertices out of a `MarchingCubes` result before a
scale/translate). What IS independently verified, not inferred, is that
`mergeVertices` only merges vertices where **every** attribute matches within
tolerance — I confirmed this by running `mergeVertices` on the *untouched*
geometry (all attributes intact) and getting the same 194 boundary edges, no
change, versus a real change once stripped to position-only. Whether the
dragon file's author had that same reasoning in mind is not established
either way.

**Reproduce (all three rows above, in one run):**
```bash
cd img2threejs-showcase
node --input-type=module -e "
import * as THREE from 'three';
import { mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
function edgeStats(idxArr, triCount) {
  const edges = new Map();
  for (let o = 0; o < triCount; o++) {
    const tri = [idxArr[o*3], idxArr[o*3+1], idxArr[o*3+2]];
    for (let e = 0; e < 3; e++) {
      const u = tri[e], v = tri[(e+1)%3];
      const k = u < v ? u+':'+v : v+':'+u;
      edges.set(k, (edges.get(k) ?? 0) + 1);
    }
  }
  return { boundary: [...edges.values()].filter(c=>c===1).length, nonManifold: [...edges.values()].filter(c=>c>2).length };
}
const raw = new THREE.CapsuleGeometry(0.35, 0.7, 16, 32);
console.log('raw:', edgeStats(raw.index.array, raw.index.count/3));
const posOnly = new THREE.BufferGeometry();
posOnly.setAttribute('position', raw.getAttribute('position').clone());
posOnly.setIndex(raw.index.clone());
const merged = mergeVertices(posOnly, 1e-5);
console.log('mergeVertices (artifact):', edgeStats(merged.index.array, merged.index.count/3));
const pos = raw.getAttribute('position');
const keyOf = (i) => Math.round(pos.getX(i)*1e5)+':'+Math.round(pos.getY(i)*1e5)+':'+Math.round(pos.getZ(i)*1e5);
const remap = new Int32Array(pos.count); const seen = new Map(); let next = 0;
for (let i = 0; i < pos.count; i++) { const k = keyOf(i); if (!seen.has(k)) seen.set(k, next++); remap[i] = seen.get(k); }
let dropped = 0; const kept = [];
for (let o = 0; o < raw.index.count/3; o++) {
  const a = remap[raw.index.array[o*3]], b = remap[raw.index.array[o*3+1]], c = remap[raw.index.array[o*3+2]];
  if (a===b||b===c||a===c) { dropped++; continue; }
  kept.push(a,b,c);
}
console.log('dedup + drop-degenerate (correct):', edgeStats(kept, kept.length/3), 'dropped', dropped);
"
```

**What Milestone 0 uses, and why it's still a reasonable choice even though
`THREE.CapsuleGeometry` turned out to be fixable:**
`forge/stage5_rig/emit_rig.py`'s `buildWatertightCapsule()` builds its own
grid from scratch — pole vertices shared once (not duplicated per fan
triangle), radial index taken `mod radialSegments` so the seam column never
exists as separate vertices in the first place. That's watertight by
construction rather than by a weld step (0 boundary / 0 non-manifold at every
configuration tried, no tolerance parameter to get wrong), which is still a
simpler property to depend on for a kill test than "call `mergeVertices`,
then remember it needs a degenerate-triangle-dropping pass too, on top of
being position-only." It is not a drop-in replacement for
`THREE.CapsuleGeometry` as used generally by the pipeline (arbitrary
placement/orientation via `component.geometryDescriptor`), and I have not
attempted to make it one.

**Update on the real pipeline:** at the time this was first written,
`generate_threejs_factory.py:1025` emitted the raw, unwelded
`THREE.CapsuleGeometry` call directly, so the 194-boundary-edge defect was
live in real output. `worker-flatten` has since ported an adapted copy of
`buildWatertightCapsule` into `generate_threejs_factory.py` for the general
"capsule" primitive (see `forge/tests/test_primitive_watertightness.py`), so
that specific defect is fixed in the real pipeline as of this writing — this
section is now a historical record of the investigation, not an open
blocker. Decision on keeping two independently-verified copies of the
builder (mine here, worker-flatten's in the factory) rather than a shared
runtime module: see the message thread with worker-flatten, 2026-07-30 —
`stage5_rig` is deliberately standalone until WS-C integration, and the two
copies have legitimate purpose-specific differences (UV attribute, normals
timing).

## Gate (b) needs the mesh to actually carry geometry near the joint

Documented in the gate report proper (message to team-lead), not repeated
here in full: the first version of `buildWatertightCapsule()` had exactly one
quad band for the whole cylindrical shaft, so no vertex existed anywhere near
an interior joint's pivot. Fixed by adding `heightSegments`, derived from the
smallest envelope radius in play (`RING_RESOLUTION_DIVISOR = 3.0` rings per
radius) rather than a hardcoded ring count, so resolution scales if the
capsule or the bone spacing changes.
