# FS-020 Determinism Evidence

- Date: 2026-08-14
- Serializer: `icalendar==7.2.2`
- Time-zone data: `tzdata==2026.3`
- Retained corpus files: 12 `.ics` files plus `manifest.json`
- Three-run aggregate SHA-256: `6efb97eb24cae29b8ebd45ef22dc67bce0095c14915671dfd7f22fda4163397b` on every run

The generator was run three times from identical inputs. After each run, every retained file was sorted by filename, hashed with SHA-256, and the complete name/hash list was hashed again. All aggregate digests were identical.

Automated service tests additionally prove:

- source retrieval order cannot change membership or serialized event order;
- event ordering is UTC start, UTC end, then ordinal UID;
- display-field edits change calendar bytes but preserve the session UID within the same revision;
- adding and removing sessions changes the snapshot;
- identical-looking sessions have distinct UIDs;
- the same session identity in another revision has a distinct UID;
- `DTSTAMP` is the immutable revision creation time, not download time;
- repeat API requests return identical bytes, filenames, and safe dispositions.

The retained per-file checksums remain in `fixtures/manifest.json` and `rfc5545-validation.md`.
