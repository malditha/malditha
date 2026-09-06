# Day 007 — Regex Playground

A dependency-free browser tool for testing JavaScript regular expressions before using them in application code.

## Purpose

Regular expressions are compact but difficult to inspect. This playground highlights every match, shows its character range and capture groups, and previews JavaScript replacement syntax without sending the test text anywhere.

## Run

```bash
npm start
```

Open <http://localhost:4173>. No installation or build step is required.

## Test

```bash
npm test
npm run check
```

## Skills practiced

- JavaScript `RegExp` construction and flags
- Global matching, capture groups and zero-length match safety
- Replacement syntax and text segmentation
- Accessible, responsive DOM rendering
- Node's built-in test runner

## Next improvement

Add a small regex reference panel that explains tokens detected in the current pattern without attempting to replace a full parser.
