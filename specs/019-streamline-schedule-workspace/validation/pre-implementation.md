# FS-019 Pre-Implementation Evidence

**Date**: 2026-07-27

## Isolation

- Implementation branch: `codex/019-streamline-schedule-workspace`
- Repository: `C:\Codex\planner-resource`
- Production source files were clean before implementation.
- Existing dirty files were classified as FS-019 planning/baseline metadata:
  - `.specify/feature.json`
  - `docs/planning/Feature_slices.md`
  - `specs/019-streamline-schedule-workspace/`
- No existing change was discarded, reset, or overwritten.

## Toolchain

- Node.js: `v26.4.0`
- npm: `11.13.0`
- Python: `3.12.8`
- Resolved Vitest: `4.1.10`

## Ignore Configuration

- Root `.gitignore` covers Node, TypeScript build output, Python caches and virtual environments, coverage, environment files, logs, databases, operating-system files, and temporary files.
- `client/eslint.config.js` ignores `node_modules`, `dist`, `build`, `coverage`, and minified JavaScript.
- No Docker, Prettier, Terraform, Helm, or publishable npm package configuration requires another ignore file.

## Focused Baseline

Command run from `client/`:

```text
npm test -- src/components/CalendarPlanningWorkspace.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/ApplicationNavigation.test.tsx src/App.test.tsx
```

Result:

```text
Test Files  4 passed (4)
Tests       69 passed (69)
Duration    4.80s
```

The first sandboxed attempt could not spawn Vite's build helper (`spawn EPERM`). The identical command passed when rerun with the required process permission; this was an environment restriction, not a product failure.
