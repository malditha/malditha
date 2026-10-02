# JSON Schema Starter

Day 033 of the 100 Days of Code challenge.

JSON Schema Starter generates a conservative Draft 2020-12 starting schema from one local JSON object. It solves one clear problem: turning an example API payload into a structured first draft that a developer can review instead of beginning from an empty schema.

The tool is dependency-free and offline. It limits input size, nesting, node count and object width. It never sends or logs the sample payload. One sample cannot prove every valid value, optional field, string format or business rule, so the result is deliberately called a **starter** schema and requires human review.

## Run

Requires Python 3.10 or newer.

    python3 json_schema_starter.py sample-event.json --title "Webhook event"

Write the result to a file:

    python3 json_schema_starter.py sample-event.json \
      --title "Webhook event" \
      --output webhook-event.schema.json

Objects reject unlisted properties by default. Use `--allow-additional` only when that matches the intended contract.

## Test

    python3 -m unittest -v

## Skills practiced

- Recursive JSON traversal
- Deterministic schema generation
- Draft 2020-12 vocabulary basics
- Bounded input validation
- Dependency-free Python CLI design
- Standard-library unit and subprocess tests

## Important limits

- Every property in the single sample is marked required; review which fields are actually optional.
- Strings are not guessed as dates, emails, UUIDs or other formats.
- Empty arrays produce an open `items` schema because the sample supplies no evidence.
- Mixed arrays use `anyOf`, which may be broader than the real API contract.
- The tool does not validate data against the generated schema.

## Next improvement

Accept several representative samples and infer which properties are consistently required while still showing conflicting shapes for human review.
