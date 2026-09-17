#!/usr/bin/env python3
"""Probe an explicit list of TCP ports and produce a small diagnostic report."""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from dataclasses import asdict, dataclass
from typing import Callable

DEFAULT_TIMEOUT = 1.0


@dataclass(frozen=True)
class ProbeResult:
    port: int
    state: str
    latency_ms: float | None
    service: str | None
    error: str | None = None


def parse_ports(value: str) -> tuple[int, ...]:
    ports: set[int] = set()
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            raise ValueError("port list contains an empty entry")
        if "-" in part:
            pieces = part.split("-")
            if len(pieces) != 2 or not all(piece.isdigit() for piece in pieces):
                raise ValueError(f"invalid port range: {part}")
            start, end = map(int, pieces)
            if start > end:
                raise ValueError(f"port range must be ascending: {part}")
            if end - start > 99:
                raise ValueError("a single range may contain at most 100 ports")
            ports.update(range(start, end + 1))
        elif part.isdigit():
            ports.add(int(part))
        else:
            raise ValueError(f"invalid port: {part}")
    if not ports or any(port < 1 or port > 65535 for port in ports):
        raise ValueError("ports must be between 1 and 65535")
    if len(ports) > 100:
        raise ValueError("at most 100 unique ports may be probed")
    return tuple(sorted(ports))


def service_name(port: int) -> str | None:
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return None


def probe_port(host: str, port: int, timeout: float,
               connector: Callable[[tuple[str, int], float], object] = socket.create_connection,
               clock: Callable[[], float] = time.perf_counter) -> ProbeResult:
    started = clock()
    try:
        connection = connector((host, port), timeout)
        close = getattr(connection, "close", None)
        if close:
            close()
        return ProbeResult(port, "open", round((clock() - started) * 1000, 2), service_name(port))
    except ConnectionRefusedError:
        return ProbeResult(port, "closed", None, service_name(port))
    except (socket.timeout, TimeoutError):
        return ProbeResult(port, "timeout", None, service_name(port))
    except OSError as error:
        return ProbeResult(port, "error", None, service_name(port), str(error))


def run_report(host: str, ports: tuple[int, ...], timeout: float, connector=socket.create_connection) -> tuple[ProbeResult, ...]:
    return tuple(probe_port(host, port, timeout, connector=connector) for port in ports)


def as_text(host: str, timeout: float, results: tuple[ProbeResult, ...]) -> str:
    counts = {state: sum(result.state == state for result in results) for state in ("open", "closed", "timeout", "error")}
    lines = ["Port Probe Report", f"Host: {host}", f"Timeout: {timeout:g}s",
             f"Summary: {counts['open']} open · {counts['closed']} closed · {counts['timeout']} timeout · {counts['error']} error", ""]
    for result in results:
        service = f" ({result.service})" if result.service else ""
        latency = f" · {result.latency_ms:.2f} ms" if result.latency_ms is not None else ""
        error = f" · {result.error}" if result.error else ""
        lines.append(f"{result.port:>5}/tcp  {result.state.upper():<7}{service}{latency}{error}")
    lines.extend(["", "TCP connection check only; this does not identify vulnerabilities or authorize broader scanning."])
    return "\n".join(lines)


def as_json(host: str, timeout: float, results: tuple[ProbeResult, ...]) -> str:
    return json.dumps({"host": host, "timeout_seconds": timeout, "results": [asdict(result) for result in results]}, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Hostname or IP address you are authorized to check")
    parser.add_argument("ports", help="Comma-separated ports or ranges, for example 22,80,443 or 8000-8005")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Timeout per port in seconds (default: 1)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.host.strip():
        print("error: host cannot be empty", file=sys.stderr)
        return 2
    if not 0.05 <= args.timeout <= 30:
        print("error: timeout must be between 0.05 and 30 seconds", file=sys.stderr)
        return 2
    try:
        ports = parse_ports(args.ports)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    results = run_report(args.host, ports, args.timeout)
    print(as_json(args.host, args.timeout, results) if args.json else as_text(args.host, args.timeout, results))
    return 1 if any(result.state in {"timeout", "error"} for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
