"""Offline inventory of selected response headers; never a security score."""
import argparse
import json
from pathlib import Path
import re

HEADERS = {
    'content-security-policy': 'Controls allowed resource sources; policy effectiveness requires manual review.',
    'strict-transport-security': 'Requests HTTPS use on future visits; deployment context and directives matter.',
    'x-content-type-options': 'nosniff prevents MIME type guessing in supported contexts.',
    'referrer-policy': 'Controls referrer information sent with requests.',
    'x-frame-options': 'Controls framing; review alongside CSP frame-ancestors.',
    'permissions-policy': 'Restricts selected browser features; support and context vary.',
}


def inspect(text):
    if not isinstance(text, str) or len(text.encode('utf-8')) > 65536:
        raise ValueError('input must be text no larger than 64 KiB')
    values = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith((' ', '\t')):
            raise ValueError(f'line {number}: folded headers are not supported')
        if ':' not in line:
            raise ValueError(f'line {number}: expected Name: value (no status line)')
        name, value = line.split(':', 1)
        if not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name):
            raise ValueError(f'line {number}: invalid header name')
        if any(ord(c) < 32 and c != '\t' or ord(c) == 127 for c in value):
            raise ValueError(f'line {number}: control character')
        key = name.lower()
        if key in HEADERS:
            values.setdefault(key, []).append(value.strip())
    result = []
    for name, purpose in HEADERS.items():
        found = values.get(name, [])
        status = 'missing' if not found else 'empty' if not any(found) else 'present'
        notes = []
        if len(found) > 1:
            notes.append('Repeated header: review combination semantics manually.')
        if name == 'x-content-type-options' and found and found != ['nosniff']:
            notes.append('Expected a single nosniff value; review the original response.')
        result.append({'header': name, 'status': status, 'occurrences': len(found),
                       'purpose': purpose, 'notes': notes})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path, help='UTF-8 Name: value lines from one response, without status line or body')
    args = p.parse_args()
    try:
        with args.file.open('rb') as f:
            raw = f.read(65537)
        if len(raw) > 65536:
            raise ValueError('input exceeds 64 KiB')
        report = inspect(raw.decode('utf-8'))
    except (OSError, UnicodeError, ValueError) as e:
        p.error(str(e))
    print(json.dumps({'scope': 'Offline inventory only; present does not mean secure. Values are omitted.',
                      'headers': report}, indent=2))


if __name__ == '__main__': main()
