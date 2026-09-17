# Port Probe Report

A dependency-free Python CLI that checks a small, explicit list of TCP ports on a host you are authorized to inspect. It distinguishes open, refused, timed-out and other connection errors, then prints a readable or JSON report.

This is a connectivity diagnostic—not a vulnerability scanner. It limits each run to 100 ports and never performs service exploitation or UDP scanning.

## Run

Requires Python 3.11 or newer.

```bash
python3 port_probe_report.py 127.0.0.1 22,80,443
python3 port_probe_report.py localhost 8000-8005 --timeout 0.5 --json
```

Use it only against devices and services you own or are authorized to check.

## Test

```bash
python3 -m unittest discover -s tests -v
```

The tests inject fake connections, so they are deterministic and do not probe the public network.

## Skills practiced

- TCP connection handling with explicit timeouts
- Input validation for ports and bounded ranges
- Failure classification without false “healthy” results
- Human-readable and JSON reports
- Dependency injection for network-free tests

## Next improvement

Add an opt-in configuration file for named, approved endpoints so recurring checks do not require repeating host and port arguments.
