# Day 063 — Accessibility Audit Checklist

A dependency-free Python CLI that turns a small manual accessibility review into a prioritized Markdown or JSON report. It highlights release blockers, incomplete checks, evidence and next actions without claiming to certify WCAG conformance.

## Run

```bash
python accessibility_audit.py sample-audit.json
python accessibility_audit.py sample-audit.json --format json
python -m unittest -v
```

Exit code `1` means at least one blocker check failed; invalid input returns `2`.

## Skills practiced

- Manual test checklist modeling
- Evidence and remediation tracking
- Deterministic report generation
- Defensive JSON validation and resource limits
- Standard-library unit testing

## Next improvement

Add optional checklist profiles for common page types while keeping every result tied to human-reviewed evidence.
