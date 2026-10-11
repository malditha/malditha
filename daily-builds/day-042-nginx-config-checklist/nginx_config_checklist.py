#!/usr/bin/env python3
"""Create a focused checklist from a local Nginx configuration file."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 2_000_000
MAX_SERVERS = 100
SEVERITY_ORDER = {"high": 0, "warning": 1, "info": 2}


class ConfigError(ValueError):
    """Raised when the input cannot be parsed safely."""


def tokenize(source: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        if quote:
            if escaped:
                current.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                tokens.append("".join(current))
                current = []
                quote = None
            else:
                current.append(char)
            index += 1
            continue
        if char in {'"', "'"}:
            if current:
                tokens.append("".join(current))
                current = []
            quote = char
        elif char == "#":
            if current:
                tokens.append("".join(current))
                current = []
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        elif char in "{};":
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append(char)
        elif char.isspace():
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)
        index += 1
    if quote:
        raise ConfigError("unterminated quoted value")
    if current:
        tokens.append("".join(current))
    return tokens


def parse_config(source: str) -> list[dict[str, Any]]:
    tokens = tokenize(source)
    position = 0

    def parse_scope(in_block: bool = False) -> list[dict[str, Any]]:
        nonlocal position
        nodes: list[dict[str, Any]] = []
        while position < len(tokens):
            if tokens[position] == "}":
                if not in_block:
                    raise ConfigError("unexpected closing brace")
                position += 1
                return nodes
            parts: list[str] = []
            while position < len(tokens) and tokens[position] not in {";", "{", "}"}:
                parts.append(tokens[position])
                position += 1
            if not parts:
                raise ConfigError("expected directive name")
            if position >= len(tokens) or tokens[position] == "}":
                raise ConfigError("expected ';' or '{' after directive")
            marker = tokens[position]
            position += 1
            node: dict[str, Any] = {"name": parts[0], "args": parts[1:], "children": []}
            if marker == "{":
                node["children"] = parse_scope(True)
            nodes.append(node)
        if in_block:
            raise ConfigError("unclosed block")
        return nodes

    return parse_scope()


def _walk(nodes: list[dict[str, Any]]):
    for node in nodes:
        yield node
        yield from _walk(node["children"])


def _directives(nodes: list[dict[str, Any]], name: str, recursive: bool = False) -> list[dict[str, Any]]:
    source = _walk(nodes) if recursive else iter(nodes)
    return [node for node in source if node["name"] == name]


def audit_config(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    server_nodes = [node for node in _walk(nodes) if node["name"] == "server"]
    if len(server_nodes) > MAX_SERVERS:
        raise ConfigError(f"input exceeds the {MAX_SERVERS}-server limit")
    findings: list[dict[str, str]] = []
    servers: list[dict[str, Any]] = []
    route_owners: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = {}

    for number, server in enumerate(server_nodes, 1):
        label = f"server[{number}]"
        listens = [" ".join(node["args"]) for node in _directives(server["children"], "listen")]
        names = [arg for node in _directives(server["children"], "server_name") for arg in node["args"]]
        all_nodes = list(_walk(server["children"]))
        proxy = any(node["name"] == "proxy_pass" for node in all_nodes)
        root = any(node["name"] == "root" for node in all_nodes)
        mode = "proxy" if proxy else "static" if root else "other"
        servers.append({"id": label, "listeners": listens, "server_names": names, "mode": mode})
        if not listens:
            findings.append({"server": label, "severity": "warning", "rule": "missing-listen", "evidence": "no listen directive"})
        if not names:
            findings.append({"server": label, "severity": "warning", "rule": "missing-server-name", "evidence": "no server_name directive"})
        tls = any("ssl" in value.split() or any(part.startswith("443") or part.endswith(":443") for part in value.split()) for value in listens)
        certificate = bool(_directives(server["children"], "ssl_certificate"))
        certificate_key = bool(_directives(server["children"], "ssl_certificate_key"))
        if tls and certificate != certificate_key:
            findings.append({"server": label, "severity": "high", "rule": "tls-pair-incomplete", "evidence": "certificate and key directives are incomplete"})
        if any(node["name"] == "autoindex" and node["args"][:1] == ["on"] for node in all_nodes):
            findings.append({"server": label, "severity": "warning", "rule": "autoindex-enabled", "evidence": "autoindex on"})
        if listens and names:
            route_owners.setdefault((tuple(sorted(listens)), tuple(sorted(names))), []).append(label)

    for owners in route_owners.values():
        if len(owners) > 1:
            for label in owners:
                findings.append({"server": label, "severity": "warning", "rule": "duplicate-route", "evidence": "listener and server-name set repeats"})

    if any(node["name"] == "include" for node in _walk(nodes)):
        findings.append({"server": "config", "severity": "info", "rule": "unresolved-include", "evidence": "include directive remains"})

    findings.sort(key=lambda item: (item["server"], SEVERITY_ORDER[item["severity"]], item["rule"]))
    counts = Counter(item["severity"] for item in findings)
    return {
        "summary": {"servers": len(servers), "high": counts["high"], "warning": counts["warning"], "info": counts["info"]},
        "servers": servers,
        "findings": findings,
    }


def load_config(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ConfigError("input exceeds the 2 MB size limit")
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ConfigError("input must be UTF-8 text") from exc
    except OSError as exc:
        raise ConfigError(f"could not read input: {exc}") from exc


def format_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Nginx configuration checklist",
        f"{summary['servers']} server block(s) · {summary['high']} high · {summary['warning']} warning · {summary['info']} info",
        "",
    ]
    for server in report["servers"]:
        listeners = ", ".join(server["listeners"]) or "(none)"
        names = ", ".join(server["server_names"]) or "(none)"
        lines.append(f"{server['id']} · {server['mode']} · listen {listeners} · names {names}")
    if report["findings"]:
        lines.append("")
        lines.extend(f"{item['server']} · {item['severity'].upper()} · {item['rule']} · {item['evidence']}" for item in report["findings"])
    else:
        lines.extend(["", "No findings for the focused checks in this report."])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="local Nginx config or rendered nginx -T output")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)
    try:
        report = audit_config(parse_config(load_config(args.config)))
        print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_text(report), end="\n" if args.json else "")
        return 1 if report["summary"]["high"] or report["summary"]["warning"] else 0
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
