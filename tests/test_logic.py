"""Offline tests for the deterministic logic: lead-time lookup, priority, Excel.

No API key needed. These lock in the rules a reviewer will scrutinize on a demo.
"""
import os
import tempfile
import unittest

from openpyxl import load_workbook

from src.excel import HEADERS, Row, write_register
from src.lead_times import CATEGORIES, bucket_for, cell_text
from src.priority import priority_flag


class TestLeadTimes(unittest.TestCase):
    def test_every_category_resolves(self):
        for cat in CATEGORIES:
            label, low, high = bucket_for(cat)
            self.assertIn(label, {"Stock", "Short", "Medium", "Long", "Extra-Long"})
            self.assertLessEqual(low, high)

    def test_unknown_is_conservative_medium(self):
        self.assertEqual(bucket_for("not-a-real-category")[0], "Medium")

    def test_cell_text_formats(self):
        self.assertEqual(cell_text("concrete_rebar_aggregate"), "Stock")
        self.assertEqual(cell_text("storefront_glazing"), "Long (20-28 wk)")


class TestPriority(unittest.TestCase):
    def test_long_lead_is_urgent(self):
        self.assertEqual(priority_flag("electrical_switchgear", False), "Urgent")

    def test_storage_sensitive_short_lead_is_urgent(self):
        # Stock item, but storage-sensitive -> still Urgent.
        self.assertEqual(priority_flag("concrete_rebar_aggregate", True), "Urgent")

    def test_ordinary_short_lead_is_standard(self):
        self.assertEqual(priority_flag("paint_coatings", False), "Standard")


class TestExcel(unittest.TestCase):
    def test_writes_readable_register(self):
        rows = [
            Row("03 30 00 — Cast-in-Place Concrete", "Concrete mix design",
                "Design mixtures; product data", "Stock", "Urgent"),
            Row("09 91 00 — Painting", "Interior paint",
                "Product data; samples", "Short (4-8 wk)", "Standard"),
        ]
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "register.xlsx")
            write_register(rows, out)
            self.assertTrue(os.path.exists(out))
            ws = load_workbook(out).active
            self.assertEqual([c.value for c in ws[1]], HEADERS)
            self.assertEqual(ws.max_row, 3)  # header + 2 rows
            self.assertEqual(ws.cell(row=2, column=5).value, "Urgent")


if __name__ == "__main__":
    unittest.main()
