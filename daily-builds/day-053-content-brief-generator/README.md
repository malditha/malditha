# Content Brief Generator

Day 053 of the 100 Days of Code challenge.

## Purpose

Content Brief Generator converts one small local JSON request into a consistent editorial brief for an article, email, Facebook post, LinkedIn post, Reel or website page. It keeps the goal, audience, problem, takeaway, evidence, requirements and review checks in one deterministic document.

It does not write the final content, contact an AI service, research facts, invent evidence or publish anything. Supplied evidence and claims still require human verification.

## Run

Requires Python 3.10 or newer and no third-party packages.

```bash
python brief_generator.py request.json
python brief_generator.py request.json --json
```

The default output is Markdown. `--json` produces structured data for a later workflow node. Exit code `0` means the brief was created; `2` means the request was invalid.

Run the tests:

```bash
python -m unittest -v test_brief_generator.py
```

## Input boundaries

- Requires a title, supported goal, audience, supported channel, problem and single takeaway
- Accepts optional evidence, must-include, avoid, call-to-action and tone fields
- Limits text to 500 characters, lists to 12 unique items and files to 100 KB
- Rejects duplicate JSON keys and undeclared fields
- Adds editorial checks for evidence, privacy and final human review

This tool structures only the information supplied to it. A well-formatted brief can still contain weak or inaccurate source material.

## Skills practiced

- Defensive JSON parsing
- Declarative input validation
- Deterministic document generation
- Markdown and structured JSON output
- Workflow-friendly exit codes
- Standard-library testing with `unittest`

## Next improvement

Add optional channel profiles that suggest length and section constraints without generating claims or final copy.
