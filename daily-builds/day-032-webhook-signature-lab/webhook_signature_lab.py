#!/usr/bin/env python3
"""Create and verify timestamped HMAC-SHA256 webhook signatures locally."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import time
from pathlib import Path

MAX_PAYLOAD_BYTES = 1_048_576
MAX_HEADER_LENGTH = 2_048
HEADER_PATTERN = re.compile(r"^[\x20-\x7e]+$")
HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


class SignatureError(ValueError):
    """Raised when inputs cannot produce a safe signature result."""


def read_payload(path: Path) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SignatureError(f"could not inspect payload: {exc}") from exc
    if size > MAX_PAYLOAD_BYTES:
        raise SignatureError(f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SignatureError(f"could not read payload: {exc}") from exc


def read_secret(variable: str, environ: dict[str, str] | None = None) -> bytes:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", variable):
        raise SignatureError("secret environment variable name is invalid")
    source = os.environ if environ is None else environ
    value = source.get(variable)
    if value is None:
        raise SignatureError(f"secret environment variable {variable} is not set")
    encoded = value.encode("utf-8")
    if not 16 <= len(encoded) <= 4096:
        raise SignatureError("secret must contain between 16 and 4096 UTF-8 bytes")
    return encoded


def validate_timestamp(value: int | str) -> int:
    try:
        timestamp = int(value)
    except (TypeError, ValueError) as exc:
        raise SignatureError("timestamp must be an integer") from exc
    if timestamp < 0 or timestamp > 9_999_999_999:
        raise SignatureError("timestamp is outside the supported range")
    return timestamp


def compute_signature(payload: bytes, secret: bytes, timestamp: int | str) -> str:
    moment = validate_timestamp(timestamp)
    signed = str(moment).encode("ascii") + b"." + payload
    return hmac.new(secret, signed, hashlib.sha256).hexdigest()


def parse_signature_header(header: str) -> tuple[int, list[str]]:
    if not isinstance(header, str) or not header or len(header) > MAX_HEADER_LENGTH:
        raise SignatureError("signature header is empty or too long")
    if not HEADER_PATTERN.fullmatch(header):
        raise SignatureError("signature header contains unsupported characters")
    timestamp: int | None = None
    signatures: list[str] = []
    for item in header.split(","):
        if "=" not in item:
            raise SignatureError("signature header item must use key=value")
        key, value = (part.strip() for part in item.split("=", 1))
        if key == "t":
            if timestamp is not None:
                raise SignatureError("signature header contains duplicate timestamps")
            timestamp = validate_timestamp(value)
        elif key == "v1":
            if not HEX_PATTERN.fullmatch(value):
                raise SignatureError("v1 signature must be 64 hexadecimal characters")
            signatures.append(value.lower())
    if timestamp is None:
        raise SignatureError("signature header is missing t")
    if not signatures:
        raise SignatureError("signature header is missing v1")
    if len(signatures) > 5:
        raise SignatureError("signature header contains too many v1 values")
    return timestamp, signatures


def sign_payload(payload: bytes, secret: bytes, timestamp: int | str) -> dict[str, object]:
    moment = validate_timestamp(timestamp)
    signature = compute_signature(payload, secret, moment)
    return {
        "algorithm": "HMAC-SHA256",
        "timestamp": moment,
        "header": f"t={moment},v1={signature}",
        "payload_bytes": len(payload),
        "secret_exposed": False,
        "network_request_sent": False,
    }


def verify_payload(
    payload: bytes,
    secret: bytes,
    header: str,
    *,
    now: int | None = None,
    tolerance: int = 300,
) -> dict[str, object]:
    if not isinstance(tolerance, int) or not 0 <= tolerance <= 86_400:
        raise SignatureError("tolerance must be between 0 and 86400 seconds")
    timestamp, candidates = parse_signature_header(header)
    reference = int(time.time()) if now is None else validate_timestamp(now)
    age = reference - timestamp
    expected = compute_signature(payload, secret, timestamp)
    signature_matches = any(
        hmac.compare_digest(expected, candidate) for candidate in candidates
    )
    timestamp_valid = abs(age) <= tolerance
    return {
        "algorithm": "HMAC-SHA256",
        "valid": signature_matches and timestamp_valid,
        "signature_matches": signature_matches,
        "timestamp_valid": timestamp_valid,
        "timestamp": timestamp,
        "age_seconds": age,
        "tolerance_seconds": tolerance,
        "payload_bytes": len(payload),
        "secret_exposed": False,
        "network_request_sent": False,
    }


def render_text(report: dict[str, object], action: str) -> str:
    lines = [
        f"WEBHOOK SIGNATURE {action.upper()}",
        "=" * (18 + len(action)),
        f"Algorithm: {report['algorithm']}",
        f"Payload bytes: {report['payload_bytes']}",
        "Secret exposed: no",
        "Network request sent: no",
    ]
    if action == "sign":
        lines.extend([f"Timestamp: {report['timestamp']}", f"Header: {report['header']}"])
    else:
        lines.extend([
            f"Valid: {'yes' if report['valid'] else 'no'}",
            f"Signature matches: {'yes' if report['signature_matches'] else 'no'}",
            f"Timestamp valid: {'yes' if report['timestamp_valid'] else 'no'}",
            f"Age seconds: {report['age_seconds']}",
        ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--secret-env", default="WEBHOOK_SECRET")
    subparsers = parser.add_subparsers(dest="action", required=True)
    sign = subparsers.add_parser("sign")
    sign.add_argument("payload", type=Path)
    sign.add_argument("--timestamp", type=int, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("payload", type=Path)
    verify.add_argument("--header", required=True)
    verify.add_argument("--now", type=int)
    verify.add_argument("--tolerance", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        payload = read_payload(args.payload)
        secret = read_secret(args.secret_env)
        if args.action == "sign":
            report = sign_payload(payload, secret, args.timestamp)
            exit_code = 0
        else:
            report = verify_payload(
                payload, secret, args.header, now=args.now, tolerance=args.tolerance
            )
            exit_code = 0 if report["valid"] else 1
    except SignatureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text(report, args.action))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
