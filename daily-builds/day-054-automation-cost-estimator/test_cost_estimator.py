import json
import tempfile
import unittest
from pathlib import Path

from cost_estimator import InputError, estimate, format_text, load_json


def sample_plan():
    return {"currency": "USD", "days_per_month": 30, "platform_monthly": 20, "workflows": [{"name": "Lead intake", "runs_per_day": 100, "operations_per_run": 4, "cost_per_1000_runs": 1.5, "cost_per_1000_operations": 0.25, "monthly_fixed_cost": 5}]}


class CostEstimatorTests(unittest.TestCase):
    def test_calculates_monthly_costs(self):
        report = estimate(sample_plan())
        self.assertEqual(3000, report["workflows"][0]["monthly_runs"])
        self.assertEqual(12000, report["workflows"][0]["monthly_operations"])
        self.assertEqual("32.50", report["totals"]["monthly_estimate"])

    def test_separates_variable_and_fixed_costs(self):
        totals = estimate(sample_plan())["totals"]
        self.assertEqual("7.50", totals["variable"])
        self.assertEqual("25.00", totals["fixed"])

    def test_defaults_optional_costs_to_zero(self):
        plan = {"workflows": [{"name": "Heartbeat", "runs_per_day": 1}]}
        self.assertEqual("0.00", estimate(plan)["totals"]["monthly_estimate"])

    def test_rounds_money_half_up(self):
        plan = {"workflows": [{"name": "Small", "runs_per_day": 1, "cost_per_1000_runs": "0.50"}]}
        self.assertEqual("0.02", estimate(plan)["totals"]["monthly_estimate"])

    def test_rejects_duplicate_names(self):
        plan = sample_plan(); plan["workflows"].append({"name": "lead INTAKE", "runs_per_day": 1})
        with self.assertRaises(InputError): estimate(plan)

    def test_rejects_negative_values(self):
        plan = sample_plan(); plan["workflows"][0]["runs_per_day"] = -1
        with self.assertRaises(InputError): estimate(plan)

    def test_rejects_boolean_as_number(self):
        plan = sample_plan(); plan["days_per_month"] = True
        with self.assertRaises(InputError): estimate(plan)

    def test_rejects_unknown_fields(self):
        plan = sample_plan(); plan["token"] = "secret"
        with self.assertRaises(InputError): estimate(plan)

    def test_requires_workflows(self):
        with self.assertRaises(InputError): estimate({"workflows": []})

    def test_text_contains_totals_and_caveat(self):
        output = format_text(estimate(sample_plan()))
        self.assertIn("Monthly estimate: 32.50 USD", output)
        self.assertIn("Estimate only", output)

    def test_loader_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "plan.json"
            path.write_text('{"workflows":[],"workflows":[]}', encoding="utf-8")
            with self.assertRaises(InputError): load_json(path)

    def test_report_is_json_serializable(self):
        json.dumps(estimate(sample_plan()))


if __name__ == "__main__":
    unittest.main()
