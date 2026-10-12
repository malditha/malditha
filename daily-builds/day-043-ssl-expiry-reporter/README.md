# Day 043 — SSL Expiry Reporter

SSL Expiry Reporter is a dependency-free Python CLI for checking the remaining validity of a small, explicit list of TLS endpoints. It solves a focused operational problem: finding certificates that need attention before their expiration date becomes an outage.

The tool uses Python's default trusted certificate authorities and hostname verification. It does not bypass certificate errors, scan address ranges, store certificate bodies, change services or renew certificates.

## Run it

Python 3.10 or newer is recommended.

```bash
python ssl_expiry_reporter.py example.com api.example.com:8443
python ssl_expiry_reporter.py example.com --warning-days 45 --critical-days 10 --json
```

Only check public services or systems you own or are authorized to inspect. Input is bounded to 20 endpoints, and the per-endpoint timeout is bounded from 0.1 to 30 seconds.

Exit codes:

- `0` — every checked certificate is healthy
- `1` — at least one endpoint is warning, critical, expired or unavailable
- `2` — command-line input is invalid

## Test it

```bash
python -m unittest -v
python -m py_compile ssl_expiry_reporter.py test_ssl_expiry_reporter.py
```

The automated suite does not contact the network. It injects deterministic certificate responses and failures so expiry boundaries, sanitized errors and CLI behavior remain repeatable.

## Skills practiced

- Verified TLS connections with Python's standard library
- Timezone-aware certificate-expiry calculations
- Bounded endpoint and timeout validation
- Deterministic text and JSON reports
- Sanitized network-error classification
- Dependency injection for network-free tests

## Deliberate boundaries

- No disabled hostname or certificate verification
- No IP-range discovery or port scanning
- No certificate renewal or service changes
- No private keys, full certificates or issuer details in reports
- No claim that expiry is the only measure of TLS health

## Next improvement

Add an opt-in JSON input file with friendly service labels, while preserving the 20-endpoint boundary and never accepting credentials or private keys.
