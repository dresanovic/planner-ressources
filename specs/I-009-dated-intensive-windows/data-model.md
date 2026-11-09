# I-009 Data Model

## Existing window record

Extend `study_type_time_windows`; retain current primary key and all incoming references. These are normative field constraints (quoted in implementation tasks):

- **D1**: `id` remains the existing primary key; edits and migration preserve identity.
- **D2**: `study_type_id` is exactly one required existing active form on create/edit/reactivate.
- **D3**: `kind` is required, either `weekly` or `dated`, and immutable on edit/copy.
- **D4**: `weekday` is an integer 0–6 for weekly and null for dated.
- **D5**: `date` is a full valid calendar date including year for dated and null for weekly.
- **D6**: `start_time` and `end_time` are required same-day times; end_time is later than start_time; midnight spanning is rejected.
- **D7**: `is_intensive` is Boolean, false for weekly, defaults false for new dated records and is editable only for dated records.
- **D8**: `sort_order` retains its existing integer value on migration/copy.
- **D9**: `is_active` retains existing Boolean lifecycle behavior; inactive entries participate in duplicate identity.
- **D10**: `revision` is a positive optimistic integer; mutation requires matching expectedRevision and increments revision.

Database checks enforce discriminated shape/time order and FK ownership. Partial unique indexes enforce weekly `(study_type_id,weekday,start_time,end_time)` or dated `(study_type_id,date,start_time,end_time)` identity, independent of marker/activity. Different forms/kinds and partial overlaps are allowed; races translate into recoverable conflicts. Archiving an owner makes its windows unavailable without rewriting records.

Migration backfills weekly/false, preserves remaining values and all FK/historical facts, and makes predecessor/fresh schemas equivalent. State transitions: unsaved → explicit create → active record → edit/archive/reactivate/confirmed permitted delete. Kind cannot change. Existing usage/reference rules can block deletion with counts/prerequisites; no cascade to peers or sessions.

## Unsaved copy

Client-only captured kind/form/weekday-or-date/hours/marker/sortOrder; no saved source link, source ID or source expectedRevision. Changes to source never synchronize. Cancel/dismiss writes nothing; explicit successful POST creates one independent record. Disable repeated in-flight submission and revalidate current form/duplicates. Copy ancestry never blocks later edit/deletion.

## Detached opportunity and scoring facts

Extend TimeWindowPlan/serializers/snapshots with discriminator/date/marker. Retain source identity/index for provenance only. Applicability is exact date or weekly weekday for same active form/record, bounded by course period, with narrower explicit restrictions additionally binding. Whole session including breaks fits one record; no stitching/capacity multiplication.

Actual 45-minute instructional intervals separated by ten-minute breaks intersect the marked union once. Intensive LE is the exact rational of integer microseconds divided by 2,700,000,000; no float/rounding in optimization. Total/intensive count selected teaching only. Extend detached fixed teaching with units/form/marked context; no ORM crosses worker boundary. Fixed exams have no scoring contribution.

Per cohort/date/LV positive marked instruction creates one presence, including qualifying fixed teaching; K distinct LVs yields max(0,K−1). No cross-cohort/window duplication, weights or stored cumulative score. Facts are derived for the actual current/generated arrangement and prepared scope, not attached to source window ownership.

## Current/prepared context

Fingerprint kind/date/weekday/hours/form/activity/marker/revision plus inherited constraints/resources/fixed teaching/exams/lifecycle. Include fixed teaching's own marker context. Relevant changes stale prepared/provisional results; marker-only changes never create validity violations. Current validation is loading/current/unavailable for a catalog revision; prior-revision responses cannot become current. History/publication uses immutable captured evidence.
