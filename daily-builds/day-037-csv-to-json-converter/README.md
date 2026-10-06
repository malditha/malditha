# CSV-to-JSON Converter

A dependency-free Python CLI that turns UTF-8 CSV data into a JSON array or JSON Lines. It validates the tabular shape and preserves every field as text, so identifiers such as `00123` are not silently changed.

## Run

Convert a file to a JSON array:

```bash
python csv_to_json_converter.py people.csv
```

Read from standard input and emit JSON Lines:

```bash
printf 'name,code\nAna,00123\n' | python csv_to_json_converter.py --json-lines
```

Use `--max-rows` and `--max-columns` to set explicit processing bounds.

## Test

```bash
python -m unittest -v
```

## Behavior

- handles standard quoted CSV fields, commas and line breaks
- trims header names and rejects blank or duplicate headers
- rejects rows whose field count does not match the header
- supports UTF-8 input with or without a byte-order mark
- outputs a JSON array by default or one object per line
- preserves all field values as strings instead of guessing types

## Skills practiced

- Python standard-library CSV parsing
- defensive, bounded input validation
- deterministic JSON and JSON Lines serialization
- command-line file and standard-input handling
- test-first development

## Next improvement

Add an explicit schema file for opt-in, validated type conversion without relying on guesses.
