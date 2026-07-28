# US5 Exams Evidence

**Date**: 2026-07-27  
**Result**: PASS

- Course selectability is derived only from authoritative `generationEligibility.eligible`.
- Eligible courses render first; unavailable courses remain visible with the exact returned reason.
- Selected count, empty-selection guidance, constraints, and preparation actions remain outside the scrolling course list.
- A refresh that makes a selected course unavailable prunes it and announces the change.
- Requirement editing preserves active-exam read-only behavior, recommendation/override validation, responsible lecturer, payload, and Cancel reset.
- Manual placement and generation continue to use existing API handlers, confirmations, snapshot tokens, partial-result, and stale behavior.
- Lifecycle/Exam focused suite: 3 files, 8 tests passed in 1.93s.
- Page/List/exam-editor suite: 3 files, 68 tests passed in 4.36s.
- Live Chromium confirmed the focused Exams composition and Eligible/Unavailable group semantics.
