import json
import tempfile
import unittest
from pathlib import Path

from docker_compose_auditor import AuditError, audit_compose, format_text, load_document, main


SAFE = {
    "name": "demo",
    "services": {
        "web": {
            "image": "nginx:1.27.4",
            "healthcheck": {"test": ["CMD", "curl", "-f", "http://localhost"]},
            "read_only": True,
            "ports": [{"target": 80, "published": "8080", "host_ip": "127.0.0.1"}],
        }
    },
}


class DockerComposeAuditorTests(unittest.TestCase):
    def test_safe_service_has_no_findings(self):
        report = audit_compose(SAFE)
        self.assertEqual(report["summary"], {"services": 1, "high": 0, "warning": 0, "info": 0})
        self.assertEqual(report["findings"], [])

    def test_flags_latest_or_unpinned_image(self):
        document = {"services": {"a": {"image": "redis:latest"}, "b": {"image": "nginx"}}}
        rules = [item["rule"] for item in audit_compose(document)["findings"] if item["rule"] == "image-unpinned"]
        self.assertEqual(rules, ["image-unpinned", "image-unpinned"])

    def test_flags_privileged_and_host_network(self):
        document = {"services": {"worker": {"image": "demo:1", "privileged": True, "network_mode": "host"}}}
        findings = audit_compose(document)["findings"]
        self.assertEqual([(item["rule"], item["severity"]) for item in findings[:2]], [("host-network", "high"), ("privileged", "high")])

    def test_flags_public_published_port(self):
        document = {"services": {"web": {"image": "demo:1", "ports": ["8080:80", "127.0.0.1:9090:90"]}}}
        findings = audit_compose(document)["findings"]
        self.assertIn("public-port", [item["rule"] for item in findings])
        public = next(item for item in findings if item["rule"] == "public-port")
        self.assertEqual(public["evidence"], "8080")

    def test_flags_writable_host_bind(self):
        document = {"services": {"web": {"image": "demo:1", "volumes": ["/srv/data:/data", "/srv/config:/config:ro"]}}}
        findings = audit_compose(document)["findings"]
        bind = next(item for item in findings if item["rule"] == "writable-host-bind")
        self.assertEqual(bind["evidence"], "/srv/data")

    def test_flags_missing_healthcheck_as_info(self):
        document = {"services": {"worker": {"image": "demo:1"}}}
        findings = audit_compose(document)["findings"]
        self.assertIn({"service": "worker", "severity": "info", "rule": "no-healthcheck", "evidence": "not configured"}, findings)

    def test_never_includes_environment_values(self):
        document = {"services": {"api": {"image": "demo:1", "environment": {"PASSWORD": "secret-value", "MODE": "prod"}}}}
        output = json.dumps(audit_compose(document))
        self.assertNotIn("secret-value", output)
        self.assertNotIn("prod", output)
        self.assertIn("PASSWORD", output)

    def test_rejects_invalid_or_oversized_service_maps(self):
        with self.assertRaises(AuditError):
            audit_compose({"services": []})
        too_many = {"services": {f"service-{index}": {} for index in range(101)}}
        with self.assertRaisesRegex(AuditError, "100"):
            audit_compose(too_many)

    def test_load_document_rejects_invalid_json_and_large_files(self):
        with tempfile.TemporaryDirectory() as folder:
            invalid = Path(folder) / "bad.json"
            invalid.write_text("{bad", encoding="utf-8")
            with self.assertRaises(AuditError):
                load_document(invalid)
            large = Path(folder) / "large.json"
            large.write_text(" " * 2_000_001, encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "2 MB"):
                load_document(large)

    def test_text_and_cli_outputs_are_deterministic(self):
        document = {"services": {"z": {"image": "demo:latest"}, "a": {"image": "demo:1", "privileged": True}}}
        text = format_text(audit_compose(document))
        self.assertLess(text.index("a · HIGH"), text.index("z · WARNING"))
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "compose.json"
            target = Path(folder) / "audit.json"
            source.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(main([str(source), "--json", "--output", str(target)]), 1)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["summary"]["services"], 2)
            self.assertEqual(main([str(Path(folder) / "missing.json")]), 2)


if __name__ == "__main__":
    unittest.main()
