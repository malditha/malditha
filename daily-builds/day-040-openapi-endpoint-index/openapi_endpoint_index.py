#!/usr/bin/env python3
"""Create a compact, deterministic index from a local OpenAPI 3.x JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 2_000_000
MAX_ENDPOINTS = 500
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head", "trace")
METHOD_ORDER = {method: index for index, method in enumerate(HTTP_METHODS)}


class DocumentError(ValueError):
    """Raised when an input document is unsafe or structurally invalid."""


def _text(value: Any, fallback: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def load_document(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise DocumentError("input exceeds the 2 MB size limit")
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DocumentError(f"file not found: {path}") from exc
    except OSError as exc:
        raise DocumentError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DocumentError(f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(value, dict):
        raise DocumentError("the OpenAPI document must be a JSON object")
    return value


def build_index(document: dict[str, Any]) -> dict[str, Any]:
    version = _text(document.get("openapi"))
    if not version.startswith("3."):
        raise DocumentError("only OpenAPI 3.x documents are supported")

    info = document.get("info", {})
    if not isinstance(info, dict):
        raise DocumentError("info must be an object")
    paths = document.get("paths")
    if not isinstance(paths, dict):
        raise DocumentError("paths must be an object")

    endpoints: list[dict[str, Any]] = []
    tag_counts: Counter[str] = Counter()

    for path_name, path_item in paths.items():
        if not isinstance(path_name, str) or not path_name.startswith("/"):
            raise DocumentError("every path key must start with /")
        if not isinstance(path_item, dict):
            raise DocumentError(f"path item {path_name} must be an object")
        shared_parameters = path_item.get("parameters", [])
        if not isinstance(shared_parameters, list):
            raise DocumentError(f"parameters for {path_name} must be an array")

        for method in HTTP_METHODS:
            if method not in path_item:
                continue
            operation = path_item[method]
            if not isinstance(operation, dict):
                raise DocumentError(f"operation {method.upper()} {path_name} must be an object")
            operation_parameters = operation.get("parameters", [])
            if not isinstance(operation_parameters, list):
                raise DocumentError(f"parameters for {method.upper()} {path_name} must be an array")
            raw_tags = operation.get("tags", [])
            if not isinstance(raw_tags, list) or any(not isinstance(tag, str) for tag in raw_tags):
                raise DocumentError(f"tags for {method.upper()} {path_name} must be strings")
            tags = sorted({tag.strip() for tag in raw_tags if tag.strip()})
            for tag in tags or ["Untagged"]:
                tag_counts[tag] += 1
            responses = operation.get("responses", {})
            if not isinstance(responses, dict):
                raise DocumentError(f"responses for {method.upper()} {path_name} must be an object")
            endpoints.append(
                {
                    "method": method.upper(),
                    "path": path_name,
                    "operation_id": _text(operation.get("operationId")),
                    "summary": _text(operation.get("summary"), "No summary provided"),
                    "tags": tags,
                    "deprecated": operation.get("deprecated") is True,
                    "parameter_count": len(shared_parameters) + len(operation_parameters),
                    "response_codes": sorted(str(code) for code in responses),
                }
            )
            if len(endpoints) > MAX_ENDPOINTS:
                raise DocumentError(f"document exceeds the {MAX_ENDPOINTS}-endpoint limit")

    endpoints.sort(key=lambda item: (item["path"], METHOD_ORDER[item["method"].lower()]))
    return {
        "api": {
            "title": _text(info.get("title"), "Untitled API"),
            "version": _text(info.get("version"), "Unversioned"),
            "openapi": version,
        },
        "endpoint_count": len(endpoints),
        "tag_counts": dict(sorted(tag_counts.items())),
        "endpoints": endpoints,
    }


def format_text(report: dict[str, Any]) -> str:
    api = report["api"]
    lines = [
        f"{api['title']} {api['version']} (OpenAPI {api['openapi']})",
        f"{report['endpoint_count']} endpoint(s)",
        "",
    ]
    for item in report["endpoints"]:
        flags = " [DEPRECATED]" if item["deprecated"] else ""
        identity = f" · {item['operation_id']}" if item["operation_id"] else ""
        tags = f" · {', '.join(item['tags'])}" if item["tags"] else " · Untagged"
        lines.append(f"{item['method']:<6} {item['path']}{flags}")
        lines.append(f"       {item['summary']}{identity}{tags}")
        lines.append(
            f"       {item['parameter_count']} parameter(s) · responses: "
            f"{', '.join(item['response_codes']) or 'none declared'}"
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path, help="local OpenAPI 3.x JSON file")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--output", type=Path, help="write the report to a file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_index(load_document(args.document))
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.json else format_text(report)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (DocumentError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
