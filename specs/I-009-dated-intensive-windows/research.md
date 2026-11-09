# I-009 Planning Research

Date: 2026-11-06. Existing repository evidence, no proposed technology upgrades. Builder inspected storage/catalog/client; fresh-context read-only agent `/root/planning_research` inspected solver/worker/proof. This research is not the independent analysis assessment.

## Record shape

**Decision**: Extend StudyTypeTimeWindow in place, retaining IDs and FK references; discriminate weekly/dated and replace old uniqueness with kind-specific indexes.
**Rationale**: `models/planning.py:StudyTypeTimeWindow` requires weekday and form/weekday/hours uniqueness. `services/academic_catalog.py:usage_for` already protects constraint, selected-window, session and historical references. `db/schema.py` owns sequential upgrades. SQLite-safe migration must preserve all these relationships.
**Alternatives considered**: Separate dated table duplicates lifecycle/reference paths; sentinel weekdays obscure shape errors. Neither serves a present need.

## Shared permission and refresh

**Decision**: Extend normalized values and a shared exact-date applicability predicate; reuse App catalogRevision/current-context states.
**Rationale**: `draft_schedule_repository.py:load_time_windows`, `draft_schedule_validation.py:fits_any_validation_window`, planning-options serializers and `conflict_aware_generation.py:_windows_host_minimum_session` assume weekdays. Catalog course availability also needs usable occurrence/period handling. `AcademicDataPage.tsx` currently waits for list reload before notifying changes; acknowledgement must invalidate even if reload fails.
**Alternatives considered**: Virtual weekly records leak recurrence; extending just generation creates selection/validation disagreement; a global refresh service adds unnecessary machinery.

## Exact scoring and complete candidates

**Decision**: Keep CP-SAT/sequential objectives; insert intensive time and variety after total units. Reuse microsecond ticks; instructional intervals are 45 minutes with ten-minute breaks. Union marked intervals, then intersect instruction.
**Rationale**: `semester_optimization.py:_candidate_start_times` uses left-shift event closure for feasibility. Coefficients alone can miss an intensive optimum inside an ordinary window: marker/instruction boundary start seeds and positive-overlap representatives must participate in closure. `_time_ticks` already preserves microsecond boundaries. Existing exhaustive-oracle tests offer an independent validation pattern.
**Alternatives considered**: Float/rounded LE loses exact ties, weighted priorities allow forbidden tradeoffs, arbitrary minute grids alter precision and increase search. Legacy seeds/order must stay unchanged without markers.

## Fixed teaching

**Decision**: Extend detached fixed teaching with units/form/marked context, using unique presence per cohort/date/LV. Fixed teaching contributes variety, not selected coverage; active exams remain occupancy only.
**Rationale**: `semester_optimization.py:FixedSession` lacks units/form. `conflict_aware_generation.py:load_operation` must load facts for each fixed teaching session's own form, which may differ from selected forms. `optimization_worker.py:DetachedOptimizationInput` intentionally carries no ORM session.
**Alternatives considered**: Worker DB access breaks spawn boundary; elapsed duration credits breaks; date-wide presence pools unrelated cohorts.

## Existing objective/proof order and acceptance

**Decision**: Extend current key/direction/fingerprint/worker/result/UI paths together and preserve I-004/I-006 acceptance authority.
**Rationale**: Current order is total_units, conflicts, schedule_shape, lecturer_changes, room_changes, retained_drafts, canonical_temporal, canonical_resource. Insert both max objectives after total_units. Existing direction whitelist in `_decision_required_result` recognizes only total_units/retained_drafts as maxima. `schedule_shape` already encodes existing weekly/session-size sub-order. Installed worker uses allow_unproven, and conditional proof/atomic at-most-once apply already exist in `optimization_operations.py`.
**Alternatives considered**: Coverage alone cannot establish preference proof; a separate acceptance route risks bypassing existing guards. Base I-003/I-004 path still needs core scoring without introducing the I-006 extension.

## Verification

**Decision**: Existing pytest/Vitest/type/build/lint plus independent small enumeration and real-browser/AT/timed-user acceptance.
**Rationale**: CI/locks/package.json establish existing tools. jsdom cannot evidence actual refresh latency, layout or AT announcements. Manual exceptions must have recorded outcomes.
**Alternatives considered**: Helper-against-helper tests cannot detect deficient candidate generation; labels alone cannot evidence SC-009/010.

## Direct consumers found during independent assessment

**Decision**: Integrate dated permission in the existing optimizer in US1, before its generation checkpoint; keep intensive scoring/completeness in US2. Explicitly extend direct constraint/Calendar/lifecycle serializers, current loaders, new captures and DraftSchedulePanel rendering; old captures default to weekly without rewrites. Filter existing exam proposals/eligibility to weekly records.
**Rationale**: Initial verifier found weekday-only solver filtering/sorting, direct profile producers/reconstructors outside shared schemas, and exam_scheduling.py proposals consumed by exam_optimization.py sorting. Mixed nullable weekdays can fail exam sorting; dated-only rows must not create weekly exam availability.
**Alternatives considered**: Deferring these integrations breaks the first increment or existing exam behavior; broadening exam policy contradicts approved exclusions. Preceding regression tests cover each path.

All technical unknowns are resolved; approved product scope and architecture remain intact.
