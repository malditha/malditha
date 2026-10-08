# Mock API Fixture Builder

Day 039 of the 100 Days of Code challenge.

## Purpose

Mock API Fixture Builder creates small, repeatable JSON datasets for interface work, demos and automated tests without copying production records. A bounded JSON blueprint declares the record count and one rule per field.

Supported field rules are integer sequences, numbered strings, alternating booleans, cycling string enums and null values. The same blueprint always produces the same fixtures, and the tool makes no network requests.

## Run

Use Python 3.10 or newer. No third-party packages are required.

\`\`\`bash
python mock_api_fixture_builder.py example-blueprint.json
python mock_api_fixture_builder.py example-blueprint.json --jsonl
\`\`\`

Run the tests:

\`\`\`bash
python -m unittest -v
\`\`\`

## Blueprint

\`\`\`json
{
  "count": 3,
  "fields": {
    "id": { "type": "integer", "start": 100, "step": 1 },
    "name": { "type": "string", "prefix": "user-", "pad": 3 },
    "active": { "type": "boolean", "start": true },
    "status": { "type": "enum", "values": ["new", "ready"] },
    "note": { "type": "null" }
  }
}
\`\`\`

The builder accepts 1–1,000 records and 1–50 fields. Unknown blueprint keys, unsupported rules and oversized inputs are rejected.

## Skills practiced

- Declarative JSON configuration
- Deterministic synthetic-data generation
- Defensive validation and bounded processing
- JSON array and JSON Lines serialization
- Standard-library CLI and integration testing

## Next improvement

Add opt-in nested-object rules while preserving the same strict field, depth and output-size boundaries.
