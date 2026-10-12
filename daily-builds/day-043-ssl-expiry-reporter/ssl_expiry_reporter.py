#!/usr/bin/env python3
"""Report TLS certificate expiry for a small, explicit endpoint list."""

from __future__ import annotations

import argparse
import json
import math
import socket
import ssl
from collections import Counter
from datetime import datetime, timezone
from typing import Callable, Iterable


MAX_ENDPOINTS = 20
Connector = Callable[[str, int, float], dict]


def parse_endpoint(value: str) -> tuple[str, int]:
    raw = value.strip()
    if not raw or "/" in raw or raw.count(":") > 1:
        raise ValueError(f"invalid endpoint: {value!r}")
    host, separator, port_text = raw.partition(":")
    try:
        ascii_host = host.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError(f"invalid hostname: {host!r}") from exc
    if not ascii_host or len(ascii_host) > 253 or any(
        not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
        for label in ascii_host.split(".")
    ):
        raise ValueError(f"invalid hostname: {host!r}")
    if any(not (character.isalnum() or character in "-_") for character in ascii_host.replace(".", "")):
        raise ValueError(f"invalid hostname: {host!r}")
    if separator:
        if not port_text.isdigit():
            raise ValueError(f"invalid port: {port_text!r}")
        port = int(port_text)
    else:
        port = 443
    if not 1 <= port <= 65535:
        raise ValueError(f"port must be between 1 and 65535: {port}")
    return ascii_host, port


def normalize_endpoints(values: Iterable[str]) -> list[tuple[str, int]]:
    parsed = [parse_endpoint(value) for value in values]
    if len(parsed) > MAX_ENDPOINTS:
        raise ValueError(f"at most {MAX_ENDPOINTS} endpoints may be checked")
    return list(dict.fromkeys(parsed))


def validate_thresholds(warning_days: int, critical_days: int) -> None:
    if not 0 <= critical_days < warning_days <= 3650:
        raise ValueError("critical days must be non-negative and lower than warning days")


def classify_expiry(
    not_after: datetime,
    now: datetime,
    warning_days: int,
    critical_days: int,
) -> dict:
    validate_thresholds(warning_days, critical_days)
    if not_after.tzinfo is None or now.tzinfo is None:
        raise ValueError("certificate and comparison times must include a timezone")
    seconds_remaining = (not_after.astimezone(timezone.utc) - now.astimezone(timezone.utc)).total_seconds()
    days_remaining = math.floor(seconds_remaining / 86400)
    if seconds_remaining < 0:
        status = "expired"
    elif days_remaining <= critical_days:
        status = "critical"
    elif days_remaining <= warning_days:
        status = "warning"
    else:
        status = "healthy"
    return {"status": status, "days_remaining": days_remaining}


def verified_certificate(host: str, port: int, timeout: float) -> dict:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as plain_socket:
        with context.wrap_socket(plain_socket, server_hostname=host) as tls_socket:
            return tls_socket.getpeercert()


def _certificate_time(value: str) -> datetime:
    try:
        timestamp = ssl.cert_time_to_seconds(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("certificate has an invalid notAfter field") from exc
    return datetime.fromtimestamp(timestamp, timezone.utc)


def inspect_endpoint(
    endpoint: tuple[str, int],
    timeout: float,
    now: datetime,
    warning_days: int,
    critical_days: int,
    connector: Connector = verified_certificate,
) -> dict:
    host, port = endpoint
    label = f"{host}:{port}"
    try:
        certificate = connector(host, port, timeout)
        not_after = _certificate_time(certificate.get("notAfter"))
        result = classify_expiry(not_after, now, warning_days, critical_days)
        return {
            "endpoint": label,
            **result,
            "not_after": not_after.isoformat().replace("+00:00", "Z"),
        }
    except TimeoutError:
        return {"endpoint": label, "status": "error", "error": "timeout"}
    except ssl.SSLCertVerificationError:
        return {"endpoint": label, "status": "error", "error": "certificate verification failed"}
    except ssl.SSLError:
        return {"endpoint": label, "status": "error", "error": "TLS handshake failed"}
    except (ConnectionError, OSError):
        return {"endpoint": label, "status": "error", "error": "connection failed"}
    except ValueError as exc:
        return {"endpoint": label, "status": "error", "error": str(exc)}


def build_report(results: list[dict], warning_days: int, critical_days: int) -> dict:
    counts = Counter(result["status"] for result in results)
    return {
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "thresholds": {"warning_days": warning_days, "critical_days": critical_days},
        "summary": {status: counts.get(status, 0) for status in ("healthy", "warning", "critical", "expired", "error")},
        "results": results,
    }


def render_text(report: dict) -> str:
    lines = ["SSL EXPIRY REPORT", f"Checked endpoints: {len(report['results'])}"]
    for result in report["results"]:
        detail = result.get("error") or f"{result['days_remaining']} days · expires {result['not_after']}"
        lines.append(f"[{result['status'].upper()}] {result['endpoint']} — {detail}")
    summary = report["summary"]
    lines.append(
        "Summary: " + ", ".join(f"{name}={summary[name]}" for name in ("healthy", "warning", "critical", "expired", "error"))
    )
    return "\n".join(lines)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("endpoints", nargs="+", help="Authorized host or host:port (maximum 20)")
    parser.add_argument("--warning-days", type=int, default=30)
    parser.add_argument("--critical-days", type=int, default=7)
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-endpoint timeout in seconds (0.1–30)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        endpoints = normalize_endpoints(args.endpoints)
        validate_thresholds(args.warning_days, args.critical_days)
        if not 0.1 <= args.timeout <= 30:
            raise ValueError("timeout must be between 0.1 and 30 seconds")
    except ValueError as exc:
        make_parser().error(str(exc))

    now = datetime.now(timezone.utc)
    results = [
        inspect_endpoint(endpoint, args.timeout, now, args.warning_days, args.critical_days)
        for endpoint in endpoints
    ]
    report = build_report(results, args.warning_days, args.critical_days)
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    return 1 if any(result["status"] != "healthy" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
