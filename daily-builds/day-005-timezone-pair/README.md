# Day 005 — Timezone Pair

Timezone Pair converts a proposed meeting time between two IANA time zones and shows a 24-hour pairing view with shared 9:00–17:00 working hours highlighted.

## Purpose

Remote teams should not have to memorize UTC offsets or manually adjust for daylight-saving changes. This browser tool uses \`Intl.DateTimeFormat\` data to translate the selected wall-clock time, identify date shifts, and reject local times that do not exist during a daylight-saving jump.

## Run

\`\`\`bash
npm start
\`\`\`

Open [http://localhost:4173](http://localhost:4173).

## Test

\`\`\`bash
npm test
\`\`\`

Tests cover IANA-zone validation, Manila-to-Toronto conversion, a daylight-saving gap, work-hour labels, and the 24-hour pairing model.

## Skills practiced

- IANA time zones with \`Intl.DateTimeFormat\`
- Wall-clock-to-UTC conversion and daylight-saving validation
- ES modules and deterministic Node tests
- Accessible forms, live results, and responsive layout

## Next improvement

Allow users to search the full browser-supported time-zone list and save named teammate pairs locally.
