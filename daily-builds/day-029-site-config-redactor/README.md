# Site Config Redactor

Site Config Redactor creates a conservative, sanitized copy of a Frappe `site_config.json` file for support or review. It keeps only a small allowlist of operational settings and replaces every other value with `[REDACTED]`.

The tool is dependency-free, read-only and local. It never edits the source file, connects to a Frappe site or uploads data.

## Run it

Python 3.10 or newer is recommended.

```bash
python3 site_config_redactor.py sample-site-config.json
python3 site_config_redactor.py sample-site-config.json --output redacted-report.json
```

Run the tests:

```bash
python3 -m unittest -v
```

The JSON report contains the sanitized configuration plus lists and counts of retained and redacted keys. Values for unknown fields are never included.

## Safety boundary

This is an allowlist-based first pass, not proof that a file is safe to publish. Review the generated copy before sharing it. Key names remain visible, and even ordinary operational settings can reveal details about a system. Never share the original site configuration.

## Skills practiced

- Conservative allowlist design
- Defensive JSON validation
- Data minimization and deterministic output
- Python CLI structure and standard-library tests

## Next improvement

Add an optional policy file so teams can define their own reviewed allowlist without changing the program.
