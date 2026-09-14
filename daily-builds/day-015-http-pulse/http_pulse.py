#!/usr/bin/env python3
"""Check a small list of HTTP endpoints and summarize their health."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CheckResult:
    url: str
    ok: bool
    status: int | None
    elapsed_ms: int
    error: str | None = None


def parse_urls(text: str) -> tuple[str, ...]:
    urls: list[str] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parsed = urlsplit(line)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"line {number}: expected an absolute http:// or https:// URL")
        urls.append(line)
    if not urls:
        raise ValueError("no URLs found")
    return tuple(urls)


def check_url(
    url: str,
    timeout: float,
    opener: Callable[..., object] = urllib.request.urlopen,
    clock: Callable[[], float] = time.perf_counter,
) -> CheckResult:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "HTTP-Pulse/1.0"})
    started = clock()
    try:
        response = opener(request, timeout=timeout)
        status = int(getattr(response, "status", response.getcode()))
        close = getattr(response, "close", None)
        if close:
            close()
        elapsed = round((clock() - started) * 1000)
        return CheckResult(url, 200 <= status < 400, status, elapsed)
    except urllib.error.HTTPError as error:
        elapsed = round((clock() - started) * 1000)
        return CheckResult(url, False, error.code, elapsed, f"HTTP {error.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        elapsed = round((clock() - started) * 1000)
        reason = getattr(error, "reason", error)
        return CheckResult(url, False, None, elapsed, str(reason))


def check_all(
    urls: tuple[str, ...],
    timeout: float,
    checker: Callable[[str, float], CheckResult] = check_url,
) -> tuple[CheckResult, ...]:
    return tuple(checker(url, timeout) for url in urls)


def render_text(results: tuple[CheckResult, ...]) -> str:
    healthy = sum(result.ok for result in results)
    lines = [f"HTTP Pulse: {healthy}/{len(results)} healthy"]
    for result in results:
        marker = "OK" if result.ok else "FAIL"
        status = result.status if result.status is not None else "—"
        detail = f" · {result.error}" if result.error else ""
        lines.append(f"[{marker}] {status} · {result.elapsed_ms} ms · {result.url}{detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Text file containing one URL per line")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    try:
        urls = parse_urls(args.file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"HTTP Pulse: {error}", file=sys.stderr)
        return 2

    results = check_all(urls, args.timeout)
    if args.json:
        print(json.dumps({"healthy": sum(r.ok for r in results), "total": len(results), "results": [asdict(r) for r in results]}, indent=2))
    else:
        print(render_text(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
