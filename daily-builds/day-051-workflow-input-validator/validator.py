#!/usr/bin/env python3
"""Validate one local workflow payload against a small declarative contract."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 1_000_000
MAX_FIELDS = 100
FIELD_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}
RULE_KEYS = {
    "type",
    "required",
    "min_length",
    "max_length",
    "enum",
    "min_items",
    "max_items",
    "item_type",
    "minimum",
    "maximum",
}


class InputError(ValueError):
    """Raised when a contract or payload cannot be safely processed."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key")
        result[key] = value
    return result


def load_json_file(path: Path) -> Any:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise InputError("file exceeds size limit")
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except InputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("unable to read JSON input") from exc


def _is_value_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and not (isinstance(value, float) and not math.isfinite(value))
        )
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return value is None


def _bounded_integer(rule: dict[str, Any], key: str) -> int | None:
    value = rule.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 10_000:
        raise InputError("invalid numeric rule")
    return value


def _validate_contract(contract: Any) -> tuple[str, dict[str, dict[str, Any]]]:
    if not isinstance(contract, dict) or set(contract) - {"unknown_fields", "fields"}:
        raise InputError("invalid contract")
    policy = contract.get("unknown_fields", "reject")
    fields = contract.get("fields")
    if policy not in {"allow", "reject"} or not isinstance(fields, dict):
        raise InputError("invalid contract")
    if not 1 <= len(fields) <= MAX_FIELDS:
        raise InputError("invalid field count")

    for name, rule in fields.items():
        if not isinstance(name, str) or not FIELD_NAME.fullmatch(name) or not isinstance(rule, dict):
            raise InputError("invalid field rule")
        if set(rule) - RULE_KEYS:
            raise InputError("unsupported field rule")
        expected = rule.get("type")
        if expected not in SUPPORTED_TYPES or not isinstance(rule.get("required", False), bool):
            raise InputError("invalid field rule")
        minimum_length = _bounded_integer(rule, "min_length")
        maximum_length = _bounded_integer(rule, "max_length")
        minimum_items = _bounded_integer(rule, "min_items")
        maximum_items = _bounded_integer(rule, "max_items")
        if minimum_length is not None and maximum_length is not None and minimum_length > maximum_length:
            raise InputError("invalid string bounds")
        if minimum_items is not None and maximum_items is not None and minimum_items > maximum_items:
            raise InputError("invalid array bounds")
        if any(key in rule for key in {"min_length", "max_length", "enum"}) and expected != "string":
            raise InputError("string rule on non-string field")
        if any(key in rule for key in {"min_items", "max_items", "item_type"}) and expected != "array":
            raise InputError("array rule on non-array field")
        if any(key in rule for key in {"minimum", "maximum"}) and expected not in {"integer", "number"}:
            raise InputError("numeric rule on non-number field")
        enum = rule.get("enum")
        if enum is not None and (
            not isinstance(enum, list)
            or not 1 <= len(enum) <= 50
            or any(not isinstance(item, str) or not 1 <= len(item) <= 128 for item in enum)
            or len(set(enum)) != len(enum)
        ):
            raise InputError("invalid enum")
        item_type = rule.get("item_type")
        if item_type is not None and item_type not in SUPPORTED_TYPES:
            raise InputError("invalid item type")
        for key in ("minimum", "maximum"):
            bound = rule.get(key)
            if bound is not None and (
                not isinstance(bound, (int, float))
                or isinstance(bound, bool)
                or not math.isfinite(bound)
            ):
                raise InputError("invalid numeric bound")
        if (
            rule.get("minimum") is not None
            and rule.get("maximum") is not None
            and rule["minimum"] > rule["maximum"]
        ):
            raise InputError("invalid numeric bounds")
    return policy, fields


def _issue(field: str, code: str, message: str) -> dict[str, str]:
    return {"field": field, "code": code, "message": message}


def validate_payload(contract: Any, payload: Any) -> dict[str, Any]:
    policy, fields = _validate_contract(contract)
    if not isinstance(payload, dict) or len(payload) > MAX_FIELDS:
        raise InputError("payload must be a bounded JSON object")
    if any(not isinstance(key, str) or not FIELD_NAME.fullmatch(key) for key in payload):
        raise InputError("invalid payload field name")

    issues: list[dict[str, str]] = []
    for name, rule in fields.items():
        if name not in payload:
            if rule.get("required", False):
                issues.append(_issue(name, "required", "required field is missing"))
            continue
        value = payload[name]
        expected = rule["type"]
        if not _is_value_type(value, expected):
            issues.append(_issue(name, "type", f"field must have type {expected}"))
            continue
        if expected == "string":
            if "min_length" in rule and len(value) < rule["min_length"]:
                issues.append(_issue(name, "min_length", "string is shorter than the allowed minimum"))
            if "max_length" in rule and len(value) > rule["max_length"]:
                issues.append(_issue(name, "max_length", "string exceeds the allowed maximum"))
            if "enum" in rule and value not in rule["enum"]:
                issues.append(_issue(name, "enum", "string is not one of the allowed choices"))
        elif expected == "array":
            if "min_items" in rule and len(value) < rule["min_items"]:
                issues.append(_issue(name, "min_items", "array has fewer than the allowed items"))
            if "max_items" in rule and len(value) > rule["max_items"]:
                issues.append(_issue(name, "max_items", "array exceeds the allowed item count"))
            item_type = rule.get("item_type")
            if item_type and any(not _is_value_type(item, item_type) for item in value):
                issues.append(_issue(name, "item_type", f"array items must have type {item_type}"))
        elif expected in {"integer", "number"}:
            if "minimum" in rule and value < rule["minimum"]:
                issues.append(_issue(name, "minimum", "number is below the allowed minimum"))
            if "maximum" in rule and value > rule["maximum"]:
                issues.append(_issue(name, "maximum", "number exceeds the allowed maximum"))

    if policy == "reject":
        for name in sorted(set(payload) - set(fields)):
            issues.append(_issue(name, "unknown_field", "field is not declared by the contract"))

    return {
        "status": "invalid" if issues else "valid",
        "checked_fields": len(fields),
        "issue_count": len(issues),
        "issues": issues,
    }


def format_text(report: dict[str, Any]) -> str:
    lines = [
        "Workflow Input Validator",
        f"Status: {report['status'].upper()}",
        f"Checked fields: {report['checked_fields']}",
        f"Issues: {report['issue_count']}",
    ]
    for issue in report["issues"]:
        lines.append(f"- {issue['field']}: {issue['code']} — {issue['message']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        report = validate_payload(load_json_file(args.contract), load_json_file(args.payload))
    except InputError:
        print("Input error: unable to validate the supplied files.", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.as_json else format_text(report))
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
