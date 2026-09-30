#!/usr/bin/env python3
"""Validate and preview a bounded HTTP request without sending it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


MAX_FILE_BYTES = 65_536
MAX_URL_LENGTH = 2_048
MAX_QUERY_FIELDS = 50
MAX_HEADERS = 40
MAX_BODY_BYTES = 32_768
ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
ALLOWED_FIELDS = {"method", "url", "query", "headers", "json"}
SENSITIVE_HEADER_PARTS = ("authorization", "cookie", "token", "secret", "api-key", "apikey")
REDACTED = "[REDACTED]"


class RequestValidationError(ValueError):
    """Raised when a request specification is unsafe or malformed."""


def _string(value: Any, label: str, *, limit: int = 1_000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError(f"{label} must be a non-empty string")
    if len(value) > limit:
        raise RequestValidationError(f"{label} exceeds {limit} characters")
    return value.strip()


def _scalar(value: Any, label: str) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)) and not isinstance(value, complex):
        text = str(value)
        if len(text) > 1_000:
            raise RequestValidationError(f"{label} exceeds 1000 characters")
        return text
    raise RequestValidationError(f"{label} must be a string, number, boolean, or null")


def _is_sensitive_header(name: str) -> bool:
    normalized = name.lower().replace("_", "-")
    return any(part in normalized for part in SENSITIVE_HEADER_PARTS)


def build_request(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise RequestValidationError("request must be a JSON object")
    unknown = sorted(set(spec) - ALLOWED_FIELDS)
    if unknown:
        raise RequestValidationError(f"unknown field(s): {', '.join(unknown)}")

    method = _string(spec.get("method", "GET"), "method", limit=10).upper()
    if method not in ALLOWED_METHODS:
        raise RequestValidationError(f"unsupported method: {method}")

    raw_url = _string(spec.get("url"), "url", limit=MAX_URL_LENGTH)
    parsed = urlsplit(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RequestValidationError("url must be an absolute HTTP or HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise RequestValidationError("url must not contain credentials")
    if parsed.fragment:
        raise RequestValidationError("url must not contain a fragment")

    query = spec.get("query", {})
    if not isinstance(query, dict):
        raise RequestValidationError("query must be a JSON object")
    if len(query) > MAX_QUERY_FIELDS:
        raise RequestValidationError(f"query exceeds {MAX_QUERY_FIELDS} fields")
    pairs = list(parse_qsl(parsed.query, keep_blank_values=True))
    for key in sorted(query):
        name = _string(key, "query key", limit=200)
        value = query[key]
        values = value if isinstance(value, list) else [value]
        if len(values) > 20:
            raise RequestValidationError(f"query.{name} exceeds 20 values")
        pairs.extend((name, _scalar(item, f"query.{name}")) for item in values)
    final_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", urlencode(pairs), ""))

    headers = spec.get("headers", {})
    if not isinstance(headers, dict):
        raise RequestValidationError("headers must be a JSON object")
    if len(headers) > MAX_HEADERS:
        raise RequestValidationError(f"headers exceeds {MAX_HEADERS} entries")
    safe_headers: dict[str, str] = {}
    redacted_headers: list[str] = []
    for key in sorted(headers, key=str.lower):
        name = _string(key, "header name", limit=200)
        if any(ch in name for ch in "\r\n:"):
            raise RequestValidationError(f"invalid header name: {name}")
        value = _string(headers[key], f"header {name}", limit=4_096)
        if any(ch in value for ch in "\r\n"):
            raise RequestValidationError(f"header {name} contains a line break")
        if _is_sensitive_header(name):
            safe_headers[name] = REDACTED
            redacted_headers.append(name)
        else:
            safe_headers[name] = value

    body = spec.get("json") if "json" in spec else None
    has_body = "json" in spec
    if has_body and method in {"GET", "HEAD"}:
        raise RequestValidationError(f"{method} requests cannot include a JSON body")
    body_text = json.dumps(body, sort_keys=True, separators=(",", ":")) if has_body else None
    if body_text is not None and len(body_text.encode("utf-8")) > MAX_BODY_BYTES:
        raise RequestValidationError(f"JSON body exceeds {MAX_BODY_BYTES} bytes")

    command = ["curl", "--request", method, final_url]
    for name, value in safe_headers.items():
        command.extend(["--header", f"{name}: {value}"])
    if body_text is not None:
        command.extend(["--header", "Content-Type: application/json", "--data", body_text])

    return {
        "method": method,
        "url": final_url,
        "headers": safe_headers,
        "redacted_headers": redacted_headers,
        "json_body": body if has_body else None,
        "has_json_body": has_body,
        "curl": " ".join(shlex.quote(part) for part in command),
        "network_request_sent": False,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "API REQUEST PREVIEW",
        "===================",
        f"Method: {report['method']}",
        f"URL: {report['url']}",
        "Network request sent: no",
        "",
        "Headers:",
    ]
    if report["headers"]:
        lines.extend(f"  {key}: {value}" for key, value in report["headers"].items())
    else:
        lines.append("  (none)")
    lines.extend(["", "cURL preview:", report["curl"]])
    return "\n".join(lines)


def load_spec(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise RequestValidationError(f"input file exceeds {MAX_FILE_BYTES} bytes")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RequestValidationError(f"could not read valid JSON: {exc}") from exc
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="JSON request specification")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        report = build_request(load_spec(args.request))
    except (OSError, RequestValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
