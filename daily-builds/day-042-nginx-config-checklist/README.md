# Nginx Config Checklist

Day 042 of the 100 Days of Code challenge.

## Purpose

Nginx Config Checklist turns one local Nginx configuration into a small server-block inventory and a focused list of review items. It checks missing listeners and server names, incomplete TLS certificate/key pairs, repeated listener/name combinations, enabled directory indexes and unresolved includes.

It does not run Nginx, follow include files, validate certificates, reload services or prove that a deployment is secure. Review configuration only on systems you own or are authorized to administer.

## Run

Audit a local configuration:

```bash
python nginx_config_checklist.py /path/to/nginx.conf
python nginx_config_checklist.py /path/to/nginx.conf --json
```

For a complete local picture, an authorized administrator can first capture Nginx's rendered configuration and audit the saved file:

```bash
sudo nginx -T > nginx-rendered.conf
python nginx_config_checklist.py nginx-rendered.conf
```

The tool itself never runs that command. Rendered configuration can contain private hostnames and paths, so keep it local and review reports before sharing.

Exit code `0` means no high or warning findings from these focused checks, `1` means review findings exist, and `2` means the input could not be processed.

Run the included fictional sample:

```bash
python nginx_config_checklist.py sample-nginx.conf
```

Run the tests:

```bash
python -m unittest -v test_nginx_config_checklist.py
```

## Skills practiced

- Tokenizing comments, quoted values and nested Nginx blocks
- Deterministic configuration inventories
- Focused, evidence-based review rules
- Bounded local-file processing
- Python CLI exit codes and standard-library testing

## Next improvement

Add an opt-in allowlist file for intentionally repeated routes and approved autoindex locations.
