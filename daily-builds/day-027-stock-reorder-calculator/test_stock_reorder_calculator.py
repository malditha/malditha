import unittest

from stock_reorder_calculator import InputError, calculate, calculate_all, render_text


BASE = {
    "item_code": "FABRIC-BLUE",
    "current_qty": 20,
    "on_order_qty": 5,
    "average_daily_usage": 4,
    "lead_time_days": 7,
    "safety_stock": 6,
    "minimum_order_qty": 12,
    "pack_size": 5,
}


class StockReorderCalculatorTests(unittest.TestCase):
    def test_reorder_point_and_pack_rounding(self):
        result = calculate(BASE)
        self.assertEqual(result.reorder_point, 34)
        self.assertEqual(result.shortage, 9)
        self.assertEqual(result.recommended_order_qty, 15)
        self.assertEqual(result.status, "reorder")

    def test_minimum_order_quantity_applies(self):
        result = calculate({**BASE, "current_qty": 31, "on_order_qty": 0})
        self.assertEqual(result.shortage, 3)
        self.assertEqual(result.recommended_order_qty, 15)

    def test_on_order_stock_prevents_reorder(self):
        result = calculate({**BASE, "current_qty": 20, "on_order_qty": 14})
        self.assertEqual(result.status, "sufficient")
        self.assertEqual(result.recommended_order_qty, 0)

    def test_zero_usage_can_be_sufficient(self):
        result = calculate({**BASE, "average_daily_usage": 0, "safety_stock": 0})
        self.assertEqual(result.reorder_point, 0)
        self.assertEqual(result.status, "sufficient")

    def test_rejects_negative_values(self):
        with self.assertRaisesRegex(InputError, "zero or greater"):
            calculate({**BASE, "current_qty": -1})

    def test_rejects_boolean_as_number(self):
        with self.assertRaisesRegex(InputError, "must be a number"):
            calculate({**BASE, "lead_time_days": True})

    def test_rejects_zero_pack_size(self):
        with self.assertRaisesRegex(InputError, "greater than zero"):
            calculate({**BASE, "pack_size": 0})

    def test_rejects_unknown_properties(self):
        with self.assertRaisesRegex(InputError, "Unsupported"):
            calculate({**BASE, "supplier_password": "secret"})

    def test_rejects_duplicate_item_codes_case_insensitively(self):
        with self.assertRaisesRegex(InputError, "duplicate"):
            calculate_all([BASE, {**BASE, "item_code": "fabric-blue"}])

    def test_results_are_sorted(self):
        results = calculate_all([{**BASE, "item_code": "Z"}, {**BASE, "item_code": "A"}])
        self.assertEqual([item.item_code for item in results], ["A", "Z"])

    def test_text_has_non_mutating_notice(self):
        self.assertIn("no stock or purchase order was changed", render_text([calculate(BASE)]))


if __name__ == "__main__":
    unittest.main()
