OPTIMIZATION_STATUSES = {"complete", "improved_partial", "unchanged", "failed", "stale"}

BLOCKING_REASON_CODES = {
    "LECTURER_OCCUPIED", "ROOM_OCCUPIED", "COHORT_OCCUPIED", "LECTURER_UNAVAILABLE",
    "ROOM_UNAVAILABLE", "NO_ELIGIBLE_LECTURER", "NO_ELIGIBLE_ROOM",
    "INSUFFICIENT_ROOM_CAPACITY", "UNAVAILABLE_DATE", "NO_ALLOWED_DATE_OR_WINDOW",
    "COURSE_CONSTRAINT", "SELECTED_COURSE_COMPETITION", "INVALID_PLANNING_INPUT",
    "STALE_PLANNING_INPUT",
}

SUMMARY_FIELDS = {
    "total", "complete", "improvedPartial", "unchanged", "failed", "stale",
    "scheduledUnits", "remainingUnits", "elapsedMilliseconds", "optimalForPreparedSnapshot",
}

OPERATION_FAILURE = {
    "code": "OPTIMAL_RESULT_NOT_PROVEN",
    "message": "A fully optimal result was not proven.",
    "saved": False,
}
