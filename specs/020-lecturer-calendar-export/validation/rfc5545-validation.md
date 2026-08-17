# FS-020 Independent RFC 5545 Validation

- Validation date: 2026-08-14
- Validator: `iCal4j Command 0.1.1-develop-SNAPSHOT (ical4j=4.0.0-rc6, jvm=21.0.12)`
- Artifact SHA-256: `45aee44d1bea6146b43eeb7c88411a430808d58d9a4731b98078206912a7e469`
- Command: `ical4j calendar validator -file=<absolute fixture path>`
- Result: all 12 retained fixtures exited `0` and reported `No errors.`

The CLI also emitted its known `TimeZoneRegistryImpl` alias-resource warning for each invocation. This was a tool-runtime warning, not a calendar validation error.

| Fixture | SHA-256 | Result |
|---|---|---|
| `cross-midnight.ics` | `bf69e8a269960050d983595a5a6ca6c95bd0101181b6146aa1910c03db734e19` | No errors |
| `dst.ics` | `c0cdb3b458560910e1fb96f74a7dba292e33304cd914ba11fbd80e6c420755f2` | No errors |
| `embedded-newline.ics` | `fb85057fe16d3ff6959098b87ee1474683fdb832cd892269710c6c800b68d64c` | No errors |
| `empty.ics` | `1e67c1dc9b36a1610272b1fbeeca17b8e5aec144faa3be8a41659dcefe9ef182` | No errors |
| `exam-only.ics` | `e7d55332271acae5f1a26395c5bbd9f419865a500ce0a76d706e4d7b38ed314c` | No errors |
| `identical-display.ics` | `eb24092f839826e9754f0c78f8c447ae2022866dc644924063ac6c2d5f0c444c` | No errors |
| `long-line.ics` | `e03b9472553cca1a1fd53ebf5024c3eaeeee901d0dcc7fe6e1aab56109bda1f0` | No errors |
| `missing-location.ics` | `1473a600e3d6557aab756b41f99a6ac366ec50e4459cea4ccf4922b27e213eb5` | No errors |
| `mixed-multi-course.ics` | `f155ee265891de87183080839216443f6f5adeae304e7bf395019eceb5f503a3` | No errors |
| `one-hundred-events.ics` | `7cd5e8eb17e1a0d7e6f9ac62657231d6904bd383899e856280e1a6afe5310763` | No errors |
| `teaching-only.ics` | `a88afeb5d0b280d83c434a15bed9de7aa557c12ea9c19c3095f878ac3cea4e67` | No errors |
| `unicode-reserved.ics` | `4ebeae1a9a7886e7b53336c11d81179f487aa6d1b4b32b321e05f84f0db24ecf` | No errors |

The exact source and expected event fields are retained in `fixtures/manifest.json`; serializer inputs are `icalendar==7.2.2` and `tzdata==2026.3`.
