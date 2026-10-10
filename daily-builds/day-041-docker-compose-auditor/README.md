# Docker Compose Auditor

Day 041 of the 100 Days of Code challenge.

## Purpose

Docker Compose Auditor provides a small, read-only review of normalized Compose configuration. It identifies privileged containers, host networking, unpinned images, publicly published ports, writable host bind mounts and missing health checks.

It reads JSON produced by Docker Compose and never invokes Docker, starts containers or prints environment-variable values.

## Run

Generate normalized JSON with Docker Compose, then audit that local file:

```bash
docker compose config --format json > compose.resolved.json
python docker_compose_auditor.py compose.resolved.json
python docker_compose_auditor.py compose.resolved.json --json --output audit.json
```

Test the included fictional sample:

```bash
python docker_compose_auditor.py sample-compose.json
```

Exit code `0` means no high or warning findings, `1` means review findings exist, and `2` means the input could not be audited.

Run the tests:

```bash
python -m unittest -v test_docker_compose_auditor.py
```

## Skills practiced

- Docker Compose configuration structure
- Defensive JSON validation and bounded processing
- Privacy-conscious configuration reporting
- Deterministic rule-based auditing
- Python standard-library tests and CLI exit codes

## Next improvement

Add opt-in policy files so teams can document approved exceptions without hiding the default audit evidence.
