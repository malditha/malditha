#!/usr/bin/env python3
"""Validate and map retry and error paths in a small workflow definition."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_BYTES = 100_000
MAX_NODES = 100
KINDS = {"trigger", "action", "retry", "error_handler"}


class InputError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key")
        result[key] = value
    return result


def load_workflow(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_BYTES:
        raise InputError("file exceeds 100 KB")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("could not read valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise InputError("workflow must be an object")
    if set(value) != {"name", "nodes"}:
        raise InputError("workflow must contain only name and nodes")
    if not isinstance(value["name"], str) or not 1 <= len(value["name"].strip()) <= 80:
        raise InputError("name must contain 1 to 80 characters")
    nodes = value["nodes"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        raise InputError("nodes must contain 1 to 100 entries")
    ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not set(node).issubset({"id", "kind", "next", "on_error"}):
            raise InputError("each node has invalid fields")
        if set(node) < {"id", "kind", "next"}:
            raise InputError("each node requires id, kind and next")
        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id.isidentifier() or len(node_id) > 40:
            raise InputError("node id must be a short identifier")
        if node_id in ids:
            raise InputError("node ids must be unique")
        ids.add(node_id)
        if node["kind"] not in KINDS:
            raise InputError("node kind is unsupported")
        if not isinstance(node["next"], list) or len(node["next"]) > 10 or not all(isinstance(x, str) for x in node["next"]):
            raise InputError("next must be a list of up to 10 node ids")
        if "on_error" in node and node["on_error"] is not None and not isinstance(node["on_error"], str):
            raise InputError("on_error must be a node id or null")
    for node in nodes:
        refs = node["next"] + ([node["on_error"]] if node.get("on_error") else [])
        if any(ref not in ids for ref in refs):
            raise InputError("all referenced node ids must exist")
    return {"name": value["name"].strip(), "nodes": nodes}


def _reachable(start: str, edges: dict[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(edges[current])
    return seen


def analyze(workflow: dict[str, Any]) -> dict[str, Any]:
    nodes = workflow["nodes"]
    by_id = {node["id"]: node for node in nodes}
    normal = {node["id"]: list(node["next"]) for node in nodes}
    combined = {node["id"]: list(node["next"]) + ([node["on_error"]] if node.get("on_error") else []) for node in nodes}
    triggers = [node["id"] for node in nodes if node["kind"] == "trigger"]
    reachable: set[str] = set()
    for trigger in triggers:
        reachable |= _reachable(trigger, combined)
    issues: list[dict[str, str]] = []
    if len(triggers) != 1:
        issues.append({"code": "trigger_count", "node": "workflow", "message": "workflow must have exactly one trigger"})
    for node in nodes:
        node_id = node["id"]
        if node_id not in reachable:
            issues.append({"code": "unreachable", "node": node_id, "message": "node is unreachable from a trigger"})
        if node["kind"] == "action":
            error_id = node.get("on_error")
            if not error_id:
                issues.append({"code": "missing_error_path", "node": node_id, "message": "action has no error path"})
            elif by_id[error_id]["kind"] not in {"retry", "error_handler"}:
                issues.append({"code": "invalid_error_target", "node": node_id, "message": "error path does not start with retry or error handler"})
        if node["kind"] == "retry":
            if not any(by_id[target]["kind"] == "action" for target in normal[node_id]):
                issues.append({"code": "retry_without_action", "node": node_id, "message": "retry path does not return to an action"})
        if node["kind"] == "error_handler" and node["next"]:
            issues.append({"code": "handler_not_terminal", "node": node_id, "message": "error handler should be terminal"})
    return {
        "workflow": workflow["name"],
        "status": "review" if issues else "ready",
        "counts": {"nodes": len(nodes), "reachable": len(reachable), "issues": len(issues)},
        "paths": [
            {"node": node["id"], "kind": node["kind"], "success": node["next"], "error": node.get("on_error")}
            for node in nodes
        ],
        "issues": issues,
    }


def format_text(report: dict[str, Any]) -> str:
    lines = [f"Retry and Error Workflow Map: {report['workflow']}", f"Status: {report['status'].upper()}", "", "Paths:"]
    for path in report["paths"]:
        success = ", ".join(path["success"]) or "end"
        error = path["error"] or "none"
        lines.append(f"- {path['node']} [{path['kind']}]: success -> {success}; error -> {error}")
    lines.extend(["", "Issues:"])
    if report["issues"]:
        lines.extend(f"- {item['node']}: {item['message']} ({item['code']})" for item in report["issues"])
    else:
        lines.append("- none")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = analyze(load_workflow(args.workflow))
    except (InputError, OSError) as exc:
        parser.exit(2, f"input error: {exc}\n")
    print(json.dumps(report, indent=2) if args.json else format_text(report))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
