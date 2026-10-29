# n8n Workflow Documenter

n8n Workflow Documenter is a dependency-free Python CLI that turns a local n8n workflow export into a compact Markdown or JSON reference. It lists nodes, node types, versions, trigger status, connection paths, disconnected nodes, broken target references, parameter key names, credential types, and workflow setting keys.

Parameter values and credential identifiers are deliberately omitted. The tool reads a file only: it does not connect to n8n, run a workflow, inspect execution data, validate business logic, or prove production readiness. Review exports before sharing them because node names can still describe internal processes.

## Run

Python 3.10 or newer is enough.

```bash
python3 workflow_documenter.py example-workflow.json
python3 workflow_documenter.py example-workflow.json --format json
python3 workflow_documenter.py example-workflow.json --output workflow.md
```

Exit code `0` means the export was documented without broken targets, `1` means the document was created but references a missing target node, and `2` means the export was invalid or unreadable.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile workflow_documenter.py test_workflow_documenter.py
```

## Skills practiced

- Defensive parsing of a real-world JSON shape
- Graph edge extraction and structural review
- Markdown and JSON report generation
- Data minimization for parameters and credentials
- Standard-library CLI design and tests

## Next improvement

Add an optional Mermaid flowchart renderer with careful escaping and a documented node-count limit.
