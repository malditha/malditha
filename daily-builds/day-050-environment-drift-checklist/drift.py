"""Compare six declared environment observations without reporting their values."""
import argparse
import json
from pathlib import Path
import sys
import unicodedata

CHECKS = ("runtime_version", "os_release", "dependency_lock", "schema_revision", "timezone", "feature_set")
MAX_BYTES = 1_000_000


def validate(snapshot):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("checks"), dict):
        raise ValueError("expected a checks object")
    checks = snapshot["checks"]
    for key in CHECKS:
        if key not in checks:
            continue
        value = checks[key]
        if not isinstance(value, str) or not 1 <= len(value) <= 256 or not value.strip():
            raise ValueError("invalid observation")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("control characters are not allowed")
    return checks


def compare(baseline, candidate):
    """Return a fixed-order checklist; equality is exact and values stay private."""
    left, right = validate(baseline), validate(candidate)
    rows, counts = [], {"match": 0, "drift": 0, "unverified": 0}
    for key in CHECKS:
        if key not in left or key not in right:
            status = "unverified"
            reason = "missing_both" if key not in left and key not in right else (
                "missing_baseline" if key not in left else "missing_candidate")
        else:
            status = "match" if left[key] == right[key] else "drift"
            reason = "equal_observations" if status == "match" else "different_observations"
        counts[status] += 1
        rows.append({"check": key, "status": status, "reason": reason})
    status = "drift" if counts["drift"] else ("unverified" if counts["unverified"] else "aligned")
    return {"status": status, "counts": counts, "checks": rows}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_snapshot(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input too large")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="sanitized reference JSON snapshot")
    parser.add_argument("candidate", help="sanitized comparison JSON snapshot")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)
    try:
        report = compare(read_snapshot(args.baseline), read_snapshot(args.candidate))
    except (OSError, ValueError, RecursionError):
        print("Error: invalid or unreadable snapshot input", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Environment drift checklist: {report['status']}")
        for row in report["checks"]:
            print(f"{row['check']}: {row['status']} ({row['reason']})")
        print("Counts: " + ", ".join(f"{k}={v}" for k, v in report["counts"].items()))
    return 0 if report["status"] == "aligned" else 1


if __name__ == "__main__":
    sys.exit(main())
