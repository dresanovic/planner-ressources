# Course unit information

Rename the course editor's former Gesamteinheiten label to Lehreinheiten.
These remain the units required by all existing planning and progress logic.
Retain the legacy `total_units` / `totalUnits` identifiers for compatibility.

Add independently editable Total Einheiten (`overall_units` / `overallUnits`)
for the full course scope, including online and self learning units. This is
informational and does not affect planning or introduce component calculations.

On database upgrade, copy every existing course's planning units into its new
total once, preserving IDs, relationships, revisions and schedules. Repeated
startup must preserve subsequently edited totals. New courses default the total
to their Lehreinheiten when omitted. Updates that omit the total preserve it.
Explicit totals must be positive integers; do not add comparisons that change
existing planning validation.

Verify migration preservation and repeatability, API persistence/defaults and
independence from planning progress, editor labels and submission, and the client
production build. Review only this change because unrelated work is in progress.
