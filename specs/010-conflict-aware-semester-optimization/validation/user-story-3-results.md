# User Story 3 evidence

Date: 2026-07-17.

- A 4-unit current draft is replaced by a proven 8-unit result; its revision increments once.
- An equal complete current draft remains `unchanged` with the same revision and sessions.
- A 6-unit current draft against a current 4-unit course is retained whole; actual saved units are the baseline.
- Two equal-unit retained drafts sharing lecturer, room, and cohort are replaced before the preservation tier when a zero-conflict arrangement exists.
- The API returns `409 REPLACEMENT_CONFIRMATION_REQUIRED` before solving an affected draft.
- A post-solve material Course change produces one stale preserved course while one exact unaffected course saves. The solver wrapper was called exactly once, proving there was no silent re-solve.
- Custom constraints/source records and other semesters remain covered by the complete existing regression suite.

Focused replacement/stale tests passed.
