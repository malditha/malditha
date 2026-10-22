#!/usr/bin/env python3
"""Build a deterministic content brief from one bounded local JSON request."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 100_000
MAX_LIST_ITEMS = 12
MAX_TEXT = 500
ALLOWED_CHANNELS = {"article", "email", "facebook", "linkedin", "reel", "website"}
ALLOWED_GOALS = {"educate", "explain", "inform", "promote", "support"}
INPUT_KEYS = {
    "title", "goal", "audience", "channel", "problem", "takeaway",
    "evidence", "must_include", "avoid", "call_to_action", "tone",
}


class InputError(ValueError):
    """Raised when a request cannot be safely converted into a brief."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise InputError("file exceeds size limit")
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except InputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("unable to read JSON input") from exc


def _clean_text(value: Any, field: str, *, required: bool = True) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise InputError(f"{field} must be text")
    cleaned = re.sub(r"\s+", " ", value).strip()
    if required and not cleaned:
        raise InputError(f"{field} is required")
    if len(cleaned) > MAX_TEXT:
        raise InputError(f"{field} exceeds length limit")
    return cleaned


def _clean_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_LIST_ITEMS:
        raise InputError(f"{field} must be a bounded list")
    cleaned = [_clean_text(item, field) for item in value]
    if len(set(item.casefold() for item in cleaned)) != len(cleaned):
        raise InputError(f"{field} contains duplicate items")
    return cleaned


def build_brief(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict) or set(request) - INPUT_KEYS:
        raise InputError("request contains unsupported fields")

    title = _clean_text(request.get("title"), "title")
    goal = _clean_text(request.get("goal"), "goal").casefold()
    channel = _clean_text(request.get("channel"), "channel").casefold()
    if goal not in ALLOWED_GOALS:
        raise InputError("unsupported goal")
    if channel not in ALLOWED_CHANNELS:
        raise InputError("unsupported channel")

    audience = _clean_text(request.get("audience"), "audience")
    problem = _clean_text(request.get("problem"), "problem")
    takeaway = _clean_text(request.get("takeaway"), "takeaway")
    evidence = _clean_list(request.get("evidence"), "evidence")
    must_include = _clean_list(request.get("must_include"), "must_include")
    avoid = _clean_list(request.get("avoid"), "avoid")
    call_to_action = _clean_text(request.get("call_to_action"), "call_to_action", required=False)
    tone = _clean_text(request.get("tone", "clear and practical"), "tone")

    sections = [
        {"heading": "Opening", "purpose": f"Name the problem for {audience}."},
        {"heading": "Core explanation", "purpose": f"Deliver the main takeaway: {takeaway}"},
    ]
    if evidence:
        sections.append({"heading": "Evidence", "purpose": "Support the explanation with the approved evidence list."})
    sections.append({"heading": "Next step", "purpose": call_to_action or "Close with a useful, non-pushy next step."})

    return {
        "title": title,
        "objective": {"goal": goal, "channel": channel, "audience": audience, "tone": tone},
        "problem": problem,
        "single_takeaway": takeaway,
        "sections": sections,
        "evidence": evidence,
        "requirements": {"must_include": must_include, "avoid": avoid},
        "call_to_action": call_to_action or None,
        "editorial_checks": [
            "Keep claims within the supplied evidence.",
            "Remove private, client-derived, or identifying details.",
            "Review the final draft before publishing.",
        ],
    }


def format_markdown(brief: dict[str, Any]) -> str:
    objective = brief["objective"]
    lines = [
        f"# {brief['title']}", "", "## Objective", "",
        f"- Goal: {objective['goal']}", f"- Channel: {objective['channel']}",
        f"- Audience: {objective['audience']}", f"- Tone: {objective['tone']}",
        "", "## Problem", "", brief["problem"], "", "## Single takeaway", "",
        brief["single_takeaway"], "", "## Structure", "",
    ]
    lines.extend(f"{index}. **{item['heading']}** — {item['purpose']}" for index, item in enumerate(brief["sections"], 1))
    for heading, items in (
        ("Evidence", brief["evidence"]),
        ("Must include", brief["requirements"]["must_include"]),
        ("Avoid", brief["requirements"]["avoid"]),
        ("Editorial checks", brief["editorial_checks"]),
    ):
        lines.extend(["", f"## {heading}", ""])
        lines.extend(f"- {item}" for item in items) if items else lines.append("- None supplied")
    if brief["call_to_action"]:
        lines.extend(["", "## Call to action", "", brief["call_to_action"]])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        brief = build_brief(load_json(args.request))
    except InputError:
        print("Input error: unable to build a brief from the supplied request.", file=sys.stderr)
        return 2
    print(json.dumps(brief, indent=2, ensure_ascii=False) if args.as_json else format_markdown(brief), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
