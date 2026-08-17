# FS-020 Representative Outlook Import Evidence

Status: **not executed in this implementation environment**.

The retained fixture corpus is ready for the institution-designated Windows/Outlook acceptance run. Automated RFC validation is recorded separately, but it does not substitute for this manual gate.

Record before acceptance:

- Outlook product/edition and exact build
- Windows version
- Account type
- Manual import/open path
- Tester and date

For every `.ics` fixture in `validation/fixtures/`, record repair prompt, imported count, summary, local start/end, duration, time zone, Busy state, location, and description. Record repeated-import behavior observationally without making it a product guarantee.
