#!/usr/bin/env python3
"""Validate and preview bounded notification templates from local JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_BYTES = 256_000
MAX_TEMPLATES = 100
MAX_TEXT = 20_000
TOKEN = re.compile(r"{{\s*([A-Za-z][A-Za-z0-9_.-]{0,63})\s*}}")


class LabError(ValueError):
    """Raised when the input plan is unsafe or malformed."""


@dataclass(frozen=True)
class TemplateResult:
    template_id: str
    channel: str
    status: str
    placeholders: tuple[str, ...]
    missing: tuple[str, ...]
    unused: tuple[str, ...]
    subject: str | None
    body: str | None


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LabError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_plan(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_BYTES:
        raise LabError("input exceeds 256 KB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LabError(f"cannot read valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LabError("top level must be an object")
    return data


def _text(value: Any, label: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise LabError(f"{label} must be a non-empty string")
    if len(value) > MAX_TEXT:
        raise LabError(f"{label} exceeds {MAX_TEXT} characters")
    return value


def _scalar_data(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise LabError(f"{label} must be an object")
    if len(value) > 100:
        raise LabError(f"{label} has more than 100 variables")
    clean: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or TOKEN.fullmatch("{{" + key + "}}") is None:
            raise LabError(f"{label} contains an invalid variable name")
        if isinstance(item, bool) or not isinstance(item, (str, int, float)):
            raise LabError(f"{label}.{key} must be a string or number")
        clean[key] = str(item)
    return clean


def _ordered_tokens(*parts: str | None) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for part in parts:
        if part:
            for match in TOKEN.finditer(part):
                token = match.group(1)
                if token not in seen:
                    seen.add(token)
                    ordered.append(token)
    return tuple(ordered)


def _render(text: str | None, data: dict[str, str]) -> str | None:
    if text is None:
        return None
    return TOKEN.sub(lambda match: data.get(match.group(1), match.group(0)), text)


def evaluate(plan: dict[str, Any]) -> list[TemplateResult]:
    templates = plan.get("templates")
    if not isinstance(templates, list) or not templates:
        raise LabError("templates must be a non-empty array")
    if len(templates) > MAX_TEMPLATES:
        raise LabError(f"templates has more than {MAX_TEMPLATES} entries")

    results: list[TemplateResult] = []
    ids: set[str] = set()
    allowed = {"id", "channel", "subject", "body", "data"}
    for index, item in enumerate(templates):
        label = f"templates[{index}]"
        if not isinstance(item, dict):
            raise LabError(f"{label} must be an object")
        unknown = sorted(set(item) - allowed)
        if unknown:
            raise LabError(f"{label} has unknown fields: {', '.join(unknown)}")
        template_id = _text(item.get("id"), f"{label}.id")
        assert template_id is not None
        if template_id in ids:
            raise LabError(f"duplicate template id: {template_id}")
        ids.add(template_id)
        channel = _text(item.get("channel"), f"{label}.channel")
        assert channel is not None
        subject = _text(item.get("subject"), f"{label}.subject", optional=True)
        body = _text(item.get("body"), f"{label}.body")
        assert body is not None
        data = _scalar_data(item.get("data"), f"{label}.data")
        placeholders = _ordered_tokens(subject, body)
        missing = tuple(name for name in placeholders if name not in data)
        unused = tuple(sorted(set(data) - set(placeholders)))
        results.append(TemplateResult(
            template_id=template_id,
            channel=channel,
            status="ready" if not missing else "blocked",
            placeholders=placeholders,
            missing=missing,
            unused=unused,
            subject=_render(subject, data) if not missing else None,
            body=_render(body, data) if not missing else None,
        ))
    return results


def as_json(results: list[TemplateResult]) -> str:
    payload = {
        "summary": {
            "templates": len(results),
            "ready": sum(r.status == "ready" for r in results),
            "blocked": sum(r.status == "blocked" for r in results),
        },
        "templates": [
            {
                "id": r.template_id,
                "channel": r.channel,
                "status": r.status,
                "placeholders": list(r.placeholders),
                "missing": list(r.missing),
                "unused": list(r.unused),
                **({"preview": {"subject": r.subject, "body": r.body}} if r.status == "ready" else {}),
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def as_text(results: list[TemplateResult]) -> str:
    ready = sum(r.status == "ready" for r in results)
    lines = [f"Notification Template Lab: {ready}/{len(results)} ready"]
    for result in results:
        lines.append(f"\n[{result.status.upper()}] {result.template_id} ({result.channel})")
        lines.append("placeholders: " + (", ".join(result.placeholders) or "none"))
        if result.missing:
            lines.append("missing: " + ", ".join(result.missing))
        if result.unused:
            lines.append("unused: " + ", ".join(result.unused))
        if result.status == "ready":
            if result.subject is not None:
                lines.append("subject: " + result.subject)
            lines.append("body: " + (result.body or ""))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="JSON template plan")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        results = evaluate(load_plan(args.plan))
    except (LabError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(as_json(results) if args.format == "json" else as_text(results))
    return 1 if any(r.status == "blocked" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
