# OpenAPI Endpoint Index

Day 040 of the 100 Days of Code challenge.

## Purpose

OpenAPI files can be large enough that a quick inventory becomes awkward. This dependency-free Python CLI reads a **local OpenAPI 3.x JSON document** and produces a compact endpoint index with methods, paths, operation IDs, summaries, tags, parameter counts, response codes and deprecation flags.

It is deliberately read-only: it does not fetch remote specifications, send API requests or expose example payload values.

## Run

```bash
python openapi_endpoint_index.py sample-openapi.json
python openapi_endpoint_index.py sample-openapi.json --json
python openapi_endpoint_index.py sample-openapi.json --json --output endpoint-index.json
```

The input is limited to 2 MB and 500 operations. Invalid documents return exit code `2`.

Run the tests:

```bash
python -m unittest -v test_openapi_endpoint_index.py
```

## Skills practiced

- OpenAPI 3.x document structure
- Defensive JSON validation and bounded input handling
- Deterministic data indexing and text reporting
- Data minimization with allowlisted metadata
- Python standard-library tests and CLI exit codes

## Next improvement

Add optional tag and path-prefix filters while keeping the default report deterministic and read-only.
