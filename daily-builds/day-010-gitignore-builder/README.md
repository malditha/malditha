# Day 010 — Gitignore Builder

A dependency-free browser utility for assembling a clean, deduplicated `.gitignore` from practical stack, editor, operating-system and sensitive-file rules.

## Purpose

Starting a repository often means copying ignore rules from several places, which can create duplicates or omit local secrets. Gitignore Builder provides small reviewed rule groups, useful presets, custom one-line patterns and a live export without uploading project filenames.

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

- Data-driven interface generation
- Rule normalization and stable deduplication
- Git ignore negation ordering
- Local file generation and download
- Responsive and accessible form controls
- Node's built-in test runner

## Next improvement

Add a file-list simulator that explains which sample paths each generated rule would ignore without reading a real repository.
