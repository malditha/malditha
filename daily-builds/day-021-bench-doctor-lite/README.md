# Bench Doctor Lite

Bench Doctor Lite is a dependency-free, read-only Python CLI for a quick structural check of a Frappe or ERPNext bench. It checks expected directories, the apps registry, `Procfile`, common configuration, discovered site configurations and whether the scheduler is marked as paused.

It never runs Bench commands, changes files or includes configuration values in its report.

## Run it

Requires Python 3.11 or newer.

```bash
python3 bench_doctor.py /path/to/frappe-bench
python3 bench_doctor.py /path/to/frappe-bench --json
```

Exit code `0` means every check passed, `1` means warnings or failures were found, and `2` means the supplied directory could not be inspected.

## Test it

```bash
python3 -m unittest -v
```

Tests use temporary fictional benches and do not require Frappe, ERPNext, Redis, a database or network access.

## Skills practiced

- Frappe bench directory conventions
- Defensive filesystem and JSON inspection
- Privacy-conscious diagnostic reporting
- Stable text and JSON output
- Automation-friendly exit codes

## Next improvement

Add an explicit opt-in check that reads sanitized `bench doctor` output without executing Bench commands itself.
