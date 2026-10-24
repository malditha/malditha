# Retry and Error Workflow Map

Day 055 of the 100 Days of Code challenge.

## Purpose

Retry and Error Workflow Map turns a small, sanitized workflow definition into a readable success-and-failure path inventory. It highlights unreachable nodes, actions without error paths, retries that do not return to an action, and non-terminal error handlers before a workflow is implemented.

It does not execute n8n, call webhooks, inspect credentials, prove that a retry policy is safe, or replace testing in the target automation platform.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
python retry_error_map.py workflow.json
python retry_error_map.py workflow.json --json
```

Exit code `0` means the map passed its structural checks, `1` means review issues were found, and `2` means the input was invalid.

Run the tests:

```bash
python -m unittest -v test_retry_error_map.py
```

## Input boundaries

- Supports trigger, action, retry and error-handler nodes
- Limits input to 100 nodes, 10 outgoing paths per node and 100 KB
- Requires every referenced node ID to exist
- Rejects duplicate JSON keys and undeclared fields
- Reports structure only; the input should contain no payload values or credentials

## Skills practiced

- Directed workflow graph traversal
- Retry and failure-path modeling
- Defensive JSON validation
- Deterministic text and JSON reports
- Automation-friendly exit codes
- Standard-library testing with `unittest`

## Next improvement

Add optional retry-policy fields for bounded attempt counts and backoff documentation.
