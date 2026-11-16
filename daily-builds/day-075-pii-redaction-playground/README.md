# Day 075 — PII Redaction Playground

Practice explicit field redaction on synthetic JSON before sharing structured examples. Python 3.10+, standard library only. This is a local CLI, not a PII detector or an anonymization guarantee.

## Run

```sh
python redact.py sample.json --key name --key email
python -m unittest -v
```

The supplied fixture is entirely synthetic. Selected object keys match exactly, case-insensitively, at every depth. Their entire values (including nested objects or arrays) become `[REDACTED]`. Other values, object keys, array order and scalar types remain unchanged. Repeating keys is harmless. The original file is never modified; output goes to stdout. Exit 0 means transformation completed, not that the output is safe to share. Exit 2 reports invalid input without echoing its contents or path.

## Boundaries

Input is UTF-8 JSON capped at 64 KiB. Duplicate object keys, nonfinite JSON constants and excessive traversed nesting (over 40 levels) are rejected. A selected subtree is replaced without traversal. Key selections must be nonempty and at most 100 characters each.

No network, telemetry, storage service or automatic field inference is used. Unselected free text, identifying object keys, alternate spellings and indirect identifiers survive unchanged. Output can still contain personal data. Use synthetic examples; manually review all output before sharing. This playground does not certify privacy, compliance or irreversible anonymization. Redirect output only to a location you intend to write; do not redirect onto the source file.

## Skills practiced

Recursive JSON transformation, explicit data minimization, defensive parsing, deterministic output and unit tests.

## Next improvement

Add a value-free preview of selected field locations so users can review coverage before generating output.
