# Environment Drift Checklist — Day 050

A dependency-free, read-only Python CLI for reviewing **six declared observations** in two sanitized environment snapshots. It produces a small checklist without printing the supplied values.

## Run

Python 3.10+; no installation or external service required.

```sh
python drift.py baseline.json candidate.json
python drift.py baseline.json candidate.json --json
python drift.py baseline.json baseline.json --json
python -m unittest -v
```

The synthetic comparison reports **4 matches, 1 drift and 1 unverified check**. Its exit code is `1` by design. Comparing the baseline with itself reports six matches and exits `0`.

Exit codes: `0` = all six observations match; `1` = drift or missing evidence; `2` = invalid/unreadable input or CLI usage. Reports go to stdout; generic input errors go to stderr. No source files are changed.

## Snapshot format

Each JSON file must contain a `checks` object. The fixed check IDs are:

| Check | Suggested observation |
| --- | --- |
| `runtime_version` | Runtime name and exact version |
| `os_release` | OS release identifier |
| `dependency_lock` | Recorded lock-file digest or revision identifier |
| `schema_revision` | Recorded database schema revision |
| `timezone` | Declared application timezone |
| `feature_set` | Consistently ordered feature-set identifier |

Known observations, when present, must be nonblank strings of 1–256 characters without Unicode control/format characters. Missing keys remain unverified: missing baseline, missing candidate or missing both. `null` is invalid, not a missing-key substitute. Unknown fields are ignored and never copied into the report.

Each file is capped at **1,000,000 bytes** and duplicate JSON keys are rejected. Comparisons are **exact string equality**: case, spacing, ordering and version formatting differences count as drift. Use consistent recording conventions. A dependency-lock identifier is compared as text; the tool does not compute or verify a digest. An empty `checks` object is accepted but all six checks remain unverified.

## Interpreting the checklist

- A known check is `match` only when both observations are present and equal.
- It is `drift` when both are present and differ.
- It is `unverified` when either observation is absent.
- Overall status prioritizes `drift`, then `unverified`, then `aligned`.

This is a snapshot-review aid, **not a live collector, compliance audit or security certification**. Matching records do not prove that a server is healthy, that the snapshots are fresh or authentic, or that other differences do not exist. Missing evidence is not a successful check. Baseline selection and acceptable differences require human review.

Use authorized, manually sanitized snapshots only. Reports omit observation values and arbitrary fields, but input files may still contain sensitive data. Do not place credentials or personal data in them. There are no server/database connections, command execution, remediation, or automatic configuration changes.

## Skills practiced

Environment baseline modeling, evidence-aware checklist states, deterministic comparisons, data minimization, bounded JSON loading, CLI exit codes and standard-library unit/integration tests.

## Next improvement

Add explicit snapshot capture dates and a documented freshness policy, keeping stale evidence separate from differences. Do not infer freshness from filenames or matching values.
