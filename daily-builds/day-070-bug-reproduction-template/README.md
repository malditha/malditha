# Bug Reproduction Template

Turn structured observations into a complete Markdown bug report. This local CLI requires environment details, preconditions, ordered steps, expected and actual results, and a measured observation count so a handoff is less likely to omit essential context.

## Run and test

Python 3.10+; no dependencies.

```sh
python3 repro.py sample.json
python3 -m unittest -v
```

Redirect stdout to save Markdown. Exit 0 means success; exit 2 means invalid input. The sample describes a fictional application and synthetic account.

## Schema and limits

Use exactly the fields in the sample. Environment is an object with 1–10 short text entries. Preconditions and steps each need 1–20 single-line entries. Title allows 120 characters; environment keys 60 and values 300; list entries 500; expected and actual results 2,000 each. Frequency must use integers satisfying 1 <= observed <= attempted <= 10,000.

Input is bounded to 128 KB. Duplicate JSON keys, unknown fields, empty text, control characters and invalid counts are rejected. Environment keys sort consistently; steps retain input order. Markdown metacharacters are escaped.

The CLI does not execute the steps, confirm a root cause or redact secrets. Use synthetic data and review the full output before sharing.

## Skills practiced

Reproduction evidence modeling, defensive JSON validation, deterministic Markdown generation, escaping and standard-library tests.

## Next improvement

Add optional evidence references with validated URLs and an explicit sharing review step.
