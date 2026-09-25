# Naming Series Tester

Naming Series Tester is a dependency-free Python CLI for checking a small, explicit subset of Frappe-style naming patterns before using them in a real system. It validates the counter, substitutes a chosen date and safe sample fields, and previews deterministic names.

It never connects to Frappe, reads the current series value, reserves a name, or modifies a document.

## Run

Requires Python 3.10 or newer.

```bash
cd daily-builds/day-026-naming-series-tester
python3 naming_series_tester.py 'INV-.branch.-YYYY-MM-#####' \
  --field branch=MNL --date 2026-09-25 --start 7 --count 3
```

JSON output is available with `--json`.

Supported preview tokens:

- one `#` counter group, from 1 to 9 digits
- `YYYY`, `YY`, `MM`, and `DD`
- field tokens such as `.branch.`, supplied with `--field branch=MNL`
- literal separators and prefixes

This is intentionally not a complete reimplementation of Frappe's naming engine. Confirm a pattern against the Frappe version used by the target site before deployment.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile naming_series_tester.py
```

## Skills practiced

- Small grammar tokenization and validation
- Deterministic date and counter formatting
- Defensive CLI input boundaries
- Privacy-conscious reporting
- Standard-library unit testing

## Next improvement

Add an opt-in compatibility profile for more Frappe naming tokens, backed by version-specific fixtures.
