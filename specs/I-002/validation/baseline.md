# FS-022 implementation baseline

Recorded on 10.08.2026 before production changes.

## Isolation and preserved state

- Implementation branch: `codex/I-002-consistent-presentation`
- The branch was created from `master` without resetting the working tree.
- Pre-existing changes preserved: `.specify/feature.json`, `docs/planning/Feature_slices.md`, the untracked `specs/I-002/` initiative artifacts, and deletions under the existing `backend/.pytest_tmp_fs015_full*` directories.
- Existing inaccessible pytest work directories reported by Git were not modified.

## Runtime versions

- Python 3.12.8
- Node v26.7.0
- npm 11.13.0

## Baseline commands

| Command | Working directory | Result |
|---|---|---|
| `python -m pytest backend/tests -q` | repository root | PASS: 468 tests, 1163 warnings, 95.45 s |
| `npm run test -- --reporter=dot` | `client/` | PASS: 46 files, 327 tests |
| `npm run lint` | `client/` | PASS |
| `npm run build` | `client/` | PASS |

The first client test attempt inside the restricted Windows sandbox failed before test discovery with `spawn EPERM` while Vite loaded its configuration. Re-running the same project command with its approved process-spawn permission passed. This is an execution-environment limitation, not an application failure.

After pytest reported success and exit code 0, the Windows process emitted an existing fatal `0xc0000139` diagnostic while importing `pyarrow` through pandas/OR-Tools. The successful test result and this post-run environment diagnostic are both retained for later comparison.

Existing React tests also emit several `act(...)` warnings while passing. FS-022 must not introduce new failures; these baseline warnings are not attributed to the slice.
