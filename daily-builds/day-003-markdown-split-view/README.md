# Day 003 — Markdown Split View

A private, dependency-free Markdown editor that turns README drafts and notes into a safe live preview without sending the content to a server.

## Purpose

Writing Markdown from memory is fast, but switching between an editor and rendered output makes small formatting mistakes easy to miss. This tool keeps source and preview together, adds writing statistics, and lets the rendered HTML be copied when needed.

## Run

1. Start a local static server in this folder, for example `python3 -m http.server 8000`.
2. Open `http://localhost:8000`.
3. Write Markdown in the left panel and inspect the preview on the right.

Run the logic tests with:

```bash
npm test
```

## Features

- Live split Markdown and HTML preview
- Headings, lists, links, images, quotes, emphasis, inline code and fenced code
- Escaped raw HTML and blocked unsafe link protocols
- Word, character and estimated reading-time statistics
- Copy rendered HTML
- Local draft persistence and responsive keyboard-friendly UI

## Skills practiced

- JavaScript text parsing and module boundaries
- Safe HTML escaping and URL allow-listing
- DOM events, Clipboard API and local storage
- Responsive layout and accessible form labels
- Node's built-in test runner

## Next improvement

Add table and task-list support with an opt-in synchronized scroll position between the editor and preview.
