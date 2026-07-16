# US1 — Single hierarchy

- Focused command: `npm test -- src/components/ApplicationNavigation.test.tsx src/App.test.tsx src/pages/AcademicDataPage.test.tsx src/pages/CourseSchedulePage.test.tsx --run`
- Result: PASS — 4 files, 36 tests.
- Assertions cover one `Primary navigation` landmark, Schedule plus the seven ordered Academic Data leaves, controlled category content, mounted Schedule/catalog refresh, and absence of Dashboard, hash links, page-local navigation, and the fixed switcher.
- Browser exercise at 1280px reached all eight leaves and returned the expected sole `aria-current="page"` and visible destination heading for each.

