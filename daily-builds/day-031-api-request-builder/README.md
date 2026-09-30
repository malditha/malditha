# API Request Builder

Day 031 of the 100 Days of Code challenge.

API Request Builder turns a small JSON specification into a deterministic request preview and shell-safe cURL command. It solves a narrow problem: reviewing a request's method, URL, query parameters, headers and JSON body before anything reaches the network.

The tool never sends a request. Sensitive header values such as authorization, cookies, tokens and API keys are replaced with `[REDACTED]` in every output.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
python3 api_request_builder.py sample-request.json
python3 api_request_builder.py sample-request.json --format json
```

The accepted top-level fields are `method`, `url`, `query`, `headers` and `json`. URLs must use HTTP or HTTPS and cannot contain embedded credentials or fragments. Inputs, collections and body sizes are bounded, and GET or HEAD requests cannot include a JSON body.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile api_request_builder.py test_api_request_builder.py
```

## Skills practiced

- Defensive JSON validation and bounded inputs
- URL parsing and deterministic query encoding
- Sensitive-header redaction and data minimization
- Shell-safe command composition with `shlex`
- Human-readable and machine-readable CLI reports
- Standard-library unit and subprocess testing

## Design boundaries

- Does not make HTTP requests or test credentials
- Does not save request data or inspect environment variables
- Always redacts sensitive header values, including in cURL output
- Rejects unknown fields, header line breaks and unsafe URL forms
- Exit code `0` means a preview was created; `2` means validation failed

Use generated commands only with endpoints you own or are authorized to access, and review the preview before execution.

## Next improvement

Add optional OpenAPI operation lookup so the builder can compare a request shape with a local API contract without making a network call.
