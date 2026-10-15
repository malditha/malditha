"""Review recorded restore-drill evidence without performing a restore."""
import argparse
import json
from pathlib import Path
import sys

CHECKS = {
    "backup_identified": "Identify the backup and recovery point",
    "integrity_checked": "Check backup integrity",
    "isolated_target": "Use an isolated restore target",
    "restore_completed": "Complete the restore operation",
    "data_validated": "Validate restored data",
    "application_checked": "Check the restored application workflow",
}
MAX_BYTES = 1024 * 1024


def review(record):
    if not isinstance(record, dict) or not isinstance(record.get("checks"), dict):
        raise ValueError("record must contain a checks object")
    checks = record["checks"]
    unknown = set(checks) - set(CHECKS)
    if unknown:
        raise ValueError("checks contains unsupported keys")
    rows = []
    for key, label in CHECKS.items():
        item = checks.get(key)
        if item is None:
            state = "unverified"
        elif not isinstance(item, dict) or item.get("status") not in ("pass", "fail", "unverified"):
            raise ValueError(f"{key} requires status pass, fail, or unverified")
        else:
            state = item["status"]
            evidence = item.get("evidence_recorded", False)
            if not isinstance(evidence, bool):
                raise ValueError(f"{key}.evidence_recorded must be boolean")
            if state == "pass" and not evidence:
                state = "unverified"
        rows.append({"id": key, "label": label, "status": state})
    counts = {state: sum(row["status"] == state for row in rows) for state in ("pass", "fail", "unverified")}
    overall = "blocked" if counts["fail"] else "incomplete" if counts["unverified"] else "record_complete"
    return {"overall": overall, "summary": counts, "checks": rows,
            "next_checks": [row["id"] for row in rows if row["status"] != "pass"],
            "scope": "Reviews supplied declarations only; does not verify evidence or prove recoverability."}


def load_record(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("record exceeds 1 MiB")
    return json.loads(raw.decode("utf-8"))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("record", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        result = review(load_record(args.record))
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Backup Restore Checklist: {result['overall']}")
        for row in result["checks"]:
            print(f"[{row['status'].upper()}] {row['label']}")
        print(result["scope"])
    return 0 if result["overall"] == "record_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
