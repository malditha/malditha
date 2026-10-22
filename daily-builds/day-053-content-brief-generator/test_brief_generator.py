import json
import tempfile
import unittest
from pathlib import Path

from brief_generator import InputError, build_brief, format_markdown, load_json


def sample_request():
    return {
        "title": "Webhook safety checklist",
        "goal": "educate",
        "audience": "small automation teams",
        "channel": "article",
        "problem": "Debug payloads may contain credentials.",
        "takeaway": "Sanitize payloads before sharing them.",
        "evidence": ["Local sanitizer output", "Approved security policy"],
        "must_include": ["Human review"],
        "avoid": ["Guaranteed-safety claims"],
        "call_to_action": "Review one sample payload.",
        "tone": "clear and practical",
    }


class ContentBriefGeneratorTests(unittest.TestCase):
    def test_builds_expected_object(self):
        brief = build_brief(sample_request())
        self.assertEqual("educate", brief["objective"]["goal"])
        self.assertEqual("Sanitize payloads before sharing them.", brief["single_takeaway"])

    def test_normalizes_whitespace(self):
        request = sample_request()
        request["audience"] = "  small   automation teams  "
        self.assertEqual("small automation teams", build_brief(request)["objective"]["audience"])

    def test_adds_evidence_section_only_when_evidence_exists(self):
        brief = build_brief(sample_request())
        self.assertIn("Evidence", [item["heading"] for item in brief["sections"]])
        request = sample_request()
        request["evidence"] = []
        self.assertNotIn("Evidence", [item["heading"] for item in build_brief(request)["sections"]])

    def test_uses_generic_next_step_without_cta(self):
        request = sample_request()
        request.pop("call_to_action")
        brief = build_brief(request)
        self.assertIsNone(brief["call_to_action"])
        self.assertIn("non-pushy", brief["sections"][-1]["purpose"])

    def test_rejects_unsupported_channel(self):
        request = sample_request()
        request["channel"] = "billboard"
        with self.assertRaises(InputError):
            build_brief(request)

    def test_rejects_unknown_fields(self):
        request = sample_request()
        request["secret_prompt"] = "hidden"
        with self.assertRaises(InputError):
            build_brief(request)

    def test_rejects_duplicate_list_items_case_insensitively(self):
        request = sample_request()
        request["avoid"] = ["Hype", "hype"]
        with self.assertRaises(InputError):
            build_brief(request)

    def test_rejects_oversized_list(self):
        request = sample_request()
        request["evidence"] = [str(index) for index in range(13)]
        with self.assertRaises(InputError):
            build_brief(request)

    def test_markdown_contains_core_sections(self):
        output = format_markdown(build_brief(sample_request()))
        self.assertIn("# Webhook safety checklist", output)
        self.assertIn("## Editorial checks", output)
        self.assertIn("Review one sample payload.", output)

    def test_loader_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "request.json"
            path.write_text('{"title":"One","title":"Two"}', encoding="utf-8")
            with self.assertRaises(InputError):
                load_json(path)

    def test_result_is_json_serializable(self):
        json.dumps(build_brief(sample_request()))


if __name__ == "__main__":
    unittest.main()
