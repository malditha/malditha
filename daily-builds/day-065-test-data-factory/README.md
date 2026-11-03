# Day 065 — Test Data Factory

A dependency-free Python CLI that generates repeatable synthetic JSON records from a bounded local schema. It supports integers, booleans, declared choices, labeled random strings and reserved `.test` email addresses without using real people or production data.

## Run

```bash
python test_data_factory.py schema.json --count 5 --seed 42
python test_data_factory.py schema.json --count 5 --seed 42 --format ndjson
python -m unittest -v
```

The same schema, count and seed always produce the same records. Invalid input returns exit code `2`.

## Skills practiced

- Seeded deterministic data generation
- Small declarative schema design
- Privacy-safe synthetic identifiers
- Defensive JSON validation and output bounds
- Standard-library unit testing

## Next improvement

Add optional uniqueness constraints with deterministic retry limits for fields that must not repeat within one generated batch.
