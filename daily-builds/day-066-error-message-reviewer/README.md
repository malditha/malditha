# Error Message Reviewer

A small Python CLI that reviews user-facing error-message copy for clarity, safe wording and an actionable next step. It reports rules by message ID and never includes submitted message text in its output.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python3 error_message_reviewer.py sample-messages.json
python3 error_message_reviewer.py sample-messages.json --json
```

Exit code `0` means every message is ready, `1` means at least one needs review, and `2` means the input is invalid.

## Test

```bash
python3 -m unittest -v
```

## Input

Pass a JSON array of objects containing only `id` and `text`. The tool checks empty or generic copy, internal technical details, blaming language, excessive length and missing recovery guidance. These are focused editorial signals, not proof that a message is accessible or correct in its product context.

## Skills practiced

- Deterministic content linting
- Privacy-conscious reports
- Defensive JSON and duplicate-key validation
- Bounded input handling and meaningful CLI exit codes
- Standard-library unit testing

## Next improvement

Add an optional product-context field so teams can review whether each message accurately names the affected action without exposing user data.
