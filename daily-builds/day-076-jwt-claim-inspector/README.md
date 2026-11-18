# Day 076 — JWT Claim Inspector

Inspect the header, payload and time claims of a synthetic compact JWT locally, without uploading it to a decoder website. Python 3.10+; no dependencies.

## Run

```sh
python inspector.py sample.jwt --now 100
python -m unittest -v
```

The sample is deliberately unsigned and fictional. At Unix second 100 its expiration has not been reached, its not-before time has been reached, and its issued-at time is in the past. Omit `--now` to use the current clock. Exit 0 means inspection completed, **not** that a token is trustworthy; exit 2 means input could not be inspected.

## Scope

Reads one UTF-8 file, maximum 16 KiB. Accepts three-part compact serialization, canonical unpadded base64url, and JSON header/payload objects. Rejects duplicate JSON keys, nonfinite constants, malformed encoding and unsupported five-part encrypted tokens. Empty signatures are allowed for inspection. The report preserves decoded values and flags absent, invalid or time-relative `exp`, `nbf` and `iat` claims with zero clock leeway. JSON escaping prevents terminal escape characters from being emitted literally.

**No signature verification, algorithm validation, issuer/audience checks or authorization decision.** Decoded data is untrusted. A future `iat` is an observation, not a universal rejection policy. Other malformed claims can still be displayed. Use synthetic tokens: output contains all decoded claims and is not redacted. No network requests, key lookup, file modification or token storage occurs in this program; shell redirection can persist its output.

## Skills practiced

Defensive base64url/JSON parsing, JWT trust boundaries, NumericDate comparisons, deterministic clocks, bounded file input and standard-library tests. Sixteen tests cover time boundaries, wrong types, malformed segments, duplicate keys, unverified signatures and CLI behavior.

## Next improvement

Add an opt-in allowlist of displayed claim names to reduce accidental disclosure during demonstrations. Keep cryptographic verification separate from this inspector.

Reference: [RFC 7519, registered claims and trust decisions](https://www.rfc-editor.org/rfc/rfc7519), reviewed November 18, 2026. This is an original small implementation, not copied RFC sample code.
