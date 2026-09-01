# JSON Lens — Day 002

A local-first browser tool for turning dense JSON into a readable, searchable path explorer. It validates input, reports the error location, formats or minifies valid JSON, summarizes leaf types, and exposes values using familiar paths such as `$.users[0].name`.

## Run

From this directory, start any static server:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000`. The app has no runtime dependencies and does not upload input.

## Test

```bash
npm test
```

Tests use Node's built-in test runner, so no install step is required.

## Skills practiced

- Recursive traversal of nested objects and arrays
- Friendly parser errors with line and column hints
- Pure JavaScript modules separated from DOM behavior
- Search filtering, accessible status feedback, and responsive UI
- Automated tests with `node:test`

## Next improvement

Add collapsible tree navigation and shareable URL-safe samples while keeping private input local.
