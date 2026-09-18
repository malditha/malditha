#!/usr/bin/env python3
"""Validate, explain and preview standard five-field cron expressions."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
WEEKDAY_NAMES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6,
}


class CronError(ValueError):
    """Raised when a cron expression cannot be parsed safely."""


@dataclass(frozen=True)
class FieldSpec:
    name: str
    minimum: int
    maximum: int
    names: dict[str, int] | None = None


FIELDS = (
    FieldSpec("minute", 0, 59),
    FieldSpec("hour", 0, 23),
    FieldSpec("day of month", 1, 31),
    FieldSpec("month", 1, 12, MONTH_NAMES),
    FieldSpec("day of week", 0, 7, WEEKDAY_NAMES),
)


@dataclass(frozen=True)
class CronSchedule:
    expression: str
    values: tuple[frozenset[int], ...]
    wildcards: tuple[bool, ...]

    def matches(self, moment: datetime) -> bool:
        cron_weekday = (moment.weekday() + 1) % 7
        minute, hour, day, month, weekday = self.values
        dom_matches = moment.day in day
        dow_matches = cron_weekday in weekday

        if self.wildcards[2] and self.wildcards[4]:
            day_matches = True
        elif self.wildcards[2]:
            day_matches = dow_matches
        elif self.wildcards[4]:
            day_matches = dom_matches
        else:
            day_matches = dom_matches or dow_matches

        return (
            moment.minute in minute
            and moment.hour in hour
            and moment.month in month
            and day_matches
        )


def _number(token: str, spec: FieldSpec) -> int:
    lowered = token.lower()
    if spec.names and lowered in spec.names:
        return spec.names[lowered]
    try:
        value = int(token)
    except ValueError as exc:
        raise CronError(f"{spec.name}: {token!r} is not a number or supported name") from exc
    if not spec.minimum <= value <= spec.maximum:
        raise CronError(
            f"{spec.name}: {value} is outside {spec.minimum}-{spec.maximum}"
        )
    return value


def _expand(part: str, spec: FieldSpec) -> set[int]:
    base, slash, step_text = part.partition("/")
    step = 1
    if slash:
        try:
            step = int(step_text)
        except ValueError as exc:
            raise CronError(f"{spec.name}: step {step_text!r} is not an integer") from exc
        if step < 1:
            raise CronError(f"{spec.name}: step must be greater than zero")

    if base == "*":
        start, end = spec.minimum, spec.maximum
    elif "-" in base:
        start_text, end_text = base.split("-", 1)
        start, end = _number(start_text, spec), _number(end_text, spec)
        if start > end:
            raise CronError(f"{spec.name}: range start must not exceed range end")
    else:
        if slash:
            raise CronError(f"{spec.name}: steps require * or a range")
        return {_number(base, spec)}

    return set(range(start, end + 1, step))


def parse(expression: str) -> CronSchedule:
    parts = expression.split()
    if len(parts) != 5:
        raise CronError("expected exactly five fields: minute hour day month weekday")

    parsed: list[frozenset[int]] = []
    wildcards: list[bool] = []
    for text, spec in zip(parts, FIELDS):
        if not text:
            raise CronError(f"{spec.name}: field cannot be empty")
        values: set[int] = set()
        for item in text.split(","):
            if not item:
                raise CronError(f"{spec.name}: list contains an empty item")
            values.update(_expand(item, spec))
        if spec.name == "day of week" and 7 in values:
            values.remove(7)
            values.add(0)
        parsed.append(frozenset(values))
        wildcards.append(text == "*")

    return CronSchedule(expression=" ".join(parts), values=tuple(parsed), wildcards=tuple(wildcards))


def _summarize(values: frozenset[int], spec: FieldSpec, wildcard: bool) -> str:
    if wildcard:
        return f"every {spec.name}"
    ordered = sorted(values)
    reverse_names = {value: name.title() for name, value in (spec.names or {}).items()}
    labels = [reverse_names.get(value, str(value)) for value in ordered]
    return ", ".join(labels)


def explain(schedule: CronSchedule) -> list[dict[str, str]]:
    return [
        {
            "field": spec.name,
            "source": source,
            "meaning": _summarize(values, spec, wildcard),
        }
        for source, spec, values, wildcard in zip(
            schedule.expression.split(), FIELDS, schedule.values, schedule.wildcards
        )
    ]


def next_matches(
    schedule: CronSchedule,
    start: datetime,
    count: int = 5,
    search_days: int = 366 * 5,
) -> list[datetime]:
    if not 1 <= count <= 20:
        raise CronError("count must be between 1 and 20")
    candidate = start.replace(second=0, microsecond=0) + timedelta(minutes=1)
    deadline = candidate + timedelta(days=search_days)
    matches: list[datetime] = []
    while candidate <= deadline and len(matches) < count:
        if schedule.matches(candidate):
            matches.append(candidate)
        candidate += timedelta(minutes=1)
    if len(matches) < count:
        raise CronError(f"could not find {count} matches within {search_days} days")
    return matches


def _parse_start(value: str | None) -> datetime:
    if value is None:
        return datetime.now().astimezone().replace(tzinfo=None)
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CronError("--from must be an ISO date/time such as 2026-09-18T09:00") from exc
    if moment.tzinfo is not None:
        moment = moment.astimezone().replace(tzinfo=None)
    return moment


def build_report(expression: str, start: datetime, count: int) -> dict[str, object]:
    schedule = parse(expression)
    return {
        "expression": schedule.expression,
        "interpretation": "standard five-field cron using local wall-clock time",
        "fields": explain(schedule),
        "next_matches": [item.isoformat(timespec="minutes") for item in next_matches(schedule, start, count)],
        "note": "When both day-of-month and day-of-week are restricted, either field may match.",
    }


def render_text(report: dict[str, object]) -> str:
    lines = [f"Cron: {report['expression']}", str(report["interpretation"]), "", "Fields:"]
    for item in report["fields"]:  # type: ignore[union-attr]
        lines.append(f"- {item['field']}: {item['source']} -> {item['meaning']}")
    lines.extend(["", "Next matches:"])
    lines.extend(f"- {value}" for value in report["next_matches"])  # type: ignore[arg-type]
    lines.extend(["", f"Note: {report['note']}"])
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expression", help='five-field cron expression, for example "*/15 9-17 * * 1-5"')
    parser.add_argument("--from", dest="start", help="ISO date/time used for a deterministic preview")
    parser.add_argument("--count", type=int, default=5, help="number of future matches (1-20)")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.expression, _parse_start(args.start), args.count)
    except CronError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
