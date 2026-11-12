# Day 072 — Security Header Explorer

An offline inventory of six browser response headers. Helps reviewers see missing, empty and repeated headers without mistaking presence for protection. Python 3.10+, no dependencies or network calls.

## Run

```sh
python explorer.py sample.txt
python -m unittest -v
```

Provide UTF-8 `Name: value` lines from **one response**, without its HTTP status line or body. Blank lines are ignored. Folded headers, malformed names, control characters and files over 64 KiB are rejected. Invalid input exits 2; a completed inventory exits 0 even when headers are missing.

The report covers Content-Security-Policy, Strict-Transport-Security, X-Content-Type-Options, Referrer-Policy, X-Frame-Options and Permissions-Policy. It reports presence and occurrence counts, flags repeated fields for manual review, and checks for a single literal `nosniff` value. Header names are case-insensitive. Raw values and unrelated headers (including cookies) are omitted from output; this is not a general-purpose redactor. Review input before sharing it.

No URL fetching, policy parsing, security score or deployment changes. A present header may be ineffective or inappropriate. HSTS needs HTTPS context; CSP needs application-specific review; repeated headers have header-specific semantics. Missing fields are investigation prompts, not proof of a vulnerability.

## Skills practiced

HTTP header handling, case normalization, data minimization, bounded input and deterministic tests.

## Next improvement

Add explicit response-scheme context and directive explanations without turning presence checks into a security verdict.

## References

- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security
