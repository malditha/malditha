#!/usr/bin/env python3
"""Generate deterministic API contract test cases from a small JSON contract."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

MAX_BYTES = 256 * 1024
MAX_PARAMETERS = 100
MAX_RESPONSE_FIELDS = 100
TYPES = {"string", "integer", "number", "boolean", "object", "array", "null"}
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

class ContractError(ValueError):
    pass

def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def load_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"input file not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise ContractError(f"input exceeds {MAX_BYTES} bytes")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contract: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError("contract must be a JSON object")
    return validate_contract(data)

def require_keys(value: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ContractError(f"{context} has unknown field(s): {', '.join(sorted(unknown))}")

def validate_name(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 80:
        raise ContractError(f"{context} must be a non-empty string of at most 80 characters")
    return value.strip()

def validate_parameters(value: Any, context: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_PARAMETERS:
        raise ContractError(f"{context} must be an array with at most {MAX_PARAMETERS} entries")
    output, names = [], set()
    for index, item in enumerate(value):
        label = f"{context}[{index}]"
        if not isinstance(item, dict):
            raise ContractError(f"{label} must be an object")
        require_keys(item, {"name", "in", "type", "required", "example"}, label)
        name = validate_name(item.get("name"), f"{label}.name")
        if name in names:
            raise ContractError(f"duplicate parameter name: {name}")
        names.add(name)
        location = item.get("in")
        if location not in {"path", "query", "header", "body"}:
            raise ContractError(f"{label}.in must be path, query, header, or body")
        data_type = item.get("type")
        if data_type not in TYPES - {"null"}:
            raise ContractError(f"{label}.type is unsupported")
        required = item.get("required", False)
        if not isinstance(required, bool):
            raise ContractError(f"{label}.required must be boolean")
        if location == "path" and not required:
            raise ContractError(f"path parameter {name} must be required")
        example = item.get("example", sample_for(data_type))
        if not matches_type(example, data_type):
            raise ContractError(f"{label}.example does not match {data_type}")
        output.append({"name": name, "in": location, "type": data_type, "required": required, "example": example})
    return output

def validate_contract(data: dict[str, Any]) -> dict[str, Any]:
    require_keys(data, {"name", "method", "path", "parameters", "response"}, "contract")
    name = validate_name(data.get("name"), "name")
    method = data.get("method")
    if not isinstance(method, str) or method.upper() not in METHODS:
        raise ContractError("method must be GET, POST, PUT, PATCH, or DELETE")
    path = data.get("path")
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 200:
        raise ContractError("path must start with / and contain at most 200 characters")
    parameters = validate_parameters(data.get("parameters"), "parameters")
    response = data.get("response")
    if not isinstance(response, dict):
        raise ContractError("response must be an object")
    require_keys(response, {"status", "required_fields"}, "response")
    status = response.get("status")
    if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
        raise ContractError("response.status must be an integer from 100 to 599")
    fields = response.get("required_fields", {})
    if not isinstance(fields, dict) or len(fields) > MAX_RESPONSE_FIELDS:
        raise ContractError(f"response.required_fields must be an object with at most {MAX_RESPONSE_FIELDS} entries")
    normalized_fields: dict[str, str] = {}
    for field, data_type in fields.items():
        field = validate_name(field, "response field name")
        if data_type not in TYPES:
            raise ContractError(f"response field {field} has unsupported type")
        normalized_fields[field] = data_type
    return {"name": name, "method": method.upper(), "path": path, "parameters": parameters, "response": {"status": status, "required_fields": normalized_fields}}

def matches_type(value: Any, data_type: str) -> bool:
    if data_type == "null": return value is None
    if data_type == "boolean": return isinstance(value, bool)
    if data_type == "integer": return isinstance(value, int) and not isinstance(value, bool)
    if data_type == "number": return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if data_type == "string": return isinstance(value, str)
    if data_type == "object": return isinstance(value, dict)
    if data_type == "array": return isinstance(value, list)
    return False

def sample_for(data_type: str) -> Any:
    return {"string": "sample", "integer": 1, "number": 1.5, "boolean": True, "object": {}, "array": [], "null": None}[data_type]

def wrong_for(data_type: str) -> Any:
    return "not-a-number" if data_type in {"integer", "number"} else 42 if data_type == "string" else "not-a-boolean" if data_type == "boolean" else "not-an-object" if data_type == "object" else "not-an-array"

def generate_plan(contract: dict[str, Any]) -> dict[str, Any]:
    base_request = {p["name"]: p["example"] for p in contract["parameters"] if p["required"] or "example" in p}
    fields = contract["response"]["required_fields"]
    base_response = {name: sample_for(kind) for name, kind in fields.items()}
    cases: list[dict[str, Any]] = [{
        "id": "valid-baseline", "area": "request-and-response", "mutation": "none",
        "request": base_request, "response": {"status": contract["response"]["status"], "body": base_response},
        "expected": "contract-pass"
    }]
    for parameter in contract["parameters"]:
        if parameter["required"]:
            request = dict(base_request); request.pop(parameter["name"], None)
            cases.append({"id": f"missing-{parameter['name']}", "area": "request", "mutation": "remove-required-parameter", "target": parameter["name"], "request": request, "expected": "request-invalid"})
        request = dict(base_request); request[parameter["name"]] = wrong_for(parameter["type"])
        cases.append({"id": f"wrong-type-{parameter['name']}", "area": "request", "mutation": "replace-with-wrong-type", "target": parameter["name"], "request": request, "expected": "request-invalid"})
    cases.append({"id": "unexpected-status", "area": "response", "mutation": "replace-status", "response": {"status": 500 if contract["response"]["status"] != 500 else 400, "body": base_response}, "expected": "contract-fail"})
    for field, kind in fields.items():
        body = dict(base_response); body.pop(field)
        cases.append({"id": f"missing-response-{field}", "area": "response", "mutation": "remove-required-field", "target": field, "response": {"status": contract["response"]["status"], "body": body}, "expected": "contract-fail"})
        body = dict(base_response); body[field] = wrong_for(kind) if kind != "null" else "not-null"
        cases.append({"id": f"wrong-response-type-{field}", "area": "response", "mutation": "replace-with-wrong-type", "target": field, "response": {"status": contract["response"]["status"], "body": body}, "expected": "contract-fail"})
    return {"contract": {"name": contract["name"], "method": contract["method"], "path": contract["path"]}, "case_count": len(cases), "cases": cases}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        plan = generate_plan(load_contract(args.contract))
        rendered = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (ContractError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
