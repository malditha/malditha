import json
import tempfile
import unittest
from pathlib import Path
from api_contract_test_starter import ContractError, generate_plan, load_contract, matches_type, validate_contract

VALID = {
    "name": "Lookup", "method": "GET", "path": "/items/{id}",
    "parameters": [
        {"name": "id", "in": "path", "type": "integer", "required": True, "example": 7},
        {"name": "verbose", "in": "query", "type": "boolean", "required": False, "example": False},
    ],
    "response": {"status": 200, "required_fields": {"id": "integer", "label": "string"}},
}

class ContractTests(unittest.TestCase):
    def test_generates_deterministic_cases(self):
        plan = generate_plan(validate_contract(VALID))
        self.assertEqual(plan["case_count"], 9)
        self.assertEqual(plan["cases"][0]["id"], "valid-baseline")
        self.assertEqual(plan["cases"][1]["id"], "missing-id")

    def test_baseline_uses_only_declared_examples(self):
        plan = generate_plan(validate_contract(VALID))
        self.assertEqual(plan["cases"][0]["request"], {"id": 7, "verbose": False})

    def test_required_parameter_creates_missing_case(self):
        ids = [case["id"] for case in generate_plan(validate_contract(VALID))["cases"]]
        self.assertIn("missing-id", ids)
        self.assertNotIn("missing-verbose", ids)

    def test_each_parameter_creates_wrong_type_case(self):
        ids = [case["id"] for case in generate_plan(validate_contract(VALID))["cases"]]
        self.assertIn("wrong-type-id", ids)
        self.assertIn("wrong-type-verbose", ids)

    def test_response_fields_create_missing_and_wrong_type_cases(self):
        ids = [case["id"] for case in generate_plan(validate_contract(VALID))["cases"]]
        self.assertIn("missing-response-label", ids)
        self.assertIn("wrong-response-type-label", ids)

    def test_rejects_optional_path_parameter(self):
        invalid = json.loads(json.dumps(VALID)); invalid["parameters"][0]["required"] = False
        with self.assertRaisesRegex(ContractError, "must be required"):
            validate_contract(invalid)

    def test_rejects_example_type_mismatch(self):
        invalid = json.loads(json.dumps(VALID)); invalid["parameters"][0]["example"] = "seven"
        with self.assertRaisesRegex(ContractError, "does not match"):
            validate_contract(invalid)

    def test_rejects_duplicate_parameter_names(self):
        invalid = json.loads(json.dumps(VALID)); invalid["parameters"].append(dict(invalid["parameters"][0]))
        with self.assertRaisesRegex(ContractError, "duplicate parameter"):
            validate_contract(invalid)

    def test_rejects_unknown_contract_field(self):
        invalid = dict(VALID, secret="no")
        with self.assertRaisesRegex(ContractError, "unknown field"):
            validate_contract(invalid)

    def test_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text('{"name":"A","name":"B"}', encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate JSON key"):
                load_contract(path)

    def test_bool_is_not_integer(self):
        self.assertFalse(matches_type(True, "integer"))

    def test_rejects_non_finite_numbers(self):
        self.assertFalse(matches_type(float("inf"), "number"))

if __name__ == "__main__":
    unittest.main()
