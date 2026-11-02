# Day 064 — Visual Regression Manifest

A dependency-free Python CLI that inventories local PNG screenshots by relative path, dimensions, byte size and SHA-256 hash, then compares two manifests. It exposes added, removed and changed files for human review without deciding whether a visual change is acceptable.

## Run

```bash
python visual_manifest.py compare baseline.json current.json
python visual_manifest.py compare baseline.json current.json --format json
python visual_manifest.py create path/to/screenshots manifest.json
python -m unittest -v
```

A comparison returns exit code `1` when files differ and `2` for invalid input.

## Skills practiced

- Visual-regression evidence modeling
- PNG header parsing and SHA-256 hashing
- Deterministic manifest comparison
- Defensive path and JSON validation
- Standard-library unit testing

## Next improvement

Add an optional review file where a human can record the reason and approval state for each expected visual change.
