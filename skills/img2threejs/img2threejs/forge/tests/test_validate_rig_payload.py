import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from forge.stage5_rig.validate_rig_payload import validate  # noqa: E402


def payload():
    return {
        "schemaVersion": 1,
        "coordinateSystem": {"up": "Y", "handedness": "right", "unit": "normalized"},
        "joints": [[0, 0, 0], [0, 1, 0], [0.5, 1.5, 0]],
        "parents": [None, 0, 1],
        "names": ["root", "spine", "arm_L"],
        "matrix_local": [
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 0, 0.5, 0, 1, 0, 0.5, 0, 0, 1, 0, 0, 0, 0, 1],
        ],
        "skinIndex": [[0, 1, 2, 0], [1, 2, 0, 0]],
        "skinWeight": [[0.5, 0.3, 0.2, 0], [0.2, 0.8, 0, 0]],
    }


class ValidateRigPayloadTest(unittest.TestCase):
    def test_valid_payload_passes(self):
        result = validate(payload())
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["summary"]["maxInfluences"], 4)

    def test_parent_order_is_hard_gate(self):
        value = payload()
        value["parents"][2] = 2
        result = validate(value)
        self.assertFalse(result["passed"])
        self.assertTrue(any("parent < child" in error for error in result["errors"]))

    def test_weight_normalization_and_nan_are_hard_gates(self):
        value = payload()
        value["skinWeight"][0] = [0.5, 0.5, 0.5, 0]
        value["skinWeight"][1][0] = float("nan")
        result = validate(value)
        self.assertFalse(result["passed"])
        self.assertTrue(any("must sum to 1" in error for error in result["errors"]))
        self.assertTrue(any("finite non-negative" in error for error in result["errors"]))

    def test_duplicate_names_and_bad_matrix_are_hard_gates(self):
        value = copy.deepcopy(payload())
        value["names"][2] = "spine"
        value["matrix_local"][1][15] = 0
        result = validate(value)
        self.assertFalse(result["passed"])
        self.assertTrue(any("duplicate joint name" in error for error in result["errors"]))
        self.assertTrue(any("affine last row" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
