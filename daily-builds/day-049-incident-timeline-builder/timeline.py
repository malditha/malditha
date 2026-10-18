"""Build a chronological, read-only report from sanitized incident events."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import unicodedata

MAX_BYTES = 1_000_000
MAX_EVENTS = 1000
KINDS = {"detected", "investigating", "mitigated", "resolved", "note"}
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", re.ASCII)


def seconds(delta):
    """Exact decimal seconds, without floating-point rounding."""
    micros = (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds
    whole, fraction = divmod(micros, 1_000_000)
    return str(whole) if not fraction else f"{whole}.{fraction:06d}".rstrip("0")


def parse_timestamp(value):
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        raise ValueError("timestamp must include seconds and an explicit offset")
    if value[-1] != "Z":
        hours, minutes = int(value[-5:-3]), int(value[-2:])
        if minutes > 59 or hours > 14 or (hours == 14 and minutes):
            raise ValueError("invalid timezone offset")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not 2000 <= stamp.year <= 2100:
        raise ValueError("timestamp year outside 2000–2100")
    return stamp.astimezone(timezone.utc)


def build_timeline(data):
    """Validate, stably sort by UTC instant, and return an allowlisted report."""
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        raise ValueError("expected an events array")
    if not 1 <= len(data["events"]) <= MAX_EVENTS:
        raise ValueError("expected 1–1000 events")
    seen, rows = set(), []
    for item in data["events"]:
        if not isinstance(item, dict):
            raise ValueError("event must be an object")
        ident, kind, label = item.get("id"), item.get("kind"), item.get("label")
        if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", ident):
            raise ValueError("invalid event id")
        if ident in seen:
            raise ValueError("duplicate event id")
        if not isinstance(kind, str) or kind not in KINDS:
            raise ValueError("invalid event kind")
        if not isinstance(label, str) or not 1 <= len(label) <= 160 or not label.strip():
            raise ValueError("invalid event label")
        if any(unicodedata.category(char).startswith("C") for char in label):
            raise ValueError("control characters are not allowed")
        seen.add(ident)
        rows.append((parse_timestamp(item.get("at")), ident, kind, label))
    rows.sort(key=lambda row: row[0])
    start, end, previous = rows[0][0], rows[-1][0], rows[0][0]
    events = []
    for stamp, ident, kind, label in rows:
        events.append({"id": ident, "at": stamp.isoformat().replace("+00:00", "Z"),
                       "kind": kind, "label": label,
                       "elapsed_seconds": seconds(stamp-start), "gap_seconds": seconds(stamp-previous)})
        previous = stamp
    return {"count": len(events), "start": events[0]["at"], "end": events[-1]["at"],
            "duration_seconds": seconds(end-start), "events": events}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="sanitized local JSON file")
    parser.add_argument("--json", action="store_true", help="emit structured report")
    args = parser.parse_args(argv)
    try:
        with Path(args.input).open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("input too large")
        report = build_timeline(json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object))
    except (OSError, ValueError, RecursionError):
        print("Error: invalid or unreadable timeline input", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(f"Incident timeline: {report['count']} events; span: {report['duration_seconds']} seconds")
        for item in report["events"]:
            print(f"{item['at']} | +{item['elapsed_seconds']}s | gap {item['gap_seconds']}s | {item['id']} [{item['kind']}] {item['label']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
