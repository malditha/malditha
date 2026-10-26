# Secret Placeholder Checker

Day 057 of the 100 Days of Code challenge.

## Purpose

Secret Placeholder Checker scans one bounded local JSON document for unresolved placeholder values before an automation is shared or deployed. Reports contain only JSON paths and generic rule codes.

It does not detect real secrets, measure credential strength, inspect n8n, call remote services or guarantee that a workflow is production-ready. Use sanitized input and review the result yourself.

## Run

Requires Python 3.10 or newer and no third-party packages.

\`\`\`bash
python secret_placeholder_checker.py sample.json
python secret_placeholder_checker.py sample.json --json
\`\`\`

Exit code \`0\` means no supported placeholders were found, \`1\` means review findings exist, and \`2\` means the input was invalid.

Run tests with \`python -m unittest -v test_secret_placeholder_checker.py\`.

## Boundaries

- Recognizes a small documented set such as \`CHANGE_ME\`, \`REPLACE_ME\` and \`YOUR_API_KEY_HERE\`
- Treats bracketed templates as findings only in credential-like fields
- Does not flag ordinary message templates such as \`{{customer_name}}\`
- Limits files to 100 KB, nesting to 20 levels and traversal to 10,000 values
- Rejects duplicate JSON keys and never echoes matched values

## Skills practiced

Recursive JSON traversal, conservative pattern matching, data-minimized reporting, defensive input limits, workflow exit codes and standard-library tests.

## Next improvement

Add an optional project policy file with an allowlist of approved template paths.
