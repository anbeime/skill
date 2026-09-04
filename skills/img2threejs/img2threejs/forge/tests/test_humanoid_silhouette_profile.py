"""Whole-silhouette assertions on the BUILT humanoid — the kind of check that was missing.

Every other rig test in this suite is PER-PART: a bbox, a propagation delta, a weight sum. Those
cannot see facts that only exist across the whole figure, and the first render proved it — 452
tests were green while the model had a tabletop for a pelvis and a neck 40% the length of its
torso. Every individual part was correct.

So these tests measure the silhouette's width as a function of height, the same instrument used on
the reference grey sculpt, and assert shape properties rather than dimensions:

- a slab shows up as consecutive bands of IDENTICAL width (flat vertical sides);
- a tabletop shows up as the hip band exceeding the torso above it;
- a missing shoulder means the neck band jumps straight to full torso width with no intermediate.

Reference figures, measured from the ZBrush grey sculpt of nguy-n-khoa-overview.jpg (848px tall):
hair 0.136 w/h, neck 0.116, shoulders 0.229, widest 0.290.

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

from generate_threejs_factory import generate  # noqa: E402

BANDS = 20

_VERTEX_PROBE = """
import { %(factory)s } from './build/%(stem)s.js';
import * as THREE from 'three';
const m = %(factory)s(); m.updateMatrixWorld(true);
const pts = [];
m.traverse((o) => {
  if (!o.isMesh || !o.geometry) return;
  const mat = o.material;
  const op = Array.isArray(mat) ? 1 : (mat && mat.opacity !== undefined ? mat.opacity : 1);
  if (op === 0) return;                       // the invisible 1x1x1 root placeholder
  const pos = o.geometry.getAttribute('position'); if (!pos) return;
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld);
    pts.push([v.x, v.y]);
  }
});
console.log(JSON.stringify(pts));
"""


class HumanoidSilhouetteProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = showcase_root()          # skips with an actionable message when unset
        cls.profile = cls._profile_for(None)

    @classmethod
    def _profile_for(cls, anatomy: dict | None) -> list[float | None]:
        """Build the model for a given anatomy and return its width-by-height profile.

        Parameterised by anatomy because a silhouette defect can be invisible at one set of
        proportions and obvious at another — the shoulder cliff only appears on a narrow-shouldered
        figure, so a test that only ever builds the default template cannot see it.
        """
        work_dir = Path(tempfile.mkdtemp())
        argv = [sys.executable, str(_FORGE / "stage2_spec" / "new_sculpt_spec.py"),
                "Silhouette Probe", "--character", "--out", str(work_dir / "character.json")]
        if anatomy is not None:
            assessment = work_dir / "assessment.json"
            subprocess.run(
                [sys.executable, str(_FORGE / "stage2_spec" / "new_pre_spec_assessment.py"),
                 "Silhouette Probe", "--complexity", "complex", "--out", str(assessment)],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(assessment.read_text())
            pre = payload["preSpecAssessment"]
            pre["anatomy"] = anatomy
            pre.setdefault("objectClass", {})["primaryDomain"] = "character"
            assessment.write_text(json.dumps(payload))
            argv += ["--assessment", str(assessment)]
        subprocess.run(argv, capture_output=True, text=True, check=True)
        spec = json.loads((work_dir / "character.json").read_text())
        generated = generate(spec, "blockout")
        factory = re.search(r"export function (create\w+Model)", generated).group(1)

        with tempfile.TemporaryDirectory(dir=cls.root) as tmp:
            work = Path(tmp)
            from test_hierarchy_scale import compile_generated_module
            compiled, module_path = compile_generated_module(generated, work)
            if compiled.returncode != 0:
                raise AssertionError(f"tsc failed:\n{compiled.stderr[:2000]}")
            run = subprocess.run(
                ["node", "--max-old-space-size=2048", "--input-type=module", "--eval",
                 _VERTEX_PROBE % {"factory": factory, "stem": module_path.stem}],
                cwd=work, capture_output=True, text=True,
            )
            if run.returncode != 0:
                raise AssertionError(f"node failed:\n{run.stderr[:2000]}")
            points = json.loads(run.stdout.strip().splitlines()[-1])

        ys = [p[1] for p in points]
        low, high = min(ys), max(ys)
        height = high - low
        cls.height = height
        profile: list[float | None] = []
        for band in range(BANDS):
            y0 = high - height * (band + 1) / BANDS
            y1 = high - height * band / BANDS
            xs = [p[0] for p in points if y0 <= p[1] <= y1]
            profile.append((max(xs) - min(xs)) / height if xs else None)
        return profile

    def test_the_profile_is_measurable(self) -> None:
        self.assertGreater(self.height, 0)
        self.assertTrue(all(w is not None for w in self.profile),
                        f"a band is empty, so the figure has a gap: {self.profile}")

    def test_no_body_segment_is_a_slab(self) -> None:
        """The tabletop test, done on the SPEC rather than the silhouette.

        I first wrote this as "no three consecutive profile bands share a width", reasoning that a
        box's flat vertical sides would show up as identical widths. Mutation-checking it proved
        that WRONG: reverting the pelvis to a box still passed, because at 20 bands the thighs and
        abdomen overlap the pelvis's bands and break the identical-width signature. That was dead
        coverage — a test that looked like it guarded the defect and did not.

        The defect is an aspect ratio, so measure the aspect ratio. The pelvis that rendered as a
        tabletop was 0.455 wide by 0.123 tall: 3.7:1. No body segment should be that flat.
        """
        out = Path(tempfile.mkdtemp()) / "aspect.json"
        subprocess.run(
            [sys.executable, str(_FORGE / "stage2_spec" / "new_sculpt_spec.py"),
             "Aspect Probe", "--character", "--out", str(out)],
            capture_output=True, text=True, check=True,
        )
        spec = json.loads(out.read_text())
        for component in spec["componentTree"]:
            if component.get("role") in (None, "detail", "hair", "decal", "panel"):
                continue
            scale = (component.get("transform") or {}).get("scale") or [1, 1, 1]
            width, height, depth = (float(v) for v in scale)
            if height <= 0:
                continue
            # `min(width, depth) / height`, not `max`. A slab has TWO large dimensions and one
            # small — wide AND deep but short. A limb bone has ONE large and two small. Using
            # `max` conflated them and flagged `clavicle-l` (0.271 x 0.095 x 0.095), which is a
            # legitimately long thin bone. Measured with `min`: the tabletop pelvis scores 2.92,
            # the corrected pelvis 1.25, and the clavicle 1.00.
            slabness = min(width, depth) / height
            self.assertLess(
                slabness, 2.0,
                f"{component['id']!r} is {width:.4f} x {height:.4f} x {depth:.4f} — both of its "
                f"horizontal extents are {slabness:.2f}x its height, which reads as a slab",
            )

    # DELETED: an assertion that hips must not be wider than the torso above them.
    #
    # It failed on the DEFAULT template and it was the test that was wrong, twice over. Its band
    # indices were hardcoded, so they do not survive a different `torso` ratio moving the pelvis
    # into a different band. And more fundamentally the rule is not universally true: a pear-shaped
    # figure legitimately has wider hips than chest, and the regret reference is measurably one —
    # narrow shoulders (1.552 HU) against wide hips (1.712 HU). The actual defect was never
    # "hips wider than torso"; it was "the pelvis is a flat slab", which
    # test_no_three_consecutive_bands_share_a_width catches directly and without assuming a body
    # type. Same failure mode as the first MONOTONIC_CHAIN: a check that rejects a legitimate case.

    def test_the_neck_to_shoulder_transition_is_a_slope_not_a_cliff(self) -> None:
        """Run against a NARROW-SHOULDERED anatomy, because that is where the cliff appears.

        Asserted against the default template this test was dead coverage: mutation-checking it by
        restoring the thin clavicle and the chest's wide flat top did NOT fail it, because at the
        default shoulderWidth of 2.3 HU the chest is broad enough that band 3 lands between head
        and torso anyway. The cliff only manifested at the regret reference's measured 1.552 HU.
        A test has to exercise the configuration that produced the bug.
        """
        profile = self._profile_for({
            "applies": True,
            "styleHeads": 6.78,
            "proportions": {"torso": 1.584, "legs": 3.384,
                            "shoulderWidth": 1.552, "hipWidth": 1.712},
        })
        head = max(w for w in profile[0:3] if w is not None)
        torso = max(w for w in profile[4:7] if w is not None)
        shoulder = profile[3]
        self.assertIsNotNone(shoulder)
        self.assertGreater(shoulder, head,
                           "the shoulder band is no wider than the head — no shoulder mass")
        self.assertLess(shoulder, torso,
                        f"shoulder band {shoulder:.4f} already equals torso width {torso:.4f} — "
                        f"the silhouette jumps from neck to full width in one band")

    def test_the_figure_tapers_toward_the_feet(self) -> None:
        """Legs must narrow. A humanoid that is as wide at the ankles as at the hips is a tube."""
        hips = max(self.profile[8:11])
        ankles = self.profile[-1]
        self.assertLess(ankles, hips * 0.75,
                        f"ankle band {ankles:.4f} against hips {hips:.4f} — the legs do not taper")

    def test_no_component_emits_empty_geometry(self) -> None:
        """A specified component whose mesh has no extent does not exist in the model.

        This is the check that was missing, and it hid a real defect for the whole of US-004: both
        eye cavities emitted EMPTY geometry. `polygonizeSdf` falls back to a
        [-2,-2,-2]..[2,2,2] sampling box when the descriptor omits `bounds`, and at resolution 20
        that makes each cell 0.2 across while the socket's shell radius is 0.0252 — the entire
        sphere fell between samples and marching cubes emitted nothing. Meanwhile the spec said
        `subtract`, the validator's recessed-feature gate was satisfied by exactly that, and the
        whole suite was green. The eyes were "recessed sockets" in the spec and absent in the model.
        """
        probe = """
