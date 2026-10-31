# Day 062 — API Contract Test Starter

Generate a compact, deterministic set of request and response contract cases from a small JSON API definition. It gives developers a reviewable starting point before wiring cases into a real test runner.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python3 api_contract_test_starter.py example-contract.json
python3 api_contract_test_starter.py example-contract.json --output contract-cases.json
python3 -m unittest -v
```

The tool does **not** call an API, send credentials, or claim that generated cases prove an endpoint is correct. It produces candidate fixtures for human review and later test-runner integration.

## Contract format

Define a name, HTTP method, path, request parameters, expected success status, and required response fields. Supported value types are `string`, `integer`, `number`, `boolean`, `object`, `array`, and response `null`.

The generated plan includes:

- one valid baseline request and response;
- missing-required-parameter cases;
- wrong request-parameter type cases;
- an unexpected response status case;
- missing and wrong-type response-field cases.

Input is limited to 256 KB, 100 parameters, and 100 required response fields. Duplicate JSON keys, duplicate parameter names, unknown fields, invalid examples, and unsupported types are rejected.

## Skills practiced

- API contract modeling
- Positive and negative test design
- Deterministic fixture generation
- Defensive JSON validation
- Standard-library CLI and unit testing

## Next improvement

Add an opt-in adapter that exports the reviewed plan as `pytest` parameter tables without executing network requests.
