# Day 008 — CSV Quicklook

A dependency-free browser tool for checking a CSV file before importing it into another system.

## Purpose

CSV files often hide uneven rows, missing values and unexpected duplicates until an import fails. CSV Quicklook parses a local file, previews its first 20 rows, flags structural inconsistencies and summarizes filled, empty and unique values per column. Data never leaves the browser.

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

- Character-by-character CSV parsing
- Quoted fields, escaped quotes and alternate delimiters
- Data-quality summaries and structural validation
- Local file handling with the browser `File` API
- Accessible responsive table rendering
- Node's built-in test runner

## Next improvement

Add opt-in type inference and downloadable validation reports while keeping all processing local.