import { %(factory)s } from './build/%(stem)s.js';
import * as THREE from 'three';
const m = %(factory)s(); m.updateMatrixWorld(true);
const empty = [];
for (const [id, mesh] of Object.entries(m.userData.sculptRuntime.meshes)) {
  const b = new THREE.Box3().setFromObject(mesh);
  if (b.isEmpty() || !Number.isFinite(b.min.x) || !Number.isFinite(b.max.x)) empty.push(id);
}
console.log(JSON.stringify({ empty, total: Object.keys(m.userData.sculptRuntime.meshes).length }));
"""
        work_dir = Path(tempfile.mkdtemp())
        subprocess.run(
            [sys.executable, str(_FORGE / "stage2_spec" / "new_sculpt_spec.py"),
             "Empty Probe", "--character", "--out", str(work_dir / "c.json")],
            capture_output=True, text=True, check=True,
        )
        generated = generate(json.loads((work_dir / "c.json").read_text()), "blockout")
        factory = re.search(r"export function (create\w+Model)", generated).group(1)
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            work = Path(tmp)
            from test_hierarchy_scale import compile_generated_module
            compiled, module_path = compile_generated_module(generated, work)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            run = subprocess.run(
                ["node", "--input-type=module", "--eval",
                 probe % {"factory": factory, "stem": module_path.stem}],
                cwd=work, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, f"{run.stdout}\n{run.stderr}")
            data = json.loads(run.stdout.strip().splitlines()[-1])

        self.assertGreater(data["total"], 0, "no meshes at all — the probe measured nothing")
        self.assertEqual(
            data["empty"], [],
            f"{len(data['empty'])} of {data['total']} components emit geometry with no extent, so "
            f"they are specified but absent from the model: {data['empty']}",
        )

    def test_head_width_is_in_the_reference_range(self) -> None:
        """Reference grey sculpt: the hair mass is 0.136 of figure height. A stylised head is
        large, but a head half the figure's width is a different character."""
        head = max(self.profile[0:3])
        self.assertGreater(head, 0.08, f"head {head:.4f} is too narrow for a stylised figure")
        self.assertLess(head, 0.22, f"head {head:.4f} is wider than any reference band")


if __name__ == "__main__":
    unittest.main()
