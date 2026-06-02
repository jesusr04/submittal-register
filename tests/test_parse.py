"""Offline tests for running-header/footer stripping — no PDF, no network.

`_strip_running_headers` is the fix for multi-page sections being fragmented by
repeated page furniture, so it's worth locking down on synthetic pages.
"""
import unittest

from src.parse import _strip_running_headers


def _page(section_header, *body):
    # The 6-line running header this spec prints, then page body.
    return "\n".join(
        [
            "Elementary School #32",
            "Leander Independent School District",
            "Project Number 25-012",
            section_header,  # e.g. "05 32 23 STEEL ROOF DECKING" (page furniture)
            "Page 1 of 5",
            "100% CONSTRUCTION DOCUMENTS",
            *body,
        ]
    )


class TestStripRunningHeaders(unittest.TestCase):
    def setUp(self):
        # Five pages of one section. The header's section number is a typo
        # (05 32 23) vs the real "SECTION 05 31 23" — the exact case from the spec.
        pages = [_page("05 32 23 STEEL ROOF DECKING", "SECTION 05 31 23", "PART 1 - GENERAL")]
        pages += [_page("05 32 23 STEEL ROOF DECKING", f"Body line {i}") for i in range(2, 6)]
        self.cleaned = _strip_running_headers(pages)

    def test_drops_global_boilerplate(self):
        joined = "\n".join(self.cleaned)
        self.assertNotIn("Leander Independent School District", joined)
        self.assertNotIn("100% CONSTRUCTION DOCUMENTS", joined)
        self.assertNotIn("Page 1 of 5", joined)

    def test_drops_bare_csi_page_header(self):
        # The phantom-causing line must be gone from every page...
        self.assertNotIn("05 32 23", "\n".join(self.cleaned))

    def test_keeps_real_section_header_and_body(self):
        # ...but the real section header and content stay.
        joined = "\n".join(self.cleaned)
        self.assertIn("SECTION 05 31 23", joined)
        self.assertIn("PART 1 - GENERAL", joined)
        self.assertIn("Body line 4", joined)


if __name__ == "__main__":
    unittest.main()
