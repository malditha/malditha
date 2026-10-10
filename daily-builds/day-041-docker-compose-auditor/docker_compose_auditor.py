#!/usr/bin/env python3
"""Audit normalized Docker Compose JSON without running Docker or containers."""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 2_000_000
MAX_SERVICES = 100
SEVERITY_ORDER = {"high": 0, "warning": 1, "info": 2}

class AuditError(ValueError):
    """Raised when the normalized Compose input is unsafe or malformed."""

def load_document(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise AuditError("input exceeds the 2 MB size limit")
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuditError(f"file not found: {path}") from exc
    except OSError as exc:
        raise AuditError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(value, dict):
        raise AuditError("Compose input must be a JSON object")
    return value

def _finding(service: str, severity: str, rule: str, evidence: str) -> dict[str, str]:
    return {"service": service, "severity": severity, "rule": rule, "evidence": evidence}

def _image_unpinned(image: Any) -> bool:
    if not isinstance(image, str) or not image.strip():
        return False
    tail = image.rsplit("/", 1)[-1]
    return "@" not in tail and (":" not in tail or tail.endswith(":latest"))

def _public_port(port: Any) -> str | None:
    if isinstance(port, dict):
        published = port.get("published")
        host_ip = str(port.get("host_ip", "")).strip()
        return str(published) if published is not None and host_ip not in {"127.0.0.1", "::1"} else None
    if not isinstance(port, str):
        return None
    parts = port.split(":")
    if len(parts) == 2:
        return parts[0]
    if len(parts) >= 3 and parts[0] not in {"127.0.0.1", "::1"}:
        return parts[-2]
    return None

def _writable_bind(volume: Any) -> str | None:
    if isinstance(volume, dict):
        if volume.get("type") == "bind" and not bool(volume.get("read_only")):
            return str(volume.get("source") or "host bind")
        return None
    if not isinstance(volume, str):
        return None
    parts = volume.split(":")
    if len(parts) >= 2 and parts[0].startswith(("/", "./", "../")):
        options = parts[2].split(",") if len(parts) >= 3 else []
        return None if "ro" in options else parts[0]
    return None

def audit_compose(document: dict[str, Any]) -> dict[str, Any]:
    services = document.get("services")
    if not isinstance(services, dict):
        raise AuditError("services must be an object")
    if len(services) > MAX_SERVICES:
        raise AuditError(f"input exceeds the {MAX_SERVICES}-service limit")
    findings: list[dict[str, str]] = []
    for service_name in sorted(services):
        service = services[service_name]
        if not isinstance(service_name, str) or not service_name.strip():
            raise AuditError("service names must be non-empty strings")
        if not isinstance(service, dict):
            raise AuditError(f"service {service_name} must be an object")
        image = service.get("image")
        if _image_unpinned(image):
            findings.append(_finding(service_name, "warning", "image-unpinned", str(image)))
        if service.get("privileged") is True:
            findings.append(_finding(service_name, "high", "privileged", "enabled"))
        if service.get("network_mode") == "host":
            findings.append(_finding(service_name, "high", "host-network", "enabled"))
        if "healthcheck" not in service:
            findings.append(_finding(service_name, "info", "no-healthcheck", "not configured"))
        ports = service.get("ports", [])
        if not isinstance(ports, list):
            raise AuditError(f"ports for {service_name} must be an array")
        for port in ports:
            published = _public_port(port)
            if published:
                findings.append(_finding(service_name, "warning", "public-port", published))
        volumes = service.get("volumes", [])
        if not isinstance(volumes, list):
            raise AuditError(f"volumes for {service_name} must be an array")
        for volume in volumes:
            source = _writable_bind(volume)
            if source:
                findings.append(_finding(service_name, "warning", "writable-host-bind", source))
        environment = service.get("environment")
        if isinstance(environment, dict) and environment:
            findings.append(_finding(service_name, "info", "environment-keys", ", ".join(sorted(str(key) for key in environment))))
        elif environment is not None and not isinstance(environment, (dict, list)):
            raise AuditError(f"environment for {service_name} must be an object or array")
    findings.sort(key=lambda item: (item["service"], SEVERITY_ORDER[item["severity"]], item["rule"], item["evidence"]))
    counts = Counter(item["severity"] for item in findings)
    return {"project": str(document.get("name") or "unnamed"), "summary": {"services": len(services), "high": counts["high"], "warning": counts["warning"], "info": counts["info"]}, "findings": findings}

def format_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [f"Docker Compose audit · {report['project']}", f"{summary['services']} service(s) · {summary['high']} high · {summary['warning']} warning · {summary['info']} info", ""]
    if not report["findings"]:
        lines.append("No findings for the focused rules in this audit.")
    for item in report["findings"]:
        lines.append(f"{item['service']} · {item['severity'].upper()} · {item['rule']} · {item['evidence']}")
    return "\n".join(lines) + "\n"

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path, help="JSON from: docker compose config --format json")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--output", type=Path, help="write the report to a file")
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = audit_compose(load_document(args.document))
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.json else format_text(report)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 1 if report["summary"]["high"] or report["summary"]["warning"] else 0
    except (AuditError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
