"""Offline, value-free triage of explicit credential assignments."""
import argparse
import json
from pathlib import Path
import re

LIMIT = 65536
ASSIGNMENT = re.compile(r'''^\s*(?:export\s+)?(?:api_key|access_token|client_secret|password)\s*[:=]\s*(\S.*?)\s*$''', re.I)
PRIVATE_KEY = re.compile(r'^\s*-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----\s*$')


def scan(text):
    if not isinstance(text, str):
        raise ValueError('expected UTF-8 text')
    if len(text.encode('utf-8')) > LIMIT or '\0' in text:
        raise ValueError('input must be text of at most 64 KiB without NUL bytes')
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        if PRIVATE_KEY.fullmatch(line):
            findings.append({'line': number, 'rule': 'private-key-marker'})
        elif ASSIGNMENT.fullmatch(line):
            findings.append({'line': number, 'rule': 'credential-assignment'})
    return {'findings': findings, 'count': len(findings), 'scope': 'limited-pattern-review; no credential verification'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        with args.file.open('rb') as stream:
            data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('input too large')
        result = scan(data.decode('utf-8'))
    except (OSError, ValueError):
        parser.exit(2, 'Cannot scan: unreadable, oversized or invalid UTF-8 text input.\n')
    print(json.dumps(result, indent=2))
    return 1 if result['count'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
