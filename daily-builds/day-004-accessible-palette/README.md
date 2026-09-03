# Accessible Palette

Day 004 of Kris Lacanlale's 100 Days of Code.

## Purpose

Accessible Palette removes guesswork from choosing readable interface colors. Enter foreground and background hex colors to see the contrast ratio, AA/AAA results for text, a UI-component check, a live preview and a suggested foreground when normal text fails AA.

All calculations run locally in the browser. No color choices or other data leave the page.

## Run

Requires Node.js 18 or newer.

```bash
npm start
```

Open the local URL printed in the terminal. The project has no runtime dependencies, so `python3 -m http.server` is also sufficient.

## Test

```bash
npm test
```

## Skills practiced

- ES modules and small pure functions
- sRGB relative-luminance and contrast calculations
- Input validation and synchronized form controls
- Accessible labels, live feedback and responsive layout
- Node's built-in test runner

## Next improvement

Add shareable URLs that encode a color pair and a multi-color palette audit that identifies every failing combination.
