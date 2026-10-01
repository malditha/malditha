# Webhook Signature Lab

Day 032 of the 100 Days of Code challenge.

Webhook Signature Lab signs or verifies a local webhook payload with a timestamped HMAC-SHA256 signature. It solves one clear problem: confirming that raw payload bytes and a shared secret produce an expected signature before wiring verification into an application.

The tool is dependency-free, makes no network request and reads its secret only from a named environment variable. The secret is never included in text or JSON output.

## Run

Requires Python 3.10 or newer. Use only a disposable development secret in examples.

    export WEBHOOK_SECRET="replace-with-at-least-16-dev-characters"
    python3 webhook_signature_lab.py sign sample-payload.json --timestamp 1700000000

Copy the generated header, then verify it against the same raw payload:

    python3 webhook_signature_lab.py verify sample-payload.json       --header "t=1700000000,v1=GENERATED_HEX_SIGNATURE"       --now 1700000000

Add --format json for machine-readable output. Verification returns exit code 0 for a valid signature, 1 for a mismatch or timestamp outside the tolerance, and 2 for invalid input.

## Test

    python3 -m unittest -v
    python3 -m py_compile webhook_signature_lab.py test_webhook_signature_lab.py

## Skills practiced

- Raw-byte webhook payload handling
- HMAC-SHA256 signing
- Constant-time signature comparison
- Timestamp tolerance and replay-age checks
- Defensive signature-header parsing
- Environment-based secret handling
- Standard-library unit and subprocess testing

## Design boundaries

- Uses the documented local scheme t=timestamp,v1=hex_signature
- Signs timestamp + period + exact payload bytes
- Supports up to five v1 signatures for safe key rotation exercises
- Rejects oversized payloads and malformed headers
- Never contacts a webhook endpoint or stores the secret
- Demonstrates a provider-neutral pattern, not a drop-in verifier for every vendor

Always follow a real provider's exact signing specification in production.

## Next improvement

Add small adapters for locally supplied Stripe-style and GitHub-style headers while keeping the core verifier provider-neutral and network-free.
