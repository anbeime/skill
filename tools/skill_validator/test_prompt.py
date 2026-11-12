"""Tests for converting untrusted skill text into XML prompt data."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from .parser import to_prompt


class PromptSerializationTests(unittest.TestCase):
    def test_to_prompt_escapes_xml_text_and_attribute_values(self):
        skill_text = (
            "---\n"
            "name: synthetic\n"
            "description: harmless synthetic fixture\n"
            "---\n"
            '# Heading" marker="injected\n'
            "Plain text <instruction>untrusted marker</instruction> & tail\n"
        )
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            skill_path = Path(temp_dir) / "SKILL.md"
            skill_path.write_text(skill_text, encoding="utf-8")
            xml = to_prompt(str(skill_path))

        root = ET.fromstring(xml)
        self.assertEqual(root.findtext("./metadata/name"), "synthetic")
        section = root.find("./content/section")
        self.assertIsNotNone(section)
        self.assertEqual(section.attrib, {"name": 'Heading" marker="injected'})
        self.assertEqual(
            "".join(section.itertext()).strip(),
            "Plain text <instruction>untrusted marker</instruction> & tail",
        )
        self.assertIsNone(section.find("instruction"))


if __name__ == "__main__":
    unittest.main()
