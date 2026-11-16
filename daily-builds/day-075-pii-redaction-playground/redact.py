"""Redact explicitly selected JSON keys; not automatic PII detection."""
import argparse
import json
from pathlib import Path

LIMIT = 65536
MARKER = '[REDACTED]'


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def redact(value, keys, depth=0):
    if depth > 40:
        raise ValueError('nesting exceeds limit')
    if isinstance(value, dict):
        return {k: MARKER if k.casefold() in keys else redact(v, keys, depth+1) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, keys, depth+1) for v in value]
    return value


def transform(data, names):
    if len(data) > LIMIT:
        raise ValueError('input too large')
    if not names or any(not isinstance(k, str) or not k or len(k)>100 for k in names):
        raise ValueError('select nonempty key names of at most 100 characters')
    value = json.loads(data.decode('utf-8'), object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite number')))
    return redact(value, {k.casefold() for k in names})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    p.add_argument('--key', action='append', required=True, help='exact key name; repeat for more keys')
    a = p.parse_args()
    try:
        with a.file.open('rb') as f:
            data = f.read(LIMIT+1)
        output = transform(data, a.key)
        print(json.dumps(output, ensure_ascii=True, allow_nan=False, indent=2))
    except (OSError, ValueError, RecursionError):
        p.exit(2, 'Cannot redact: invalid, unreadable, oversized or excessively nested JSON input.\n')


if __name__ == '__main__': main()
