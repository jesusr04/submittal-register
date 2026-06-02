"""Offline tests for section splitting — no API key, no network.

These prove the deterministic spine of the pipeline (parse/split) works against
a realistic CSI layout, including the Table-of-Contents de-dup and PART 1
slicing. Run: `python -m pytest` or `python -m unittest`.
"""
import os
import unittest

from src.sections import Section, is_spec_section, part1, real_sections, split_sections

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


class TestSectionFiltering(unittest.TestCase):
    """is_spec_section / real_sections drop the junk a real spec book carries."""

    def _section(self, number, title="", body_len=500):
        return Section(number=number, title=title, text="x" * body_len)

    def test_rejects_non_masterformat_division(self):
        # "55 60 65" has the XX XX XX shape but division 55 doesn't exist — it's a
        # number row from a sieve-analysis chart in an appended geotech report.
        self.assertFalse(is_spec_section(self._section("55 60 65", body_len=500)))

    def test_rejects_empty_body(self):
        # Real division, but only a TOC line / specified in another volume (MEP),
        # so there's nothing to extract.
        self.assertFalse(is_spec_section(self._section("26 24 16", "PANELBOARDS", 40)))

    def test_keeps_real_section(self):
        self.assertTrue(is_spec_section(self._section("03 30 00", "CONCRETE", 500)))

    def test_rejects_numeric_title_in_valid_division(self):
        # Valid division, long body, but the "title" is a number — a sieve row or
        # submittal-numbering prose, not a real section name.
        self.assertFalse(is_spec_section(self._section("10 15 20", "25", 800)))
        self.assertFalse(is_spec_section(self._section("10 16 00", "4, etc.  Note:", 3000)))

    def test_real_sections_drops_chart_noise_keeps_real(self):
        text = (
            "SECTION 03 30 00 — CAST-IN-PLACE CONCRETE\n"
            "PART 1 - GENERAL\n" + "A. Product data and design mixtures.\n" * 20
            + "\nU.S. SIEVE NUMBERS\n55 60 65\nGRAIN SIZE IN MILLIMETERS\n"
        )
        numbers = [s.number for s in real_sections(text)]
        self.assertIn("03 30 00", numbers)
        self.assertNotIn("55 60 65", numbers)


if __name__ == "__main__":
    unittest.main()
