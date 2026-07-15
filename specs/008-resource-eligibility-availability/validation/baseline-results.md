# FS-008 Baseline Results

- Branch: `codex/fs-008-resource-eligibility`
- Baseline commit: `a2dd7d68f5fb69dfbea8bdabad02ca777d723c34`
- Date: 2026-07-15

## Backend

Command: `python -m pytest` from `backend/`

Result: PASS — 103 tests passed in 6.39 seconds. The existing suite emitted 308 SQLAlchemy `datetime.utcnow()` deprecation warnings.

## Client

- `npm test`: PASS — 13 files and 54 tests passed in 3.98 seconds.
- `npm run lint`: PASS.
- `npm run build`: PASS — TypeScript and Vite production build completed successfully.

No FS-008 production changes were present during this baseline.
