import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nginx_config_checklist import ConfigError, audit_config, parse_config


class NginxConfigChecklistTests(unittest.TestCase):
    def test_parses_comments_quotes_and_nested_blocks(self):
        nodes = parse_config('http { server { server_name "example.test"; # note\n location / { proxy_pass http://app; } } }')
        report = audit_config(nodes)
        self.assertEqual(report["summary"]["servers"], 1)
        self.assertEqual(report["servers"][0]["server_names"], ["example.test"])
        self.assertEqual(report["servers"][0]["mode"], "proxy")

    def test_rejects_unbalanced_blocks(self):
        with self.assertRaisesRegex(ConfigError, "unclosed block"):
            parse_config("http { server { listen 80; }")

    def test_requires_directive_semicolon(self):
        with self.assertRaisesRegex(ConfigError, "expected"):
            parse_config("events { worker_connections 64 }")

    def test_reports_missing_listen_and_server_name(self):
        report = audit_config(parse_config("http { server { root /srv/site; } }"))
        rules = {item["rule"] for item in report["findings"]}
        self.assertEqual(rules, {"missing-listen", "missing-server-name"})

    def test_reports_incomplete_tls_pair(self):
        config = "http { server { listen 443 ssl; server_name secure.test; ssl_certificate /cert.pem; } }"
        report = audit_config(parse_config(config))
        finding = next(item for item in report["findings"] if item["rule"] == "tls-pair-incomplete")
        self.assertEqual(finding["severity"], "high")
        self.assertNotIn("/cert.pem", json.dumps(report))

    def test_accepts_complete_tls_pair(self):
        config = "http { server { listen 443 ssl; server_name secure.test; ssl_certificate /cert.pem; ssl_certificate_key /key.pem; } }"
        report = audit_config(parse_config(config))
        self.assertNotIn("tls-pair-incomplete", {item["rule"] for item in report["findings"]})

    def test_reports_autoindex_in_nested_location(self):
        config = "http { server { listen 80; server_name files.test; location / { autoindex on; } } }"
        report = audit_config(parse_config(config))
        self.assertIn("autoindex-enabled", {item["rule"] for item in report["findings"]})

    def test_reports_duplicate_route(self):
        config = "http { server { listen 80; server_name same.test; } server { listen 80; server_name same.test; } }"
        report = audit_config(parse_config(config))
        duplicate = [item for item in report["findings"] if item["rule"] == "duplicate-route"]
        self.assertEqual(len(duplicate), 2)

    def test_reports_unresolved_include(self):
        report = audit_config(parse_config("http { include /etc/nginx/conf.d/*.conf; }"))
        self.assertEqual(report["findings"][0]["rule"], "unresolved-include")
        self.assertNotIn("/etc/nginx", json.dumps(report))

    def test_cli_emits_json_and_review_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nginx.conf"
            path.write_text("http { server { root /srv/site; } }", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "nginx_config_checklist.py", str(path), "--json"],
                cwd=Path(__file__).parent,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["summary"]["servers"], 1)

    def test_rejects_more_than_one_hundred_server_blocks(self):
        source = "http {" + " server { listen 80; server_name test; }" * 101 + " }"
        with self.assertRaisesRegex(ConfigError, "100-server limit"):
            audit_config(parse_config(source))


if __name__ == "__main__":
    unittest.main()
