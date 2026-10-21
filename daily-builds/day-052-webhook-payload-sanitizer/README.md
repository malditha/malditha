# Webhook Payload Sanitizer

Day 052 of the 100 Days of Code challenge.

## Purpose

Webhook Payload Sanitizer prepares a local JSON payload for safer debugging and sharing. It recursively masks or removes values whose keys look like credentials while preserving the payload's useful structure.

It is a defensive helper, not a guarantee that a payload contains no sensitive data. It does not detect sensitive free text, transmit webhooks, call external services, inspect credentials or modify the input file. Review sanitized output before sharing it.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
python sanitizer.py payload.json
python sanitizer.py payload.json --strategy remove
python sanitizer.py payload.json --sensitive-key internal_code --report
```

Sanitized JSON is written to standard output. With `--report`, metadata goes to standard error so it can be captured separately. Exit code `0` means sanitization succeeded; `2` means the input or options were unsafe or invalid.

Run the tests:

```bash
python -m unittest -v test_sanitizer.py
```

## Safety boundaries

- Masks conservative credential-like keys such as `password`, `authorization`, `api_key`, `cookie`, `secret` and token fields
- Normalizes camelCase, snake_case and punctuated keys before matching
- Supports repeatable custom sensitive keys
- Rejects duplicate JSON keys, malformed object keys, files over 1 MB, nesting beyond 20 levels and payloads over 10,000 visited nodes
- Reports only redacted paths and counts, never redacted values

Field names and non-matching values can still be sensitive. Use fictional input for demos and inspect the result before logging or sharing it.

## Skills practiced

- Recursive JSON traversal
- Conservative sensitive-key matching
- Data-minimized reporting
- Bounded input handling and duplicate-key rejection
- Automation-friendly standard streams and exit codes
- Standard-library testing with `unittest`

## Next improvement

Add an explicit allowlist mode for teams that want to retain only a known-safe payload schema instead of relying on sensitive-key detection.
