"""PLAN_1.5 WS-C slice 1 — the emitted bone hierarchy, measured on executed geometry.

The load-bearing test is `test_bone_world_positions_round_trip_to_the_spec_joints`. The spec
stores `jointPos` in MODEL space and a `THREE.Bone`'s position is PARENT-LOCAL, so the emitter
subtracts the parent's joint. If that conversion is wrong in any frame, accumulating the offsets
back down the chain lands somewhere else — and nothing else in the suite would notice, because
the code would still compile and still produce sixteen correctly-named bones.

`test_pivot_track_emits_no_rig` guards the other half of PLAN_1.5 §8: the pivot track is "not
replaced", so an `object` spec must come out of the generator with no bone code at all.

Pure Python 3.10+ stdlib. No pip installs.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_FORGE = _TESTS.parent
for path in (_TESTS, _FORGE, _FORGE / "stage2_spec", _FORGE / "stage3_build"):
    sys.path.insert(0, str(path))

try:
    from .showcase_test_support import showcase_root
except ImportError:
    from showcase_test_support import showcase_root

from generate_threejs_factory import (  # noqa: E402
    _posed_bone_rotations,
    generate,
    rig_is_bone_track,
)


class RigHierarchyEmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = showcase_root()          # skips with an actionable message when unset
        out = Path(tempfile.mkdtemp()) / "chr.json"
        subprocess.run(
            [sys.executable, str(_FORGE / "stage2_spec" / "new_sculpt_spec.py"),
             "Rig Probe", "--character", "--out", str(out)],
            capture_output=True, text=True, check=True,
        )
        cls.spec = json.loads(out.read_text())
        cls.generated = generate(cls.spec, "blockout")

    def test_character_spec_is_on_the_bone_track(self) -> None:
        self.assertTrue(rig_is_bone_track(self.spec))

    def test_pivot_track_emits_no_rig(self) -> None:
        """PLAN_1.5 §8: the pivot track is not replaced, so an object spec gets no bone code.

        This generates a REAL object spec rather than flipping `primaryDomain` on the character
        one. Doing that by hand is rejected outright — `validate_sculpt_spec` cross-checks
        `pipelineRouting.track` against `primaryDomain` ("character-v1.5 routing requires the
        character template"), so a hand-mangled hybrid tests a spec shape that cannot exist.
        """
        out = Path(tempfile.mkdtemp()) / "obj.json"
        subprocess.run(
            [sys.executable, str(_FORGE / "stage2_spec" / "new_sculpt_spec.py"),
             "Pivot Probe", "--out", str(out)],
            capture_output=True, text=True, check=True,
        )
        object_spec = json.loads(out.read_text())
        self.assertFalse(rig_is_bone_track(object_spec))
        source = generate(object_spec, "blockout")
        self.assertNotIn("THREE.Bone", source)
        self.assertNotIn("userData.rig", source)

    def test_bones_are_emitted_parents_first(self) -> None:
        """The spec's bone list is sorted by (has-parent, id), so `foot-l` precedes `shin-l`.
        Emitting in list order would parent a bone to one that does not exist yet."""
        declared: set[str] = set()
        for line in self.generated.splitlines():
            made = re.match(r"\s*const (bone_\w+) = new THREE\.Bone\(\)", line)
            if made:
                declared.add(made.group(1))
                continue
            added = re.match(r"\s*(bone_\w+)\.add\((bone_\w+)\)", line)
            if added:
                self.assertIn(added.group(1), declared, f"parent used before declaration: {line.strip()}")

    def test_attachment_limbs_receive_their_authored_rotation(self) -> None:
        """The endpoint branch used to force `node.rotation.set(0, 0, 0)`.

        Every capsule/cylinder limb carries an `attachment` block and therefore takes that
        branch, so zeroing there silently discarded every authored rotation on exactly the
        components that articulate — `anatomy.pose.jointAngles` had no observable effect at all
        until it stopped. Posing works because the pivot sits AT the joint while the limb's own
        direction lives on the mesh inside it, so rotating the pivot rotates the limb about its
        joint. Guarding the emitted source because a regression here is invisible: the model
        still builds, still renders, and simply ignores the pose.
        """
        from new_sculpt_spec import apply_character_pose

        spec = json.loads(json.dumps(self.spec))
        applied = apply_character_pose(
            spec["componentTree"],
            {"pose": {"jointAngles": {"leftShoulder": [0.05, 0.0, -0.2],
                                      "rightElbow": [-0.34, 0.0, 0.05]}}},
        )
        self.assertEqual(len(applied), 2)
        source = generate(spec, "blockout")

        posed = {c["id"]: (c.get("transform") or {}).get("rotation")
                 for c in spec["componentTree"]
                 if c.get("attachment")
                 and any(abs(float(v)) > 1e-9
                         for v in ((c.get("transform") or {}).get("rotation") or [0, 0, 0]))}
        self.assertTrue(posed, "fixture must contain at least one posed attachment limb")
        for component_id, rotation in posed.items():
            literal = ", ".join(str(float(v)) for v in rotation)
            self.assertIn(
                f"rotation.set({literal})", source,
                f"{component_id}: authored rotation {rotation} never reaches the emitted source",
            )

    def test_exactly_one_weight_function_is_emitted(self) -> None:
        """WS-C.2's acceptance criterion is literally "a grep must find no second weight
        function". Two copies is the defect the criterion exists to prevent, so this counts."""
        self.assertEqual(self.generated.count("const computeVertexWeights ="), 1)
        self.assertIn("new Map<string, number>", self.generated)
        self.assertEqual(self.generated.count("boneOrder.indexOf"), 0,
                         "bone lookup must be a Map, not indexOf")
        self.assertIn("fallback: true", self.generated,
                      "the zero-sum fallback (PLAN_1.5 §4 / ADR-8) must be present")

    def test_skin_weights_are_normalised_and_in_range_on_executed_geometry(self) -> None:
        """Measured, not asserted from the source. The fallback's reachability is what makes
        `zeroSum == 0` meaningful: with 49 envelopes over ~31.7k vertices, any vertex outside
        every envelope would otherwise sum to zero and three.js would silently pin it to bone 0.
        """
        probe = """
import { %(factory)s } from './build/%(stem)s.js';
const m = %(factory)s();
const rig = m.userData.rig;
let worstSum = 0, zeroSum = 0, outOfRange = 0, verts = 0;
const boneCount = rig.boneOrder.length;
for (const name of rig.skinAttributes) {
  const g = m.userData.sculptRuntime.meshes[name].geometry;
  const si = g.getAttribute('skinIndex'), sw = g.getAttribute('skinWeight');
  if (!si || !sw) continue;
  for (let v = 0; v < sw.count; v++) {
    verts++; let s = 0;
    for (let k = 0; k < 4; k++) {
      const idx = si.getComponent(v, k); s += sw.getComponent(v, k);
      if (idx < 0 || idx >= boneCount) outOfRange++;
    }
    if (s === 0) zeroSum++;
    worstSum = Math.max(worstSum, Math.abs(s - 1));
  }
}
console.log(JSON.stringify({ bound: rig.bound, boneCount, verts, worstSum, zeroSum, outOfRange }));
"""
        factory = re.search(r"export function (create\w+Model)", self.generated).group(1)
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            work = Path(tmp)
            from test_hierarchy_scale import compile_generated_module
            compiled, module_path = compile_generated_module(self.generated, work)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            run = subprocess.run(
                ["node", "--input-type=module", "--eval",
                 probe % {"factory": factory, "stem": module_path.stem}],
                cwd=work, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, f"{run.stdout}\n{run.stderr}")
            data = json.loads(run.stdout.strip().splitlines()[-1])

        self.assertGreater(data["verts"], 0, "no skin attributes were written at all")
        self.assertLess(data["worstSum"], 1e-5,
                        f"weights do not sum to 1: max error {data['worstSum']:.3e}")
        self.assertEqual(data["zeroSum"], 0, "a zero-weight-sum vertex escaped the fallback")
        self.assertEqual(data["outOfRange"], 0, "skinIndex out of range")
        self.assertTrue(data["bound"],
                        "WS-C.3 binds every skinned mesh; rig.bound must say so")

    def test_bone_world_positions_round_trip_to_the_spec_joints(self) -> None:
        probe = """
import { %(factory)s } from './build/%(stem)s.js';
import * as THREE from 'three';
const model = %(factory)s();
const rig = model.userData.rig;
model.updateMatrixWorld(true);
const out = { bound: rig.bound, count: rig.boneOrder.length,
              skeletonBones: rig.skeleton.bones.length, world: {}, parent: {} };
for (const id of rig.boneOrder) {
  const b = rig.bones[id];
  out.world[id] = new THREE.Vector3().setFromMatrixPosition(b.matrixWorld).toArray();
  out.parent[id] = b.parent && b.parent.isBone ? b.parent.name : null;
}
console.log(JSON.stringify(out));
"""
        factory = re.search(r"export function (create\w+Model)", self.generated).group(1)
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            work = Path(tmp)
            from test_hierarchy_scale import compile_generated_module
            compiled, module_path = compile_generated_module(self.generated, work)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            run = subprocess.run(
                ["node", "--input-type=module", "--eval",
                 probe % {"factory": factory, "stem": module_path.stem}],
                cwd=work, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, f"{run.stdout}\n{run.stderr}")
            data = json.loads(run.stdout.strip().splitlines()[-1])

        by_id = {b["id"]: b for b in self.spec["rig"]["bones"]}
        self.assertEqual(data["count"], len(by_id))
        self.assertEqual(data["skeletonBones"], len(by_id))
        self.assertTrue(data["bound"], "WS-C.3 binds the skinned meshes; say so in userData.rig")

        # This round-trip is a REST-pose invariant. The generator applies the authored pose to the
        # bones as its last act, so on a posed spec a bone's world position is its posed position,
        # not its rest joint. What matters is specifically that no BONE's component is rotated --
        # the fixture does rotate `nose`, but a micro detail with no bone cannot move a bone.
        # Checked with the emitter's own predicate so the two cannot drift apart.
        self.assertEqual(
            _posed_bone_rotations(self.spec, self.spec["rig"]["bones"]), [],
            "no bone's component may be posed, or the rest-pose round-trip below is vacuous")

        for bone_id, world in data["world"].items():
            joint = by_id[bone_id]["jointPos"]
            error = max(abs(world[i] - joint[i]) for i in range(3))
            self.assertLess(
                error, 1e-6,
                f"bone {bone_id!r} world position {world} does not round-trip to its "
                f"model-space jointPos {joint} (error {error:.3e}) — the parent-local "
                f"conversion is wrong",
            )
            self.assertEqual(data["parent"][bone_id], by_id[bone_id]["parent"])

    def test_bone_rotation_deforms_its_own_mesh_and_not_a_distant_one(self) -> None:
        """WS-C.3: the meshes are genuinely skeleton-driven, on executed geometry.

        `rig.bound === true` does not prove this. A mesh can be bound and completely inert if the
        skeleton's inverse bind matrices cancel the wrong pose — which is what a `Skeleton`
        constructed before `updateMatrixWorld()` produces, since `calculateInverses()` reads the
        bones' CURRENT world matrices and would capture identity. That failure compiles, binds,
        reports `bound: true`, and renders a corpse.

        The far-mesh half is the negative control. Without it this test passes just as well on a
        model where every vertex is weighted to every bone, which is the other way skinning goes
        wrong — the whole body billowing when one finger moves.
        """
        probe = """
import { %(factory)s } from './build/%(stem)s.js';
import * as THREE from 'three';
const model = %(factory)s();
model.updateMatrixWorld(true);
const rig = model.userData.rig;
const skinned = [];
const skeletons = new Set();
model.traverse((o) => {
  if (o.isSkinnedMesh) { skinned.push(o); if (o.skeleton) skeletons.add(o.skeleton); }
});
const v = new THREE.Vector3();
const sample = (mesh) => {
  const pos = mesh.geometry.getAttribute('position');
  const pts = [];
  for (let i = 0; i < pos.count; i += 3) {
    v.fromBufferAttribute(pos, i);
    mesh.applyBoneTransform(i, v);
    pts.push(mesh.localToWorld(v.clone()).toArray());
  }
  return pts;
};
const spread = (a, b) => {
  let mx = 0;
  for (let i = 0; i < a.length; i++) {
    mx = Math.max(mx, Math.hypot(a[i][0]-b[i][0], a[i][1]-b[i][1], a[i][2]-b[i][2]));
  }
  return mx;
};
const byName = {};
for (const mesh of skinned) byName[mesh.name] = mesh;

// Rest-pose identity. With every bone rotation zeroed the bones are back in the pose the
// Skeleton's inverse bind matrices were computed from, so skinning must be a NO-OP: each vertex
// maps to exactly where the baked geometry already puts it. This is what catches a Skeleton
// constructed before its bones' world matrices exist -- calculateInverses() then captures
// identity, and every vertex is displaced by its bone's joint offset instead of staying put.
const restRotations = {};
for (const id of rig.boneOrder) {
  const b = rig.bones[id];
  restRotations[id] = [b.rotation.x, b.rotation.y, b.rotation.z];
  b.rotation.set(0, 0, 0);
}
model.updateMatrixWorld(true); rig.skeleton.update();
let restDrift = 0;
let restChecked = 0;
for (const mesh of skinned) {
  const pos = mesh.geometry.getAttribute('position');
  for (let i = 0; i < pos.count; i += 3) {
    v.fromBufferAttribute(pos, i);
    const raw = v.clone();
    mesh.applyBoneTransform(i, v);
    restDrift = Math.max(restDrift, raw.distanceTo(v));
    restChecked += 1;
  }
}
for (const id of rig.boneOrder) rig.bones[id].rotation.set(...restRotations[id]);
model.updateMatrixWorld(true); rig.skeleton.update();

const out = {
  restDrift, restChecked,
  bound: rig.bound,
  skinnedCount: skinned.length,
  skeletonCount: skeletons.size,
  allParentedToRoot: skinned.every((o) => o.parent === model),
  identityLocal: skinned.every((o) =>
    o.position.lengthSq() < 1e-12
    && o.scale.distanceToSquared(new THREE.Vector3(1, 1, 1)) < 1e-12),
  anyCulled: skinned.filter((o) => o.frustumCulled).map((o) => o.name),
  cullingRecorded: rig.frustumCulled === false && typeof rig.cullingNote === 'string',
  names: Object.keys(byName),
  probes: [],
};
for (const [boneId, ownName, farName] of %(cases)s) {
  const bone = rig.bones[boneId], own = byName[ownName], far = byName[farName];
  if (!bone || !own || !far) { out.probes.push({ boneId, missing: true }); continue; }
  const beforeOwn = sample(own), beforeFar = sample(far);
  const keep = bone.rotation.z;
  bone.rotation.z = keep + 1.0;
  model.updateMatrixWorld(true); rig.skeleton.update();
  const ownDelta = spread(beforeOwn, sample(own));
  const farDelta = spread(beforeFar, sample(far));
  bone.rotation.z = keep;
  model.updateMatrixWorld(true); rig.skeleton.update();
  out.probes.push({ boneId, ownName, farName, ownDelta, farDelta });
}
console.log(JSON.stringify(out));
"""
        cases = [["upper-arm-l", "Upper arm L", "Shin R"], ["thigh-r", "Thigh R", "Forearm L"]]
        factory = re.search(r"export function (create\w+Model)", self.generated).group(1)
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            work = Path(tmp)
            from test_hierarchy_scale import compile_generated_module
            compiled, module_path = compile_generated_module(self.generated, work)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            run = subprocess.run(
                ["node", "--max-old-space-size=3072", "--input-type=module", "--eval",
                 probe % {"factory": factory, "stem": module_path.stem,
                          "cases": json.dumps(cases)}],
                cwd=work, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, f"{run.stdout}\n{run.stderr}")
            data = json.loads(run.stdout.strip().splitlines()[-1])

        bone_count = len(self.spec["rig"]["bones"])
        self.assertTrue(data["bound"])
        self.assertEqual(data["skinnedCount"], bone_count,
                         "every bone's component must be emitted as a THREE.SkinnedMesh")
        self.assertEqual(data["skeletonCount"], 1,
                         f"all {bone_count} skinned meshes must share ONE Skeleton, "
                         f"found {data['skeletonCount']}")
        self.assertTrue(data["allParentedToRoot"],
                        "skinned meshes are reparented to root so no pivot applies on top")
        self.assertTrue(data["identityLocal"],
                        "a skinned mesh's own transform must be identity; its world matrix was "
                        "baked into the geometry")
        # A SkinnedMesh keeps its REST boundingSphere, so a posed limb reaching outside it is culled
        # and disappears from some camera angles only. The choice has to be discoverable too, or a
        # consumer that needs culling silently gets none.
        self.assertEqual(data["anyCulled"], [],
                         "these skinned meshes are still frustum-culled and can vanish when posed")
        self.assertTrue(data["cullingRecorded"],
                        "userData.rig must record the culling decision and why")
        self.assertGreater(data["restChecked"], 1000,
                           "the rest-pose check must actually sample vertices")
        self.assertLess(
            data["restDrift"], 1e-5,
            f"at rest, skinning displaces vertices by up to {data['restDrift']:.4f} instead of "
            f"leaving them where the baked geometry puts them — the Skeleton's inverse bind "
            f"matrices do not match the pose the geometry was baked in",
        )

        self.assertEqual(len(data["probes"]), len(cases))
        for probe_result in data["probes"]:
            self.assertFalse(
                probe_result.get("missing"),
                f"probe {probe_result['boneId']!r} could not resolve its meshes; available: "
                f"{sorted(data['names'])}",
            )
            self.assertGreater(
                probe_result["ownDelta"], 1e-3,
                f"rotating bone {probe_result['boneId']!r} moved its own mesh "
                f"{probe_result['ownName']!r} by only {probe_result['ownDelta']:.3e} — the mesh "
                f"is bound but inert",
            )
            self.assertLess(
                probe_result["farDelta"], 1e-6,
                f"rotating bone {probe_result['boneId']!r} also moved {probe_result['farName']!r} "
                f"by {probe_result['farDelta']:.3e} — weights are leaking across the body",
            )


    def test_the_bake_is_pose_independent(self) -> None:
        """A posed spec must bake the SAME rest geometry as an unposed one.

        The bake folds each skinned mesh's world matrix into its vertex data, and at that moment
        the pivots still carry the authored pose — so baking naively freezes the pose into the
        buffer while the bones ALSO apply it, and the figure is posed twice. Nothing checked so far
        can see that: `bound` is true, bones still deform their own meshes, weights still sum to 1,
        and the rest-pose identity check still passes, because at bone-rest skinning is a no-op on
        whatever geometry happens to be in the buffer — correct or not.

        So compare the two builds directly. The raw baked geometry is what the pose must not reach;
        if it is identical with and without a pose, the pose lives only on the bones.

        The fixture is posed here rather than reusing the template's own pose because the character
        template poses no bone at all (only `nose`, a boneless micro detail), which would make this
        a no-op — a mutation that removed the rest-for-bake step passed against it.
        """
        posed_spec = json.loads(json.dumps(self.spec))
        pose = {"upper-arm-l": [0.0, 0.0, 0.45], "shin-r": [0.35, 0.0, 0.0],
                "neck": [0.0, 0.25, 0.0]}
        applied = 0
        for component in posed_spec["componentTree"]:
            if component["id"] in pose:
                component["transform"]["rotation"] = pose[component["id"]]
                applied += 1
        self.assertEqual(applied, len(pose), "fixture pose did not land on the intended components")
        self.assertEqual(
            {b for b, _c, _v in _posed_bone_rotations(posed_spec, posed_spec["rig"]["bones"])},
            set(pose), "the posed components must all be bones, or this proves nothing")

        probe = """
import { %(factory)s } from './build/%(stem)s.js';
const model = %(factory)s();
model.updateMatrixWorld(true);
const raw = {};
model.traverse((o) => {
  if (!o.isSkinnedMesh) return;
  const pos = o.geometry.getAttribute('position');
  const pts = [];
  for (let i = 0; i < pos.count; i += 11) {
    pts.push([+pos.getX(i).toFixed(6), +pos.getY(i).toFixed(6), +pos.getZ(i).toFixed(6)]);
  }
  raw[o.name] = pts;
});
console.log(JSON.stringify(raw));
"""

        def raw_geometry(spec: dict) -> dict:
            generated = generate(spec, "blockout")
            factory = re.search(r"export function (create\w+Model)", generated).group(1)
            with tempfile.TemporaryDirectory(dir=self.root) as tmp:
                work = Path(tmp)
                from test_hierarchy_scale import compile_generated_module
                compiled, module_path = compile_generated_module(generated, work)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                run = subprocess.run(
                    ["node", "--max-old-space-size=3072", "--input-type=module", "--eval",
                     probe % {"factory": factory, "stem": module_path.stem}],
                    cwd=work, capture_output=True, text=True,
                )
                self.assertEqual(run.returncode, 0, f"{run.stdout}\n{run.stderr}")
                return json.loads(run.stdout.strip().splitlines()[-1])

        rest = raw_geometry(self.spec)
        posed = raw_geometry(posed_spec)

        self.assertEqual(sorted(rest), sorted(posed), "the two builds skinned different meshes")
        self.assertGreater(sum(len(v) for v in rest.values()), 500,
                           "not enough vertices sampled for this comparison to mean anything")
        worst_name, worst = "", 0.0
        for name, points in rest.items():
            for a, b in zip(points, posed[name]):
                drift = max(abs(a[i] - b[i]) for i in range(3))
                if drift > worst:
                    worst_name, worst = name, drift
        self.assertLess(
            worst, 1e-5,
            f"posing the spec changed the BAKED geometry of {worst_name!r} by {worst:.5f} — the "
            f"pose was frozen into the vertex buffer, so the bones will apply it a second time",
        )


if __name__ == "__main__":
    unittest.main()
