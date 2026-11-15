# Day 074 — Secret Leak Pattern Scanner

A small offline pre-sharing review aid for one text file. It flags explicit credential assignments and private-key opening markers while keeping values and file paths out of the report. Python 3.10+, standard library only.

## Run

```sh
python scanner.py sample.txt
python -m unittest -v
```

The synthetic sample intentionally exits **1** with one finding. Exit 0 means no supported patterns matched; exit 2 means unreadable, oversized or invalid text. Input is UTF-8, at most 64 KiB, with no NUL bytes. Output is JSON containing only line numbers, fixed rule names, count and scope. No network requests, credential validation or file changes occur.

## Exact scope

Matches line-start assignments (optional `export`) to `api_key`, `access_token`, `client_secret` or `password`, case-insensitively, with `:` or `=` and a nonempty value. Also matches standalone BEGIN PRIVATE KEY markers, optionally RSA, EC, OPENSSH or ENCRYPTED. Comment lines, arbitrary variable names, embedded JSON keys, other token formats and Git history are outside this narrow detector. Placeholder values are intentionally flagged: the scanner cannot establish whether a value is live.

Treat each finding as a prompt for local review, not proof of a leak. A clean result is not proof that a file contains no secrets. Do not paste matched values into tickets or public reports. If review confirms a real exposed credential, use its provider's revocation/rotation process and investigate the exposure separately. This tool does not perform remediation.

Only explicitly supplied files are read; there is no directory traversal. The report omits filenames and excerpts, but line numbers still describe the input's structure. Do not publish the input file or a real credential as a test fixture.

## Skills practiced

Bounded text parsing, conservative pattern matching, data-minimized reporting, CLI exit codes and Python unit tests.

## Next improvement

Add configurable rule identifiers with tests for false positives, while keeping values out of diagnostics.
