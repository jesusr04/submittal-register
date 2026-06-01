"""Offline tests for section splitting — no API key, no network.

These prove the deterministic spine of the pipeline (parse/split) works against
a realistic CSI layout, including the Table-of-Contents de-dup and PART 1
slicing. Run: `python -m pytest` or `python -m unittest`.
"""
import os
import unittest

from src.sections import part1, split_sections

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_spec.txt")


class TestSections(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE, encoding="utf-8") as f:
            self.text = f.read()
        self.sections = split_sections(self.text)

    def test_dedupes_table_of_contents(self):
        # 03 30 00 and 08 41 13 each appear in the TOC and as a real section;
        # we should end up with exactly two sections, not four.
        self.assertEqual(len(self.sections), 2)
        self.assertEqual([s.number for s in self.sections], ["03 30 00", "08 41 13"])

    def test_keeps_real_body_over_toc_line(self):
        concrete = self.sections[0]
        self.assertIn("SUBMITTALS", concrete.text)
        self.assertGreater(len(concrete.text), 200)

    def test_label_formats_number_and_title(self):
        self.assertEqual(
            self.sections[0].label, "03 30 00 — CAST-IN-PLACE CONCRETE"
        )

    def test_part1_excludes_part2(self):
        p1 = part1(self.sections[0].text)
        self.assertIn("SUBMITTALS", p1)
        self.assertNotIn("CONCRETE MATERIALS", p1)  # that's in PART 2


if __name__ == "__main__":
    unittest.main()
