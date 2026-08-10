# US1 actionable-problem verification

Date: 10.08.2026

## Automated evidence

- `client/src/utils/userProblems.test.ts`: safe validation, stale, permission,
  connectivity, ambiguous mutation and unknown-failure mappings; unsafe input is
  not rendered.
- `client/src/components/ActionableProblemList.test.tsx`: separate problem
  items, blocking alert semantics, polite warning semantics, field description
  IDs and safe caller-owned actions.
- Schedule, calendar, exam, academic, resource, holiday and lecturer regression
  tests ran as part of the complete Vitest suite: 51 files, 352 tests passed.
- Backend lecturer projection tests ran as part of the complete pytest suite:
  481 tests passed. The public response shape is unchanged and public finding
  messages use allowlisted course/session facts.

The motivating outside-window case asserts the affected course, scheduled
date, recommended range, non-blocking saved state, edit guidance and intentional
retention guidance. Raw validity codes are not the primary explanation.

## Residual manual evidence

Keyboard, screen-reader, zoom/320px and representative-user comprehension
checks remain open as T053 and T054. No manual result is inferred from the
automated suite.
