# Notification Template Lab

Notification Template Lab is a dependency-free Python CLI for checking local notification templates before they are copied into n8n or another workflow tool. It finds placeholders in the subject and body, reports missing and unused variables, and renders a preview only when every placeholder has a value.

It does not send notifications, connect to n8n, fetch secrets, or prove that a production workflow is safe. Preview files can contain sample values, so use synthetic data and keep them out of production logs.

## Run

Python 3.10 or newer is enough.

```bash
python3 notification_template_lab.py example.json
python3 notification_template_lab.py example.json --format json
```

Exit code `0` means every template is ready, `1` means at least one template is blocked by missing data, and `2` means the plan itself is invalid.

## Input

Each item needs an `id`, `channel`, `body`, and flat `data` object. `subject` is optional. Placeholders use `{{variable_name}}`; string and number values are accepted. The parser rejects duplicate JSON keys, duplicate template IDs, unknown fields, nested data, oversized input, and invalid variable names.

## Test

```bash
python3 -m unittest -v
python3 -m py_compile notification_template_lab.py test_notification_template_lab.py
```

## Skills practiced

- Regular-expression token extraction
- Deterministic validation and rendering
- Defensive JSON parsing and size limits
- Data-minimized diagnostics
- Standard-library CLI design and tests

## Next improvement

Add opt-in channel rules, such as requiring a subject for email, while keeping the core renderer independent from any delivery provider.
