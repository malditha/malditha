# Changelog Composer

Compose a consistent Markdown release note from reviewed structured changes. This small local tool groups entries in a fixed order and makes breaking changes visible without inventing release claims.

## Run

Python 3.10+; no dependencies.

```sh
python3 composer.py sample.json
python3 -m unittest -v
```

Redirect stdout to save the Markdown. Exit 0 means success; exit 2 means invalid input.

## Input

Use exactly `version`, ISO calendar `date`, and `changes`. Each change needs a unique `id`, `category` (Added, Changed, Fixed, Removed or Security), `summary`, and boolean `breaking`. Version and IDs allow 60 characters; summaries allow 300. Input is bounded to 128 KB and 200 entries. Duplicate JSON keys, unknown fields, invalid dates and control characters are rejected. Markdown metacharacters are escaped.

Changes retain their input order within each category. Only populated categories appear. Review the facts and wording before publishing; this tool does not read Git history or verify that a change shipped.

## Skills practiced

Deterministic text generation, release communication, defensive JSON validation, Markdown escaping, calendar validation and standard-library tests.

## Next improvement

Add optional issue links with strict URL validation and a separate preview of those references.
