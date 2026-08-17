# FS-020 Full Regression Evidence

Date: 2026-08-14.

- Backend: **515 passed, 1 skipped** in 409.60 seconds.
- Client: **412 passed across 55 files** in 15.26 seconds.
- Client lint: passed.
- Client production build: passed.
- Python dependency check: passed.
- Independent iCal4j validation: 12/12 fixtures reported `No errors.`

The skipped backend case is the explicitly environment-gated FS-020 release-container performance protocol. It was not silently converted into a local timing test.

Unresolved release evidence:

1. Representative manual Outlook imports (T029 / TR-008 / SC-004 and part of SC-005).
2. Constrained 2-vCPU/2-GiB release-container performance protocol (SC-007).
3. Windows browser, keyboard, NVDA, 200% zoom, 320 CSS-pixel, and ten-participant usability acceptance (T041 / SC-008 / SC-009 / SC-012).

These gaps prevent a claim of release acceptance, but they do not represent an automated regression failure.
