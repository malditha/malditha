# Day 073 — CSP Builder Lite

Build a deterministic **Content-Security-Policy-Report-Only** header draft from a small JSON source inventory. This avoids hand-joining directives while keeping every source explicit. Python 3.10+, standard library only.

## Run

```sh
python builder.py sample.json
python -m unittest -v
```

Input is a JSON object mapping directive names to arrays of sources. `default-src` is required. Supported directives: default-src, script-src, style-src, img-src, connect-src, font-src, object-src, base-uri, frame-ancestors. Each accepts 1–20 sources: quoted `'self'`, quoted `'none'`, or lowercase HTTPS origins with an optional port (1–65535). No paths, wildcards, credentials, queries, data URLs, nonces or hashes. `'none'` must stand alone. Duplicate keys/sources and unknown directives are rejected. Input is capped at 32 KiB. Output order is fixed; sources sort lexically. Errors exit 2.

## Scope and safe use

This is an intentionally restricted draft generator, not a complete CSP parser, scanner or recommended policy. It performs no network requests and changes no server configuration. Use only origins you control or have reviewed. The sample is fictional and is not a production policy.

Report-Only does not enforce the policy. Review browser violations and test application flows before deciding on an enforcing policy. This tool does not configure a reporting endpoint; it provides no report collection. A report-only header must be delivered as an HTTP response header, not a meta tag. `default-src` is a fallback for relevant fetch directives; it does not replace explicit `base-uri` or `frame-ancestors`. Presence of directives does not establish protection. Existing enforcing policies are separate and are not weakened by this draft.

## Skills practiced

Security policy modeling, explicit allowlists, defensive JSON validation, deterministic serialization and unit tests.

## Next improvement

Add a separate explanation report identifying omitted directives and their fallback behavior, without automatically broadening sources.

## References

- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors
