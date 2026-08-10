# US2 European-date verification

Date: 10.08.2026

## Boundary behavior

- Human display and entry use zero-padded `DD.MM.YYYY`.
- The shared parser returns the original ISO calendar day or `null`; no
  date-only `Date` construction is used.
- Leap-year, century, year-boundary, open-range, Vienna DST and
  institution-local-today cases pass in `datePresentation.test.ts`.
- The controlled text field provides persistent `TT.MM.JJJJ` guidance, strict
  impossible/incomplete-date handling, min/max checks, stable description IDs,
  and ISO/null callbacks.
- Native browser `type="date"` controls are absent from production TSX.

## Surface and machine-boundary evidence

Calendar, schedule, exam, deletion, lifecycle, academic, holiday, availability,
batch and lecturer surfaces ran in the complete client suite: 51 files and 352
tests passed. API request/snapshot tests remain green and continue to assert ISO
payloads. Backend API regressions remain green in the complete 481-test suite;
database/API date contracts were not changed.

Cross-browser pointer/keyboard behavior, NVDA, 320px and 200% zoom remain open
under T053 and are not claimed here.
