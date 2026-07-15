# Client Regression Results

Date: 2026-07-15

Commands:

```text
cd client
npm test -- --run
npm run lint
npm run build
```

Results:

- Vitest: `18` files, `81` tests passed.
- ESLint: passed with no findings.
- TypeScript/Vite production build: passed; 39 modules transformed.
- Component coverage includes labeled resource fields, fieldsets, keyboard-operable native controls, contained/restored dialog focus, announced availability-deletion errors, owner- and request-bound availability responses including repeated resource selection, Course-bound eligibility loads and saves, preservation of currently assigned invalid resources during session editing, active-only Course resource choices, Course-specific availability/session usage, and blocker-accurate retirement outcomes.
