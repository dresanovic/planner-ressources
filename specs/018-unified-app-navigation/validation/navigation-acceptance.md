# Navigation acceptance

Date: 2026-07-16

## Completed checks

- Automated browser: Codex in-app browser against Vite 8.1.3 dev server.
- 1280×800: persistent 220px sidebar, main content starts at x=220, header at x=244, no overlap, no horizontal overflow, one primary navigation, and zero hash links.
- 820×800: modal panel semantics (`role="dialog"`, `aria-modal="true"`, named by `navigation-title`), 290px panel, inert/hidden background, initial close focus, Escape restoration, no overflow.
- 320×720: all eight destinations visible in the scroll-safe panel, 290px panel width, no overflow; closed Schedule header and metadata reflow inside 296px.
- All eight destinations were activated in sequence and exposed the expected sole current leaf and visible Schedule/Academic Data heading.
- Console inspection found no warnings or errors from the navigation implementation.
- Focus contrast measured 5.49:1 or better in every navigation state.

Screenshots:

- `screenshots/wide-schedule.png`
- `screenshots/wide-academic-semesters.png`
- `screenshots/820-menu-open.png`
- `screenshots/320-menu-open.png`
- `screenshots/320-schedule.png`

## Remaining manual acceptance

- 200% text zoom could not be reliably applied through the available in-app browser viewport controls; the 320px reflow check passed, but the explicit 200% zoom observation remains pending.
- Firefox is installed, but NVDA is not installed on this workstation. NVDA/Firefox announcements for primary-navigation purpose, Academic Data expansion, and the sole current destination remain pending in an environment with NVDA.

