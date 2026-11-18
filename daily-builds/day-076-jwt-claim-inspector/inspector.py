"""Offline JWT claim inspection; never an authentication decision."""
import argparse
import base64
import json
import math
import re
import sys
import time

LIMIT = 16384


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON')


def decode(segment):
    if not segment or not re.fullmatch(r'[A-Za-z0-9_-]+', segment):
        raise ValueError('invalid segment')
    raw = base64.b64decode(segment + '=' * (-len(segment) % 4), altchars=b'-_', validate=True)
    if base64.urlsafe_b64encode(raw).decode().rstrip('=') != segment:
        raise ValueError('noncanonical encoding')
    return raw


def inspect(token, now):
    if not isinstance(token, str) or len(token) > LIMIT:
        raise ValueError('invalid token')
    if type(now) not in (int, float) or not math.isfinite(now):
        raise ValueError('invalid clock')
    parts = token.strip().split('.')
    if len(parts) != 3:
        raise ValueError('expected compact JWS')
    header, claims = [json.loads(decode(p).decode('utf-8'), object_pairs_hook=unique,
                                 parse_constant=reject_constant) for p in parts[:2]]
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise ValueError('expected objects')
    if parts[2]:
        decode(parts[2])
    checks = {}
    for key in ('exp', 'nbf', 'iat'):
        if key not in claims:
            checks[key] = 'absent'
        elif type(claims[key]) not in (int, float) or not math.isfinite(claims[key]):
            checks[key] = 'invalid NumericDate'
        elif key == 'exp':
            checks[key] = 'expired' if now >= claims[key] else 'not expired'
        elif key == 'nbf':
            checks[key] = 'not yet active' if now < claims[key] else 'time reached'
        else:
            checks[key] = 'future issued-at' if now < claims[key] else 'not in future'
    return {'verification': 'NOT VERIFIED: decoded claims are untrusted',
            'header': header, 'claims': claims, 'checked_at': now, 'time_checks': checks,
            'scope': 'No signature, issuer, audience, algorithm or authorization validation; zero clock leeway.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', help='UTF-8 token file; use synthetic tokens')
    parser.add_argument('--now', type=float, help='Unix seconds for repeatable inspection')
    args = parser.parse_args()
    try:
        with open(args.file, 'rb') as source:
            raw = source.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('too large')
        report = inspect(raw.decode('utf-8'), time.time() if args.now is None else args.now)
        print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError, OverflowError):
        print('Cannot inspect input: use a compact three-part JWT with JSON objects (maximum 16 KiB).', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
