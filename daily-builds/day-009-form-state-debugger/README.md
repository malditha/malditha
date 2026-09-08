# Day 009 — Form State Debugger

A dependency-free browser tool for seeing how form fields move through pristine, touched, dirty, valid and invalid states.

## Purpose

Form bugs are difficult to reason about when values, validation and interaction history are hidden inside event handlers. Form State Debugger turns a small profile form into a visible state timeline. It shows each field's current value, touched and dirty flags, validation result and the latest browser event without sending data anywhere.

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

- Immutable form-state transitions
- Input, blur, reset and submit events
- Field-level and whole-form validation
- Accessible live status updates
- Safe DOM rendering without dependencies
- Node's built-in test runner

## Next improvement

Add an exportable event trace that can reproduce a reported form-state bug without capturing sensitive field values.
