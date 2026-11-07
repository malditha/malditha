"""Generate bounded exhaustive boolean feature-flag test scenarios."""
import argparse
import itertools
import json
import re
import sys
from pathlib import Path

def names(value, label):
    if not isinstance(value, list) or not 1 <= len(value) <= 8:
        raise ValueError(label + " must contain 1 to 8 names")
    if any(not isinstance(x, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", x) for x in value):
        raise ValueError("names must use lowercase identifiers")
    if len(set(value)) != len(value):
        raise ValueError("names must be unique")
    return sorted(value)

def generate(data):
    if not isinstance(data, dict) or set(data) != {"flags", "environments", "requires"}:
        raise ValueError("expected flags, environments and requires")
    flags = names(data["flags"], "flags")
    environments = names(data["environments"], "environments")
    rules = data["requires"]
    if not isinstance(rules, list) or len(rules) > 56:
        raise ValueError("requires must be a bounded array")
    seen = set()
    for rule in rules:
        if not isinstance(rule, list) or len(rule) != 2 or any(not isinstance(x, str) or x not in flags for x in rule):
            raise ValueError("each dependency must name two declared flags")
        if rule[0] == rule[1] or tuple(rule) in seen:
            raise ValueError("self and duplicate dependencies are not allowed")
        seen.add(tuple(rule))
    scenarios = []
    rejected = 0
    for values in itertools.product((False, True), repeat=len(flags)):
        state = dict(zip(flags, values))
        if any(state[a] and not state[b] for a, b in seen):
            rejected += 1
            continue
        for environment in environments:
            scenarios.append({"id": f"case-{len(scenarios)+1:04d}", "environment": environment, "flags": state.copy()})
    return {"summary": {"valid_combinations": len(scenarios)//len(environments), "excluded_combinations": rejected, "scenarios": len(scenarios)}, "scenarios": scenarios}

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
        report = generate(json.loads(raw.decode("utf-8"), object_pairs_hook=pairs))
        print(json.dumps(report, indent=2))
    except (ValueError, OSError, UnicodeError, RecursionError):
        print("Invalid input: check the schema, names, dependencies and limits.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
