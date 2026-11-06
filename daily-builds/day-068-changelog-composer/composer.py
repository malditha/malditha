"""Compose a small, reviewed release changelog from structured changes."""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

CATEGORIES = ("Added", "Changed", "Fixed", "Removed", "Security")

def plain(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("text must be nonempty and within its length limit")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("control characters are not allowed")
    return value.strip()

def escape(text):
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', text)

def compose(data):
    if not isinstance(data, dict) or set(data) != {"version", "date", "changes"}:
        raise ValueError("expected version, date and changes")
    version = plain(data["version"], 60)
    date = plain(data["date"], 10)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("date must use YYYY-MM-DD")
    datetime.date.fromisoformat(date)
    changes = data["changes"]
    if not isinstance(changes, list) or not 1 <= len(changes) <= 200:
        raise ValueError("provide 1 to 200 changes")
    groups = {key: [] for key in CATEGORIES}
    seen = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"id", "category", "summary", "breaking"}:
            raise ValueError("each change needs id, category, summary and breaking")
        ident = plain(change["id"], 60)
        category = change["category"]
        if not isinstance(category, str) or category not in CATEGORIES:
            raise ValueError("unsupported category")
        summary = plain(change["summary"], 300)
        if type(change["breaking"]) is not bool:
            raise ValueError("breaking must be boolean")
        if ident in seen:
            raise ValueError("duplicate change id")
        seen.add(ident)
        groups[category].append({"id": ident, "summary": summary, "breaking": change["breaking"]})
    lines = [f"## {escape(version)} — {date}", ""]
    for category in CATEGORIES:
        if groups[category]:
            lines.extend([f"### {category}", ""])
            for item in groups[category]:
                prefix = "**BREAKING:** " if item["breaking"] else ""
                lines.append(f"- {prefix}{escape(item['summary'])}")
            lines.append("")
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
            raise ValueError("input exceeds 128 KB")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
        print(compose(data))
    except (OSError, UnicodeError, ValueError, RecursionError):
        print("Invalid input: check the documented schema, limits and JSON format.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
