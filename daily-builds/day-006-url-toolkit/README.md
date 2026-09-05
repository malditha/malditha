# Day 006 — URL Toolkit

URL Toolkit normalizes a pasted web address, reveals its components and query parameters, and produces a cleaner URL using optional transformations.

## Purpose

Long links can hide tracking parameters, duplicate values, fragments and important routing details. This small browser utility makes those parts visible and lets a user remove common campaign identifiers, sort query parameters or strip the fragment before copying the result.

All parsing happens locally. The entered URL is never requested or uploaded.

## Run

Requires Node.js 18 or newer.

```bash
npm start
```

Open `http://localhost:4173`.

## Test

```bash
npm test
```

## Skills practiced

- The standard `URL` and `URLSearchParams` APIs
- Pure parsing and transformation functions
- Duplicate query-parameter handling
- Safe DOM rendering and clipboard interaction
- Responsive, accessible form design
- Node's built-in test runner

## Next improvement

Add an editable parameter table that can rebuild a URL while preserving repeated keys and their order.
