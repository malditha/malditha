# Config Diff

Config Diff is a dependency-free Python CLI that compares two JSON configuration files and reports which paths were added, removed, changed or changed type. It deliberately omits configuration values so a useful drift report does not become a secret-leak report.

## Run it

Requires Python 3.11 or newer.

```bash
python3 config_diff.py baseline.json candidate.json
python3 config_diff.py baseline.json candidate.json --ignore runtime.generated_at
python3 config_diff.py baseline.json candidate.json --json
```

Exit code `0` means the files match, `1` means differences were found, and `2` means an input could not be read or parsed. The command never edits either file.

## Test it

```bash
python3 -m unittest -v
```

The tests cover nested objects, arrays, added and removed paths, scalar and type changes, ignored branches, deterministic ordering, value-free reports and CLI exit codes.

## Skills practiced

- Recursive comparison of JSON objects and arrays
- Privacy-conscious reporting through data minimization
- Deterministic text and JSON output
- Automation-friendly command-line exit codes
- Standard-library unit testing

## Next improvement

Add YAML support behind an optional parser while keeping the core comparison model format-independent.
