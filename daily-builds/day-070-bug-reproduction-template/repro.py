"""Validate structured bug evidence and render a portable Markdown report."""
import argparse
import json
import re
import sys
from pathlib import Path

def text(value, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("text must be nonempty and within limits")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("control characters are not allowed")
    return value.strip()

def escape(value):
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', value)

def render(data):
    required = {"title", "environment", "preconditions", "steps", "expected", "actual", "frequency"}
    if not isinstance(data, dict) or set(data) != required:
        raise ValueError("report fields do not match schema")
    title = text(data["title"], 120)
    environment = data["environment"]
    if not isinstance(environment, dict) or not 1 <= len(environment) <= 10:
        raise ValueError("provide 1 to 10 environment fields")
    env = []
    for key, value in environment.items():
        env.append((text(key, 60), text(value, 300)))
    sections = {}
    for field in ("preconditions", "steps"):
        rows = data[field]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
            raise ValueError("provide 1 to 20 preconditions and steps")
        sections[field] = [text(row, 500) for row in rows]
    expected, actual = text(data["expected"]), text(data["actual"])
    frequency = data["frequency"]
    if not isinstance(frequency, dict) or set(frequency) != {"observed", "attempted"}:
        raise ValueError("frequency needs observed and attempted")
    observed, attempted = frequency["observed"], frequency["attempted"]
    if type(observed) is not int or type(attempted) is not int or not 1 <= observed <= attempted <= 10000:
        raise ValueError("frequency must satisfy 1 <= observed <= attempted <= 10000")
    lines = ["# " + escape(title), "", "## Environment", ""]
    lines.extend(f"- **{escape(k)}:** {escape(v)}" for k, v in sorted(env))
    lines.extend(["", "## Preconditions", ""])
    lines.extend("- " + escape(row) for row in sections["preconditions"])
    lines.extend(["", "## Steps to reproduce", ""])
    lines.extend(f"{i}. {escape(row)}" for i, row in enumerate(sections["steps"], 1))
    lines.extend(["", "## Expected result", "", escape(expected), "", "## Actual result", "", escape(actual),
                  "", "## Observed frequency", "", f"{observed} of {attempted} attempts.",
                  "", "Review for sensitive information before sharing. This report records observations; it does not verify a root cause.", ""])
    return "\n".join(lines)

def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.input.open("rb") as source:
            raw = source.read(128001)
        if len(raw) > 128000:
            raise ValueError("input too large")
        print(render(json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)))
    except (OSError, UnicodeError, ValueError, RecursionError):
        print("Invalid input: check the documented schema, limits and JSON format.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
