"""Concrete teaching searches. Unknown or unfinished strategies never fall back."""
from typing import Protocol

from app.services.semester_optimization import SemesterOptimizationResult, optimize_semester


class TeachingStrategy(Protocol):
    def optimize(self, courses, fixed_sessions, unavailable_dates=(), **options) -> SemesterOptimizationResult: ...


class StandardStrategy:
    def optimize(self, courses, fixed_sessions, unavailable_dates=(), **options):
        return optimize_semester(courses, fixed_sessions, unavailable_dates, **options)


class CohortStrategy:
    def optimize(self, courses, fixed_sessions, unavailable_dates=(), **options):
        from app.services.heuristic_teaching import search_teaching
        return search_teaching(courses, fixed_sessions, unavailable_dates, algorithm='cohort', **options)


class StandardOptimizedStrategy:
    def optimize(self, courses, fixed_sessions, unavailable_dates=(), **options):
        from app.services.standard_optimized import optimize_semester
        return optimize_semester(courses, fixed_sessions, unavailable_dates, **options)


class LecturerStrategy:
    def optimize(self, courses, fixed_sessions, unavailable_dates=(), **options):
        from app.services.heuristic_teaching import search_teaching
        return search_teaching(courses, fixed_sessions, unavailable_dates, algorithm='lecturer', **options)


_STRATEGIES: dict[str, TeachingStrategy] = {
    'standard': StandardStrategy(), 'cohort': CohortStrategy(), 'lecturer': LecturerStrategy(),
    'standard_optimized': StandardOptimizedStrategy(),
}


def get_strategy(identifier: str) -> TeachingStrategy:
    try:
        return _STRATEGIES[identifier]
    except (KeyError, TypeError) as exc:
        raise ValueError('Unsupported teaching strategy') from exc
