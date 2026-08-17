# FS-020 Release Checklist

Status: **implementation complete; release acceptance pending external/manual gates**.

| Requirement group | Evidence | Status |
|---|---|---|
| FR-001–FR-017 complete scoped download and notice | focused backend/client suites; privacy audit | Pass |
| FR-018–FR-036 calendar identity, content, ordering, time zone, determinism | serializer/API suites; retained manifest; determinism evidence | Pass |
| FR-037 representative Outlook import | `outlook-import.md` | Pending |
| FR-038 independent validation | `rfc5545-validation.md`, 12/12 no errors | Pass |
| FR-039 manual file-only exchange | route/import audit; no provider integration | Pass |
| TR-001–TR-006 test-first matrix and corpus | baseline, fixture source manifest, automated suites | Pass |
| TR-007 independent validator | pinned iCal4j evidence | Pass |
| TR-008 manual Outlook import | `outlook-import.md` | Pending |
| TR-009–TR-010 privacy and non-mutation | `privacy-scope-audit.md`, lifecycle/concurrency tests | Pass |
| TR-011 accessibility interaction | automated interaction coverage plus manual matrix | Partial; manual pending |
| TR-012 excluded integrations | static audit and route tests | Pass |
| SC-001–SC-003 scope/lifecycle/conformance | automated suites and iCal4j | Pass |
| SC-004 representative Outlook import | manual matrix | Pending |
| SC-005 DST/cross-midnight/device-zone correctness | automated fixtures pass; Outlook/device observation pending | Partial |
| SC-006 deterministic three-run output | `determinism.md` | Pass |
| SC-007 constrained release performance | gated test exists; designated environment absent | Pending |
| SC-008–SC-009 ten-participant comprehension/usability | `accessibility-usability.md` | Pending |
| SC-010–SC-011 privacy/non-mutation | privacy audit and automated tests | Pass |
| SC-012 manual browser/AT/responsive acceptance | automated mechanics pass; manual matrix pending | Partial |

## User-story checkpoints

- US1 complete download: automated pass.
- US2 recognizable standards/Outlook: RFC validation pass; manual Outlook gate pending.
- US3 privacy boundary: automated pass; manual accessibility/usability gate pending.
- US4 deterministic snapshot: automated and retained-evidence pass.

## Release decision

Do not declare FS-020 release-accepted until T029, T041, and the SC-007 constrained performance protocol are completed and their evidence is appended. All implementation, automated regression, deterministic corpus, privacy audit, and independent RFC validation gates are complete.
