#!/usr/bin/env python3
"""Create data-minimized documentation from a local n8n workflow export."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

MAX_BYTES = 1_000_000
MAX_NODES = 500
MAX_EDGES = 2_000


class DocumentError(ValueError):
    """Raised when a workflow export is malformed or exceeds a safety limit."""


@dataclass(frozen=True)
class NodeDoc:
    name: str
    node_type: str
    type_version: str
    disabled: bool
    parameter_keys: tuple[str, ...]
    credential_types: tuple[str, ...]
    is_trigger: bool


@dataclass(frozen=True)
class EdgeDoc:
    source: str
    output: str
    target: str
    input_index: int


@dataclass(frozen=True)
class WorkflowDoc:
    name: str
    active: bool
    nodes: tuple[NodeDoc, ...]
    edges: tuple[EdgeDoc, ...]
    disconnected: tuple[str, ...]
    broken_targets: tuple[str, ...]
    settings_keys: tuple[str, ...]


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DocumentError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_export(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_BYTES:
            raise DocumentError("export exceeds 1 MB")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DocumentError(f"cannot read valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DocumentError("top level must be an object")
    return value


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DocumentError(f"{label} must be a non-empty string")
    if len(value) > 200:
        raise DocumentError(f"{label} exceeds 200 characters")
    return value.strip()


def _sorted_keys(value: Any, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise DocumentError(f"{label} must be an object")
    return tuple(sorted(str(key) for key in value))


def _is_trigger(node_type: str) -> bool:
    short = node_type.rsplit(".", 1)[-1].lower()
    return short.endswith("trigger") or short in {"webhook", "formtrigger"}


def build_document(export: dict[str, Any]) -> WorkflowDoc:
    name = _required_text(export.get("name", "Unnamed workflow"), "name")
    active = export.get("active", False)
    if not isinstance(active, bool):
        raise DocumentError("active must be a boolean")
    raw_nodes = export.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise DocumentError("nodes must be a non-empty array")
    if len(raw_nodes) > MAX_NODES:
        raise DocumentError(f"nodes has more than {MAX_NODES} entries")

    nodes: list[NodeDoc] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_nodes):
        label = f"nodes[{index}]"
        if not isinstance(raw, dict):
            raise DocumentError(f"{label} must be an object")
        node_name = _required_text(raw.get("name"), f"{label}.name")
        if node_name in names:
            raise DocumentError(f"duplicate node name: {node_name}")
        names.add(node_name)
        node_type = _required_text(raw.get("type"), f"{label}.type")
        version = raw.get("typeVersion", "unknown")
        if isinstance(version, bool) or not isinstance(version, (str, int, float)):
            raise DocumentError(f"{label}.typeVersion must be a string or number")
        disabled = raw.get("disabled", False)
        if not isinstance(disabled, bool):
            raise DocumentError(f"{label}.disabled must be a boolean")
        nodes.append(NodeDoc(
            name=node_name,
            node_type=node_type,
            type_version=str(version),
            disabled=disabled,
            parameter_keys=_sorted_keys(raw.get("parameters", {}), f"{label}.parameters"),
            credential_types=_sorted_keys(raw.get("credentials", {}), f"{label}.credentials"),
            is_trigger=_is_trigger(node_type),
        ))

    raw_connections = export.get("connections", {})
    if not isinstance(raw_connections, dict):
        raise DocumentError("connections must be an object")
    edges: list[EdgeDoc] = []
    broken: set[str] = set()
    connected: set[str] = set()
    for source, outputs in raw_connections.items():
        if source not in names:
            raise DocumentError(f"connection source is not a node: {source}")
        if not isinstance(outputs, dict):
            raise DocumentError(f"connections.{source} must be an object")
        for output, lanes in outputs.items():
            if not isinstance(lanes, list):
                raise DocumentError(f"connections.{source}.{output} must be an array")
            for lane in lanes:
                if not isinstance(lane, list):
                    raise DocumentError(f"connections.{source}.{output} lanes must be arrays")
                for link in lane:
                    if not isinstance(link, dict):
                        raise DocumentError("connection entry must be an object")
                    target = _required_text(link.get("node"), "connection target")
                    index = link.get("index", 0)
                    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
                        raise DocumentError("connection index must be a non-negative integer")
                    edges.append(EdgeDoc(str(source), str(output), target, index))
                    if len(edges) > MAX_EDGES:
                        raise DocumentError(f"connections has more than {MAX_EDGES} edges")
                    connected.add(str(source))
                    if target in names:
                        connected.add(target)
                    else:
                        broken.add(target)

    disconnected = tuple(node.name for node in nodes if node.name not in connected)
    return WorkflowDoc(
        name=name,
        active=active,
        nodes=tuple(nodes),
        edges=tuple(edges),
        disconnected=disconnected,
        broken_targets=tuple(sorted(broken)),
        settings_keys=_sorted_keys(export.get("settings", {}), "settings"),
    )


def to_json(doc: WorkflowDoc) -> str:
    payload = asdict(doc)
    payload["summary"] = {
        "nodes": len(doc.nodes),
        "connections": len(doc.edges),
        "triggers": sum(node.is_trigger for node in doc.nodes),
        "disabled": sum(node.disabled for node in doc.nodes),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_markdown(doc: WorkflowDoc) -> str:
    state = "active" if doc.active else "inactive"
    lines = [f"# {doc.name}", "", f"**State:** {state}  ", f"**Nodes:** {len(doc.nodes)}  ", f"**Connections:** {len(doc.edges)}", "", "## Nodes", "", "| Node | Type | Version | Trigger | Disabled | Parameter keys | Credential types |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for node in doc.nodes:
        lines.append("| " + " | ".join([
            node.name.replace("|", "\\|"), node.node_type.replace("|", "\\|"), node.type_version,
            "Yes" if node.is_trigger else "No", "Yes" if node.disabled else "No",
            ", ".join(node.parameter_keys) or "—", ", ".join(node.credential_types) or "—",
        ]) + " |")
    lines.extend(["", "## Connections", ""])
    if doc.edges:
        lines.extend(f"- `{edge.source}` → `{edge.target}` ({edge.output}, input {edge.input_index})" for edge in doc.edges)
    else:
        lines.append("No connections documented.")
    lines.extend(["", "## Review notes", ""])
    lines.append("- Disconnected nodes: " + (", ".join(doc.disconnected) or "none"))
    lines.append("- Broken target references: " + (", ".join(doc.broken_targets) or "none"))
    lines.append("- Workflow setting keys: " + (", ".join(doc.settings_keys) or "none"))
    lines.extend(["", "> Parameter values and credential identifiers are intentionally omitted."])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="local n8n workflow JSON export")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="write the document to this file")
    args = parser.parse_args(argv)
    try:
        doc = build_document(load_export(args.export))
        rendered = to_json(doc) if args.format == "json" else to_markdown(doc)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (DocumentError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1 if doc.broken_targets else 0


if __name__ == "__main__":
    raise SystemExit(main())
