# Day 001 — Commit Craft ✦

A tiny, dependency-free conventional commit message generator with validation and a soft cyber interface.

## Why this project

Good commit messages make code review and release history easier to understand. Commit Craft turns a few structured fields into a consistent conventional commit without sending project information to a server.

## Features

- Conventional commit types and optional scope
- Breaking-change support
- Optional body and issue reference
- Header-length validation
- One-click clipboard copy
- Responsive, accessible browser interface
- Unit tests using Node's built-in test runner
- No dependencies and no data collection

## Run locally

Open `index.html` directly in a browser, or serve the folder with any static server.

To run the tests:

    npm test

Node.js 20 or newer is recommended.

## Skills practiced

- Separating domain logic from DOM code
- Browser Clipboard API with a fallback
- Accessible form feedback
- Node's built-in test runner
- Responsive CSS and visual hierarchy

## Next improvement

Add reusable presets and URL-based sharing without storing commit content remotely.
