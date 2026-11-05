# Release Checklist Generator

A dependency-free Python CLI that turns a small release profile into a deterministic before-and-after checklist. It solves the problem of remembering conditional work such as database backups, rollback planning and customer communication.

## Run

Requires Python 3.10+.

```bash
python3 release_checklist_generator.py sample-release.json
python3 release_checklist_generator.py sample-release.json --json
```

## Test

```bash
python3 -m unittest -v
```

## Input and limits

The JSON profile declares a short `release_id`, one or more supported components, a risk level and whether the change is customer-facing. The tool adds focused tasks for application, database and infrastructure releases. It rejects duplicate keys, unknown fields, unsupported values and files over 128 KB.

The generated list supports release planning; it does not prove that a release is safe or replace team-specific review.

## Skills practiced

- Deterministic rule-based generation
- Release and rollback planning
- Defensive JSON validation
- Markdown and JSON reporting
- Standard-library unit testing

## Next improvement

Add an optional policy file so a team can define its own approved checklist rules while preserving deterministic output.
